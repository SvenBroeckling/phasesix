from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import activate
from django.views import View

from armory.models import (
    WeaponType,
    RiotGearType,
    ItemType,
    WeaponModificationType,
)
from body_modifications.models import BodyModificationType
from horror.models import QuirkCategory
from magic.models import SpellOrigin, SpellTemplateCategory
from portal.models import Profile
from rules.models import TemplateCategory, FoeType, Extension


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
            "weapon_modifications": WeaponModificationType,
            "riot_gear": RiotGearType,
            "items": ItemType,
            "spells": SpellOrigin,
            "spell_templates": SpellTemplateCategory,
            "quirks": QuirkCategory,
            "body_modifications": BodyModificationType,
            "foes": FoeType,
        }
        qs = model_map[kwargs["model"]].objects.all()

        world_name = request.GET.get("world", None)
        extensions = Extension.objects.active()
        if world_name is not None and world_name in ["nexus", "tirakan"]:
            extensions = Extension.objects.for_world_identifier(world_name)
        else:
            extensions = Extension.objects.exclude(type="w")
        return JsonResponse(
            [t.as_dict(extension_qs=extensions) for t in qs], safe=False
        )
