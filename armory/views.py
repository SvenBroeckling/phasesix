from django.views.generic import ListView, DetailView, TemplateView

from armory.models import Item, WeaponType, RiotGearType, ItemType


class WeaponListView(ListView):
    model = WeaponType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "weapon_list"
        return context


class RiotGearListView(ListView):
    model = RiotGearType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "riot_gear_list"
        return context


class ItemListView(ListView):
    model = ItemType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "item_list"
        return context


class ItemDetailView(DetailView):
    model = Item


class MaterialOverviewView(TemplateView):
    template_name = "armory/material_overview.html"
