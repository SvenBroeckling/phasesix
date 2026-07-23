import json
import os
import zipfile
from io import BytesIO

import markdown


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
        return f"1.0.{self.plot.export_version}" if self.plot else "1.0.0"

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
        payload = {"actors": [], "journals": [], "scenes": []}
        if not self.plot:
            return payload

        elements = self.plot.plotelement_set.prefetch_related(
            "npc",
            "essential_npc",
            "foes__resistances",
            "foes__weaknesses",
            "foes__foeaction_set",
            "locations",
        ).all()
        seen = {"actors": set(), "scenes": set()}
        for element in elements:
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
                            npc.description,
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
                            "\n\n".join(
                                part
                                for part in (npc.concept, npc.oath_or_debt, npc.notes)
                                if part
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
                            foe.short_description,
                            self.asset_path(foe.image, "foe", foe.pk),
                            foe.as_dict(),
                        )
                    )
            for location in element.locations.all():
                if location.pk in seen["scenes"]:
                    continue
                seen["scenes"].add(location.pk)
                background = self.asset_path(location.image, "location", location.pk)
                payload["scenes"].append(
                    {
                        "_id": document_id("P6S", location.pk),
                        "name": location.name,
                        "background": {"src": background or ""},
                        "flags": {self.id: {"source": f"location:{location.pk}"}},
                    }
                )
        return payload

    def manifest(self):
        return {
            "id": self.id,
            "title": f"{self.campaign.name} - PhaseSix",
            "description": "PhaseSix campaign material for Foundry VTT.",
            "version": self.version,
            "authors": [{"name": "PhaseSix"}],
            "compatibility": {"minimum": "14", "verified": "14"},
            "manifest": self.manifest_url,
            "download": self.download_url,
            "esmodules": ["scripts/main.mjs"],
            "languages": [{"lang": "en", "name": "English", "path": "lang/en.json"}],
            "documentTypes": {"Actor": {"phasesix": {"htmlFields": ["description"]}}},
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
  <header><img src=\"{{actor.img}}\" data-edit=\"img\"><input name=\"name\" value=\"{{actor.name}}\"></header>
  <p><strong>{{actor.system.category}}</strong></p>
  <label>Description<textarea name=\"system.description\">{{actor.system.description}}</textarea></label>
  <label>Details<textarea disabled>{{details}}</textarea></label>
</form>"""

    def script(self):
        return f"""const MODULE_ID = "{self.id}";
const ACTOR_TYPE = `${{MODULE_ID}}.phasesix`;
const {{ TypeDataModel }} = foundry.abstract;
const fields = foundry.data.fields;
const {{ ActorSheetV2 }} = foundry.applications.sheets;
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
  async _prepareContext(options) {{ const context = await super._prepareContext(options); context.actor = this.actor; context.details = JSON.stringify(this.actor.system.details, null, 2); return context; }}
}}
Hooks.once("init", () => {{
  CONFIG.Actor.dataModels[ACTOR_TYPE] = PhaseSixActorData;
  DocumentSheetConfig.registerSheet(Actor, MODULE_ID, PhaseSixActorSheet, {{types: [ACTOR_TYPE], makeDefault: true}});
}});
async function importDocuments(pack, documents) {{
  for (const source of documents) {{
    const existing = await pack.getDocument(source._id);
    if (existing) await existing.update(source); else await pack.documentClass.create(source, {{pack: pack.collection}});
  }}
}}
Hooks.once("ready", async () => {{
  if (!game.user.isGM) return;
  const exported = await (await fetch(`modules/${{MODULE_ID}}/data/export.json`)).json();
  const revision = game.settings.get(MODULE_ID, "importedRevision");
  if (revision === game.modules.get(MODULE_ID).version) return;
  for (const [kind, type, label] of [["actors", "Actor", "Actors"], ["journals", "JournalEntry", "Plot journals"], ["scenes", "Scene", "Locations"]]) {{
    const name = `${{MODULE_ID}}-${{kind}}`;
    let pack = game.packs.get(`world.${{name}}`);
    if (!pack) {{ await CompendiumCollection.createCompendium({{name, label, type, package: "world"}}); pack = game.packs.get(`world.${{name}}`); }}
    await importDocuments(pack, exported[kind]);
  }}
  await game.settings.set(MODULE_ID, "importedRevision", game.modules.get(MODULE_ID).version);
  ui.notifications.info(`${{game.modules.get(MODULE_ID).title}} imported.`);
}});
Hooks.once("init", () => game.settings.register(MODULE_ID, "importedRevision", {{scope: "world", config: false, type: String, default: ""}}));
"""
