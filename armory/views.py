from django.views.generic import ListView, DetailView, TemplateView

from armory.models import Item, WeaponType, RiotGearType, ItemType


class MaterialListView(ListView):
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.world_configuration is not None:
            qs = qs.for_world(self.request.world_configuration.world)
        if self.request.GET.get("extension", None) is not None:
            qs = qs.filter(extensions__id=self.request.GET.get("extension"))
        return qs.distinct()


class WeaponListView(MaterialListView):
    model = WeaponType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "weapon_list"
        return context


class RiotGearListView(MaterialListView):
    model = RiotGearType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "riot_gear_list"
        return context


class ItemListView(MaterialListView):
    model = ItemType

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "item_list"
        return context


class ItemDetailView(DetailView):
    model = Item


class MaterialOverviewView(TemplateView):
    template_name = "armory/material_overview.html"
