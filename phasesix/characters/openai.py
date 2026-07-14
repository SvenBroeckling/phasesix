import json
import logging
from base64 import b64decode
from mimetypes import guess_type
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from openai import OpenAI

from armory.models import Item, RiotGear, Weapon
from body_modifications.models import BodyModification
from curators_desk.utils import get_homebrew_models
from horror.models import Quirk
from magic.models import BaseSpell
from potions.models import Recipe
from rules.models import Extension, Foe, Template
from worlds.models import Language, WorldLeadImage

logger = logging.getLogger(__name__)


class CharacterLeadImageService:
    """Create a transparent start-page image from a character portrait."""

    def __init__(self, character, world):
        self.character = character
        self.world = world

    def create(self):
        if not self.character.image:
            raise ValueError("This character does not have an image.")
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured.")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        try:
            self.character.image.open("rb")
            response = client.images.edit(
                model=settings.OPENAI_IMAGE_MODEL,
                image=(
                    Path(self.character.image.name).name,
                    self.character.image.read(),
                    guess_type(self.character.image.name)[0]
                    or "application/octet-stream",
                ),
                prompt=(
                    "Remove the entire background from this character portrait. "
                    "Keep the character unchanged and return only the character "
                    "on a transparent background."
                ),
                background="transparent",
                output_format="png",
            )
            image_data = response.data[0].b64_json
            if not image_data:
                raise ValueError("OpenAI did not return an image.")
        except Exception:
            logger.exception(
                "OpenAI background removal failed for character=%s",
                self.character.pk,
            )
            raise
        finally:
            self.character.image.close()

        filename = f"{Path(self.character.image.name).stem}-lead.png"
        lead_image = WorldLeadImage(world=self.world, character=self.character)
        lead_image.image.save(filename, ContentFile(b64decode(image_data)), save=False)
        lead_image.save()
        return lead_image


