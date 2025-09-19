from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import activate
from django.views import View

from armory.models import (
    Weapon,
    WeaponModification,
    Item,
    RiotGear,
    WeaponType,
    RiotGearType,
    ItemType,
)
from body_modifications.models import BodyModification, BodyModificationType
from horror.models import Quirk, QuirkCategory
from magic.models import SpellTemplate, BaseSpell, SpellOrigin, SpellTemplateCategory
from portal.models import Profile
from rules.models import Template, Foe, TemplateCategory, FoeType


class ApiKeyView(View):
    def dispatch(self, request, *args, **kwargs):
        api_key = request.headers.get("Authorization")
        if not Profile.objects.filter(
            Q(api_key=api_key) & Q(api_key__isnull=False)
        ).exists():
            raise PermissionDenied()
        activate(request.headers.get("Accept-Language") or "en")
        return super().dispatch(request, *args, **kwargs)


class DumpApiView(ApiKeyView):
    def get(self, request, *args, **kwargs):
        model_map = {
            "templates": TemplateCategory,
            "weapons": WeaponType,
            "weapon_modifications": WeaponModification,
            "riot_gear": RiotGearType,
            "items": ItemType,
            "spells": SpellOrigin,
            "spell_templates": SpellTemplateCategory,
            "quirks": QuirkCategory,
            "body_modifications": BodyModificationType,
            "foes": FoeType,
        }
        qs = model_map[kwargs["model"]].objects.all()
        return JsonResponse([t.as_dict() for t in qs], safe=False)
