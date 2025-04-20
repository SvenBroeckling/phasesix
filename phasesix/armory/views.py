from django.views.generic import DetailView, TemplateView
from django.utils.translation import gettext_lazy as _

from armory.models import Item
from characters.character_objects import WeaponObject, RiotGearObject, ItemObject


class WeaponListView(TemplateView):
    template_name = "characters/character_object_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "weapon_list"
        context["title"] = _("Weapons")
        context["sub_title"] = _("Weapons and their properties")
        context["character_object"] = WeaponObject(self.request, character=None)
        return context


class RiotGearListView(TemplateView):
    template_name = "characters/character_object_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "riot_gear_list"
        context["title"] = _("Armor")
        context["sub_title"] = _("Protective gear and accessories")
        context["character_object"] = RiotGearObject(self.request, character=None)
        return context


class ItemListView(TemplateView):
    template_name = "characters/character_object_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "item_list"
        context["title"] = _("Items")
        context["sub_title"] = _("All sorts of useful things")
        context["character_object"] = ItemObject(self.request, character=None)
        return context


class ItemDetailView(DetailView):
    model = Item


class MaterialOverviewView(TemplateView):
    template_name = "armory/material_overview.html"
