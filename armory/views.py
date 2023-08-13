from django.views.generic import ListView, DetailView

from armory.models import Weapon, RiotGear, Item
from rules.models import Extension


class MaterialListView(ListView):
    def get_queryset(self):
        qs = self.get_model().objects.without_homebrew()
        if self.request.world_configuration is not None:
            qs = qs.for_world(self.request.world_configuration.world)
        if self.request.GET.get("extension", None) is not None:
            qs = qs.filter(extensions__id=self.request.GET.get("extension"))
        return qs.distinct()

    def get_model(self):
        return Weapon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extension = self.request.GET.get("extension", None)
        context["extensions"] = Extension.objects.first_class_extensions()
        if extension is not None:
            context["selected_extension"] = Extension.objects.get(id=extension)
        return context


class WeaponListView(MaterialListView):
    def get_model(self):
        return Weapon


class RiotGearListView(MaterialListView):
    def get_model(self):
        return RiotGear


class ItemListView(MaterialListView):
    def get_model(self):
        return Item


class ItemDetailView(DetailView):
    model = Item
