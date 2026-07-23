import json
import os
import zipfile
from io import BytesIO

import markdown
from django.utils.text import slugify

MODULE_FORMAT_VERSION = 5


def module_id(campaign):
    return f"phasesix-campaign-{campaign.pk}"


def document_id(prefix, pk):
    return f"{prefix}{pk:013d}"


class FoundryModule:
    """Build a self-contained V14 module without creating temporary files."""

    def __init__(self, campaign, manifest_url, download_url):
        self.campaign = campaign
        self.plot = getattr(campaign, "plot", None)
        self.id = module_id(campaign)
        self.manifest_url = manifest_url
        self.download_url = download_url
        self.assets = []

    @property
    def version(self):
        export_version = self.plot.export_version if self.plot else 0
        return f"{MODULE_FORMAT_VERSION}.0.{export_version}"

    @property
    def title(self):
        if self.plot and self.plot.name != self.campaign.name:
            return f"{self.plot.name} ({self.campaign.name})"
        return self.plot.name if self.plot else self.campaign.name

    @property
    def filename(self):
        return f"{slugify(self.title) or self.id}-{self.version}.zip"

    def asset_path(self, field_file, kind, pk):
        if not field_file:
            return None
        suffix = os.path.splitext(field_file.name)[1].lower() or ".bin"
        path = f"assets/{kind}-{pk}{suffix}"
        if not any(asset[0] == path for asset in self.assets):
            self.assets.append((path, field_file))
        return f"modules/{self.id}/{path}"

    def actor(self, prefix, pk, name, category, description, image, details=None):
        return {
            "_id": document_id(prefix, pk),
            "name": name,
            "type": f"{self.id}.phasesix",
            "img": image or "icons/svg/mystery-man.svg",
            "system": {
                "category": category,
                "description": description or "",
                "details": details or {},
            },
            "flags": {self.id: {"source": f"{category}:{pk}"}},
        }

    def documents(self):
        payload = {"actors": [], "items": [], "journals": [], "scenes": []}
        if not self.plot:
            return payload

        elements = list(
            self.plot.plotelement_set.prefetch_related(
                "npc",
                "essential_npc",
                "foes__resistances",
                "foes__weaknesses",
                "foes__foeaction_set",
                "handouts",
                "locations",
            ).all()
        )
        elements_by_parent = {}
        for element in elements:
            elements_by_parent.setdefault(element.parent_id, []).append(element)

        ordered_elements = []
        visited_element_ids = set()

        def walk(parent_id):
            for element in elements_by_parent.get(parent_id, []):
                if element.pk in visited_element_ids:
                    continue
                visited_element_ids.add(element.pk)
                ordered_elements.append(element)
                walk(element.pk)

        walk(None)
        # Include malformed or detached branches instead of silently omitting content.
        ordered_elements.extend(
            element for element in elements if element not in ordered_elements
        )

        seen = {"actors": set(), "items": set(), "scenes": set()}
        for element in ordered_elements:
            if element.player_summary:
                payload["journals"].append(
                    {
                        "_id": document_id("P6J", element.pk),
                        "name": element.name,
                        "pages": [
                            {
                                "_id": document_id("P6P", element.pk),
                                "name": element.name,
                                "type": "text",
                                "text": {
                                    "content": markdown.markdown(
                                        element.player_summary
                                    ),
                                    "format": 1,
                                },
                            }
                        ],
                        "flags": {self.id: {"source": f"plot-element:{element.pk}"}},
                    }
                )
            for npc in element.npc.all():
                if npc.pk not in seen["actors"]:
                    seen["actors"].add(npc.pk)
                    payload["actors"].append(
                        self.actor(
                            "P6N",
                            npc.pk,
                            npc.name,
                            "npc",
                            markdown.markdown(npc.description or ""),
                            self.asset_path(npc.image, "npc", npc.pk),
                            {"health": npc.health, "stress": npc.stress},
                        )
                    )
            for npc in element.essential_npc.all():
                source = f"essential-{npc.pk}"
                if source not in seen["actors"]:
                    seen["actors"].add(source)
                    payload["actors"].append(
                        self.actor(
                            "P6C",
                            npc.pk,
                            npc.name,
                            "character",
                            markdown.markdown(
                                "\n\n".join(
                                    part
                                    for part in (
                                        npc.concept,
                                        npc.oath_or_debt,
                                        npc.notes,
                                    )
                                    if part
                                )
                            ),
                            self.asset_path(npc.image, "character", npc.pk),
                            {"mind": npc.mind, "will": npc.will, "body": npc.body},
                        )
                    )
            for foe in element.foes.all():
                source = f"foe-{foe.pk}"
                if source not in seen["actors"]:
                    seen["actors"].add(source)
                    payload["actors"].append(
                        self.actor(
                            "P6F",
                            foe.pk,
                            foe.name,
                            "foe",
                            markdown.markdown(foe.short_description or ""),
                            self.asset_path(foe.image, "foe", foe.pk),
                            foe.as_dict(),
                        )
                    )
            for handout in element.handouts.all():
                if handout.pk in seen["items"]:
                    continue
                seen["items"].add(handout.pk)
                payload["items"].append(
                    {
                        "_id": document_id("P6H", handout.pk),
                        "name": handout.name,
                        "type": f"{self.id}.handout",
                        "img": self.asset_path(handout.image, "handout", handout.pk)
                        or "icons/svg/book.svg",
                        "system": {
                            "description": markdown.markdown(handout.description or "")
                        },
                        "flags": {self.id: {"source": f"handout:{handout.pk}"}},
                    }
                )
            for location in element.locations.all():
                if location.pk in seen["scenes"]:
                    continue
                seen["scenes"].add(location.pk)
                background = self.asset_path(location.image, "location", location.pk)
                dimensions = {}
                if location.image:
                    dimensions = {
                        "width": location.image.width,
                        "height": location.image.height,
                    }
                payload["scenes"].append(
                    {
                        "_id": document_id("P6S", location.pk),
                        "name": location.name,
                        **dimensions,
                        "levels": [
                            {
                                "_id": document_id("P6L", location.pk),
                                "name": "Ground",
                                "elevation": {"bottom": 0, "top": 10},
                                "background": {"src": background or ""},
                            }
                        ],
                        "flags": {self.id: {"source": f"location:{location.pk}"}},
                    }
                )
        return payload

    def manifest(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": "PhaseSix campaign material for Foundry VTT.",
            "version": self.version,
            "authors": [{"name": "PhaseSix"}],
            "compatibility": {"minimum": "14", "verified": "14"},
            "manifest": self.manifest_url,
            "download": self.download_url,
            "esmodules": ["scripts/main.mjs"],
            "styles": ["styles/actor-sheet.css"],
            "languages": [{"lang": "en", "name": "English", "path": "lang/en.json"}],
            "documentTypes": {
                "Actor": {"phasesix": {"htmlFields": ["description"]}},
                "Item": {"handout": {"htmlFields": ["description"]}},
            },
        }

    def archive(self):
        data = self.documents()
        output = BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            root = ""
            archive.writestr(
                root + "module.json", json.dumps(self.manifest(), indent=2)
            )
            archive.writestr(root + "data/export.json", json.dumps(data))
            archive.writestr(root + "scripts/main.mjs", self.script())
            archive.writestr(root + "templates/actor-sheet.hbs", self.template())
            archive.writestr(
                root + "templates/handout-sheet.hbs", self.handout_template()
            )
            archive.writestr(root + "styles/actor-sheet.css", self.styles())
            archive.writestr(root + "lang/en.json", json.dumps(self.translations()))
            for path, field_file in self.assets:
                field_file.open("rb")
                try:
                    archive.writestr(root + path, field_file.read())
                finally:
                    field_file.close()
        output.seek(0)
        return output

    def translations(self):
        return {"TYPES": {"Actor": {"phasesix": "PhaseSix actor"}}}

    def template(self):
        return """<form class=\"phasesix-actor-sheet\" autocomplete=\"off\">
  <header class=\"phasesix-actor-sheet__header\">
    <img class=\"phasesix-actor-sheet__portrait\" src=\"{{actor.img}}\" data-edit=\"img\">
    <div>
      <input class=\"phasesix-actor-sheet__name\" name=\"name\" value=\"{{actor.name}}\">
      <span class=\"phasesix-actor-sheet__category\">{{category}}</span>
    </div>
  </header>
  <section class=\"phasesix-actor-sheet__section\">
    <h2>Overview</h2>
    <div class=\"phasesix-actor-sheet__description\">{{{description}}}</div>
  </section>
  {{#if details.length}}
    <section class=\"phasesix-actor-sheet__section\">
      <h2>Details</h2>
      <dl class=\"phasesix-actor-sheet__details\">
        {{#each details}}<div><dt>{{label}}</dt><dd>{{value}}</dd></div>{{/each}}
      </dl>
    </section>
  {{/if}}
</form>"""

    def styles(self):
        return """.phasesix-actor-sheet { color: var(--color-text-primary); padding: 1rem; }
.phasesix-actor-sheet__header { align-items: center; border-bottom: 1px solid var(--color-border-light-primary); display: flex; gap: 1rem; margin-bottom: 1rem; padding-bottom: 1rem; }
.phasesix-actor-sheet__portrait { border: 1px solid var(--color-border-highlight); border-radius: 4px; height: 96px; object-fit: cover; width: 96px; }
.phasesix-actor-sheet__name { background: none; border: 0; color: var(--color-text-primary); font-family: var(--font-primary); font-size: 1.5rem; font-weight: 700; padding: 0; width: 100%; }
.phasesix-actor-sheet__category { color: var(--color-text-secondary); display: block; font-size: .75rem; font-weight: 700; letter-spacing: .12em; margin-top: .35rem; text-transform: uppercase; }
.phasesix-actor-sheet__section { margin-top: 1.25rem; }
.phasesix-actor-sheet__section h2 { border-bottom: 1px solid var(--color-border-light-primary); font-size: .9rem; letter-spacing: .08em; margin: 0 0 .6rem; padding-bottom: .4rem; text-transform: uppercase; }
.phasesix-actor-sheet__description { line-height: 1.5; max-height: 18rem; overflow-y: auto; padding-right: .5rem; }
.phasesix-actor-sheet__description p:first-child { margin-top: 0; }
.phasesix-actor-sheet__details { display: grid; gap: .5rem; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); margin: 0; }
.phasesix-actor-sheet__details > div { background: color-mix(in srgb, var(--color-cool-3) 45%, transparent); border-left: 2px solid var(--color-border-highlight); min-height: 3.6rem; padding: .45rem .6rem; }
.phasesix-actor-sheet__details dt { color: var(--color-text-secondary); font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; }
.phasesix-actor-sheet__details dd { font-size: .95rem; font-weight: 600; margin: .25rem 0 0; white-space: pre-line; }"""

    def handout_template(self):
        return """<form class=\"phasesix-actor-sheet\" autocomplete=\"off\">
  <header class=\"phasesix-actor-sheet__header\">
    <img class=\"phasesix-actor-sheet__portrait\" src=\"{{item.img}}\" data-edit=\"img\">
    <div><input class=\"phasesix-actor-sheet__name\" name=\"name\" value=\"{{item.name}}\"><span class=\"phasesix-actor-sheet__category\">Handout</span></div>
  </header>
  <section class=\"phasesix-actor-sheet__section\"><div class=\"phasesix-actor-sheet__description\">{{{description}}}</div></section>
</form>"""

    def script(self):
        return f"""const MODULE_ID = "{self.id}";
const ACTOR_TYPE = `${{MODULE_ID}}.phasesix`;
const {{ TypeDataModel }} = foundry.abstract;
const fields = foundry.data.fields;
const {{ ActorSheetV2 }} = foundry.applications.sheets;
const {{ ItemSheetV2 }} = foundry.applications.sheets;
const {{ HandlebarsApplicationMixin }} = foundry.applications.api;

class PhaseSixActorData extends TypeDataModel {{
  static defineSchema() {{ return {{
    category: new fields.StringField({{initial: "npc"}}),
    description: new fields.HTMLField({{required: false, blank: true}}),
    details: new fields.ObjectField({{initial: {{}}}})
  }}; }}
}}
class PhaseSixActorSheet extends HandlebarsApplicationMixin(ActorSheetV2) {{
  static DEFAULT_OPTIONS = {{ form: {{closeOnSubmit: false, submitOnChange: true}}, position: {{width: 520}} }};
  static PARTS = {{ form: {{template: `modules/${{MODULE_ID}}/templates/actor-sheet.hbs`}} }};
  async _prepareContext(options) {{
    const context = await super._prepareContext(options);
    context.actor = this.actor;
    context.category = this.actor.system.category.charAt(0).toUpperCase() + this.actor.system.category.slice(1);
    context.description = await TextEditor.enrichHTML(this.actor.system.description || "", {{async: true, relativeTo: this.actor, secrets: this.actor.isOwner}});
    context.details = Object.entries(this.actor.system.details || {{}}).map(([key, value]) => ({{
      label: key.replace(/_/g, " "),
      value: Array.isArray(value) ? value.map(entry => typeof entry === "object" ? Object.values(entry).join(": ") : entry).join(" | ") : typeof value === "object" ? JSON.stringify(value) : String(value ?? "")
    }}));
    return context;
  }}
}}
class PhaseSixHandoutData extends TypeDataModel {{
  static defineSchema() {{ return {{ description: new fields.HTMLField({{required: false, blank: true}}) }}; }}
}}
class PhaseSixHandoutSheet extends HandlebarsApplicationMixin(ItemSheetV2) {{
  static DEFAULT_OPTIONS = {{ form: {{closeOnSubmit: false, submitOnChange: true}}, position: {{width: 520}} }};
  static PARTS = {{ form: {{template: `modules/${{MODULE_ID}}/templates/handout-sheet.hbs`}} }};
  async _prepareContext(options) {{
    const context = await super._prepareContext(options);
    context.item = this.item;
    context.description = await TextEditor.enrichHTML(this.item.system.description || "", {{async: true, relativeTo: this.item, secrets: this.item.isOwner}});
    return context;
  }}
}}
Hooks.once("init", () => {{
  CONFIG.Actor.dataModels[ACTOR_TYPE] = PhaseSixActorData;
  CONFIG.Item.dataModels[`${{MODULE_ID}}.handout`] = PhaseSixHandoutData;
  DocumentSheetConfig.registerSheet(Actor, MODULE_ID, PhaseSixActorSheet, {{types: [ACTOR_TYPE], makeDefault: true}});
  DocumentSheetConfig.registerSheet(Item, MODULE_ID, PhaseSixHandoutSheet, {{types: [`${{MODULE_ID}}.handout`], makeDefault: true}});
}});
async function importDocuments(pack, documents) {{
  for (const source of documents) {{
    const existing = await pack.getDocument(source._id);
    if (existing) await existing.update(source); else await pack.documentClass.create(source, {{pack: pack.collection}});
  }}
}}
async function importScenes(pack, scenes) {{
  for (const source of scenes) {{
    const {{levels, ...sceneSource}} = source;
    let scene = await pack.getDocument(source._id);
    if (scene) await scene.update(sceneSource); else scene = await pack.documentClass.create(sceneSource, {{pack: pack.collection}});
    const level = levels[0];
    if (!level) continue;
    const existingLevel = scene.firstLevel;
    if (existingLevel) await scene.updateEmbeddedDocuments("Level", [{{...level, _id: existingLevel.id}}]);
    else await scene.createEmbeddedDocuments("Level", [level], {{keepId: true}});
  }}
}}
Hooks.once("ready", async () => {{
  if (!game.user.isGM) return;
  const exported = await (await fetch(`modules/${{MODULE_ID}}/data/export.json`)).json();
  const revision = game.settings.get(MODULE_ID, "importedRevision");
  if (revision === game.modules.get(MODULE_ID).version) return;
  for (const [kind, type, label] of [["actors", "Actor", "Actors"], ["items", "Item", "Handouts"], ["journals", "JournalEntry", "Plot journals"], ["scenes", "Scene", "Locations"]]) {{
    const name = `${{MODULE_ID}}-${{kind}}`;
    let pack = game.packs.get(`world.${{name}}`);
    if (!pack) {{ await CompendiumCollection.createCompendium({{name, label, type, package: "world"}}); pack = game.packs.get(`world.${{name}}`); }}
    if (kind === "scenes") await importScenes(pack, exported[kind]);
    else await importDocuments(pack, exported[kind]);
  }}
  await game.settings.set(MODULE_ID, "importedRevision", game.modules.get(MODULE_ID).version);
  ui.notifications.info(`${{game.modules.get(MODULE_ID).title}} imported.`);
}});
Hooks.once("init", () => game.settings.register(MODULE_ID, "importedRevision", {{scope: "world", config: false, type: String, default: ""}}));
"""