class CharacterRandomFillService:
    def __init__(self, character):
        self.character = character

    @staticmethod
    def _parse_json_response(text):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Invalid JSON response")
        return json.loads(text[start : end + 1])

    def _qs_for_extensions(self, model):
        if hasattr(model.objects, "for_extensions"):
            try:
                return model.objects.for_extensions(self.character.extensions)
            except Exception:
                return model.objects.all()
        try:
            return model.objects.filter(
                Q(extensions__id__in=self.character.extensions.all())
                | Q(extensions__id__in=Extension.objects.filter(is_mandatory=True))
            ).distinct()
        except Exception:
            return model.objects.all()

    def _has_extension(self, identifier):
        if self.character.extension_enabled.get(identifier):
            return True
        world = self.character.world
        if world and world.identifier == identifier:
            return True
        if world and world.fixed_extensions.filter(identifier=identifier).exists():
            return True
        return False

    def _openai_random_fill_options(self):
        options = {}
        for model in get_homebrew_models():
            qs = self._qs_for_extensions(model)

            if model is BaseSpell:
                if not self._has_extension("magic"):
                    qs = qs.none()
                else:
                    origins = self.character.unlocked_spell_origins
                    if origins.exists():
                        qs = qs.filter(origin__in=origins)
                    else:
                        qs = qs.none()

            if model is Quirk and not self._has_extension("horror"):
                qs = qs.none()

            options[model.__name__] = [
                {"pk": obj.pk, "name": getattr(obj, "name", str(obj))}
                for obj in qs.order_by("id")
            ]
        return options

    def _openai_random_fill_prompt(self):
        templates = [
            {
                "pk": ct.template.pk,
                "name": ct.template.name,
                "cost": ct.template.cost,
            }
            for ct in self.character.charactertemplate_set.select_related("template")
        ]
        extensions = [
            {"pk": ext.pk, "name": ext.name} for ext in self.character.extensions.all()
        ]
        world = self.character.world
        character_payload = {
            "name": self.character.name,
            "description": self.character.description or "",
            "world": {"pk": world.pk, "name": world.name} if world else None,
            "extensions": extensions,
            "current_templates": templates,
            "template_points_available": self.character.reputation_available,
            "spell_points_available": self.character.spell_points_available,
        }
        options = self._openai_random_fill_options()

        return (
            "You are selecting equipment, templates, and abilities for a tabletop RPG character. "
            "Return ONLY a JSON object. Use ONLY the provided pk values from the options list. "
            "Pick a reasonable amount that fits the character description, world, and templates.\n\n"
            "Constraints:\n"
            f"- template_points_available: {self.character.reputation_available}\n"
            f"- spell_points_available: {self.character.spell_points_available}\n"
            "- Use at most 3 templates, 3 weapons, 2 riot_gear, 10 items, 4 spells, 3 body_modifications.\n"
            "- Prefer variety and avoid duplicates unless it makes sense.\n\n"
            "Return JSON with these keys (empty arrays if none):\n"
            "{\n"
            '  "templates": [{"pk": 1}],\n'
            '  "weapons": [{"pk": 2}],\n'
            '  "riot_gear": [{"pk": 3}],\n'
            '  "items": [{"pk": 4, "quantity": 2}],\n'
            '  "spells": [{"pk": 5}],\n'
            '  "body_modifications": [{"pk": 6}],\n'
            '  "quirks": [{"pk": 7}],\n'
            '  "languages": [{"pk": 8}],\n'
            '  "foes": [{"pk": 9}],\n'
            '  "recipes": [{"pk": 10}]\n'
            "}\n\n"
            "Character:\n"
            f"{json.dumps(character_payload, ensure_ascii=False)}\n\n"
            "Options by model (pk + name only):\n"
            f"{json.dumps(options, ensure_ascii=False)}"
        )

    def _apply_openai_random_fill(self, data):
        def normalize_pk_list(value):
            pks = []
            if not isinstance(value, list):
                return pks
            for entry in value:
                if isinstance(entry, dict):
                    pk = entry.get("pk") or entry.get("id")
                else:
                    pk = entry
                try:
                    pk = int(pk)
                except (TypeError, ValueError):
                    continue
                if pk > 0:
                    pks.append(pk)
            return pks

        def normalize_item_list(value):
            items = []
            if not isinstance(value, list):
                return items
            for entry in value:
                if isinstance(entry, dict):
                    pk = entry.get("pk") or entry.get("id")
                    quantity = entry.get("quantity", 1)
                else:
                    pk = entry
                    quantity = 1
                try:
                    pk = int(pk)
                    quantity = int(quantity)
                except (TypeError, ValueError):
                    continue
                if pk > 0:
                    items.append((pk, max(1, quantity)))
            return items

        added = {
            "templates": 0,
            "weapons": 0,
            "riot_gear": 0,
            "items": 0,
            "spells": 0,
            "body_modifications": 0,
            "quirks": 0,
            "languages": 0,
            "foes": 0,
            "recipes": 0,
        }

        with transaction.atomic():
            template_points_left = self.character.reputation_available
            template_pks = normalize_pk_list(data.get("templates", []))
            if template_pks:
                for template in self._qs_for_extensions(Template).filter(
                    pk__in=template_pks
                ):
                    if (
                        template.cost <= template_points_left
                        and not self.character.charactertemplate_set.filter(
                            template=template
                        ).exists()
                    ):
                        self.character.add_template(template)
                        template_points_left -= template.cost
                        added["templates"] += 1

            spell_points_left = self.character.spell_points_available
            spell_pks = normalize_pk_list(
                data.get("spells", []) or data.get("base_spells", [])
            )
            if spell_pks and self._has_extension("magic"):
                allowed_origins = list(self.character.unlocked_spell_origins)
                for spell in BaseSpell.objects.filter(pk__in=spell_pks):
                    if spell.origin and spell.origin not in allowed_origins:
                        continue
                    if (
                        spell.spell_point_cost <= spell_points_left
                        and not self.character.characterspell_set.filter(
                            spell=spell
                        ).exists()
                    ):
                        self.character.characterspell_set.create(spell=spell)
                        spell_points_left -= spell.spell_point_cost
                        added["spells"] += 1

            weapon_pks = normalize_pk_list(data.get("weapons", []))
            if weapon_pks:
                for weapon in self._qs_for_extensions(Weapon).filter(pk__in=weapon_pks):
                    if not self.character.characterweapon_set.filter(
                        weapon=weapon
                    ).exists():
                        self.character.characterweapon_set.create(weapon=weapon)
                        added["weapons"] += 1

            riot_gear_pks = normalize_pk_list(data.get("riot_gear", []))
            if riot_gear_pks:
                for gear in self._qs_for_extensions(RiotGear).filter(
                    pk__in=riot_gear_pks
                ):
                    if not self.character.characterriotgear_set.filter(
                        riot_gear=gear
                    ).exists():
                        self.character.characterriotgear_set.create(riot_gear=gear)
                        added["riot_gear"] += 1

            item_entries = normalize_item_list(data.get("items", []))
            if item_entries:
                items_qs = self._qs_for_extensions(Item).filter(
                    pk__in=[pk for pk, _ in item_entries]
                )
                item_map = {item.pk: item for item in items_qs}
                for pk, quantity in item_entries:
                    item = item_map.get(pk)
                    if not item:
                        continue
                    if (
                        self.character.characteritem_set.filter(item=item).exists()
                        and not item.is_container
                    ):
                        ci = self.character.characteritem_set.filter(item=item).latest(
                            "id"
                        )
                        ci.quantity += quantity
                        ci.save(update_fields=["quantity"])
                    else:
                        self.character.characteritem_set.create(
                            item=item, quantity=quantity
                        )
                    added["items"] += quantity

            body_modification_pks = normalize_pk_list(
                data.get("body_modifications", [])
            )
            if body_modification_pks and self._has_extension("bodymod"):
                for modification in self._qs_for_extensions(BodyModification).filter(
                    pk__in=body_modification_pks
                ):
                    if self.character.characterbodymodification_set.filter(
                        body_modification=modification
                    ).exists():
                        continue
                    socket_location = (
                        modification.bodymodificationsocketlocation_set.select_related(
                            "socket_location"
                        )
                        .order_by("id")
                        .first()
                    )
                    if not socket_location:
                        continue
                    self.character.characterbodymodification_set.create(
                        body_modification=modification,
                        socket_location=socket_location.socket_location,
                        socket_amount=socket_location.socket_amount,
                    )
                    added["body_modifications"] += 1

            quirk_pks = normalize_pk_list(data.get("quirks", []))
            if quirk_pks and self._has_extension("horror"):
                for quirk in self._qs_for_extensions(Quirk).filter(pk__in=quirk_pks):
                    if not self.character.characterquirk_set.filter(
                        quirk=quirk
                    ).exists():
                        self.character.add_quirk(quirk)
                        added["quirks"] += 1

            language_pks = normalize_pk_list(data.get("languages", []))
            if language_pks:
                for language in self._qs_for_extensions(Language).filter(
                    pk__in=language_pks
                ):
                    if not self.character.characterlanguage_set.filter(
                        language=language
                    ).exists():
                        self.character.characterlanguage_set.create(language=language)
                        added["languages"] += 1

            foe_pks = normalize_pk_list(data.get("foes", []))
            if foe_pks:
                for foe in self._qs_for_extensions(Foe).filter(pk__in=foe_pks):
                    if not self.character.characterfoe_set.filter(foe=foe).exists():
                        self.character.characterfoe_set.create(
                            foe=foe, health=foe.health, max_health=foe.health
                        )
                        added["foes"] += 1

            recipe_pks = normalize_pk_list(data.get("recipes", []))
            if recipe_pks:
                for recipe in self._qs_for_extensions(Recipe).filter(pk__in=recipe_pks):
                    if not self.character.characterrecipe_set.filter(
                        recipe=recipe
                    ).exists():
                        self.character.characterrecipe_set.create(recipe=recipe)
                        added["recipes"] += 1

        return added

    def fill_randomly_from_openai(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured.")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = self._openai_random_fill_prompt()
        try:
            response = client.responses.create(
                model=settings.OPENAI_TRANSLATION_MODEL,
                input=prompt,
            )
            output_text = getattr(response, "output_text", None)
            if not output_text and getattr(response, "output", None):
                output_text = response.output[0].content[0].text
            if not output_text:
                raise ValueError("OpenAI did not return any content.")
        except Exception:
            logger.exception(
                "OpenAI random fill request failed for character=%s",
                self.character.pk,
            )
            raise

        data = self._parse_json_response(output_text)
        return self._apply_openai_random_fill(data)
