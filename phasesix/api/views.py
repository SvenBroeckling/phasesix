from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import activate
from django.views import View

from armory.models import Weapon, WeaponModification, Item, RiotGear
from body_modifications.models import BodyModification
from horror.models import Quirk
from magic.models import SpellTemplate, BaseSpell
from portal.models import Profile
from rules.models import Template, Foe


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
            "templates": Template,
            "weapons": Weapon,
            "weapon_modifications": WeaponModification,
            "riot_gear": RiotGear,
            "items": Item,
            "spells": BaseSpell,
            "spell_templates": SpellTemplate,
            "quirks": Quirk,
            "body_modifications": BodyModification,
            "foes": Foe,
        }
        qs = model_map[kwargs["model"]].objects.all()
        return JsonResponse([t.as_json() for t in qs], safe=False)
