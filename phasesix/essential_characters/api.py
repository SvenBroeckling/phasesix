import mimetypes
import os

from django.http import HttpResponse, JsonResponse
from django.views import View

from .models import EssentialCharacter
from .rules import ATTRIBUTES

PUBLIC_API_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, PATCH, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _portrait_fields(character):
    if not character.image:
        return {
            "portraitOriginalName": None,
            "portraitMimeType": None,
            "portraitSize": None,
            "portraitUpdatedAt": None,
        }

    try:
        portrait_size = character.image.size
    except OSError:
        portrait_size = None

    return {
        "portraitOriginalName": os.path.basename(character.image.name),
        "portraitMimeType": mimetypes.guess_type(character.image.name)[0],
        "portraitSize": portrait_size,
        "portraitUpdatedAt": character.modified_at,
    }


def essential_character_to_public_api(character):
    weapons = list(character.weapons.all())
    armor = character.armor.first()
    campaign = character.pc_or_npc_campaign

    return {
        "hash": character.slug,
        "name": character.name,
        "birthDate": character.birth_date or None,
        "century": character.century,
        "campaign": campaign.name if campaign else None,
        "playerName": character.created_by.username,
        "concept": character.concept,
        "ancestry": str(character.ancestry),
        "ancestryCustom": False,
        "path": str(character.path),
        "pathCustom": False,
        "bond": str(character.bond),
        "bondCustom": False,
        "oathOrDebt": character.oath_or_debt or None,
        "mark": "keins",
        "attributes": {
            attribute: getattr(character, attribute) for attribute in ATTRIBUTES
        },
        "skills": [
            {"name": skill.name, "rank": skill.rank}
            for skill in character.essentialcharacterskill_set.all()
        ],
        "equipment": {
            "primaryWeapon": str(weapons[0]) if weapons else "",
            "secondaryWeapon": str(weapons[1]) if len(weapons) > 1 else "",
            "armor": str(armor) if armor else "",
            "items": [str(item) for item in character.items.all()],
            "customWeapons": {},
            "customArmors": {},
        },
        "supernatural": {
            "focus": character.focus,
            "regenerationRitual": character.regeneration_ritual,
            "aspects": [str(aspect) for aspect in character.magic_aspects.all()],
            "spells": [str(spell) for spell in character.spells.all()],
        },
        "conditions": {
            "wounds": character.wounds,
            "burden": character.burden,
            "omen": character.omen,
            "arkana": character.arkana,
            "favor": character.favor,
            "corruption": character.corruption,
        },
        "notes": character.notes or None,
        **_portrait_fields(character),
        "woundThreshold": character.wound_threshold,
        "burdenThreshold": character.burden_threshold,
        "initiative": character.initiative,
        "faithLevel": character.faith_level,
        "magicLevel": character.magic_level,
        "omenMax": character.omen_max,
        "invocationValue": character.invocation_value,
        "favorLimit": character.favor_limit,
        "arkanaMax": character.arkana_max,
        "favorMax": character.favor_max,
        "createdAt": character.created_at,
        "updatedAt": character.modified_at,
    }


class PublicEssentialCharacterApiView(View):
    def get(self, request, *args, **kwargs):
        character = (
            EssentialCharacter.objects.select_related(
                "campaign",
                "npc_campaign",
                "created_by",
                "ancestry",
                "path",
                "bond",
            )
            .prefetch_related(
                "essentialcharacterskill_set",
                "weapons",
                "armor",
                "items",
                "magic_aspects",
                "spells",
            )
            .filter(slug=kwargs["character_hash"])
            .first()
        )
        if character is None:
            return JsonResponse(
                {"error": "Nicht gefunden"}, status=404, headers=PUBLIC_API_HEADERS
            )
        return JsonResponse(
            essential_character_to_public_api(character), headers=PUBLIC_API_HEADERS
        )

    def options(self, request, *args, **kwargs):
        return HttpResponse(status=204, headers=PUBLIC_API_HEADERS)
