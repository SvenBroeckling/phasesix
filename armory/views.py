from django.views.generic import ListView

from armory.models import Weapon, RiotGear
from rules.models import Extension


class MaterialListView(ListView):
    def get_queryset(self):
        qs = super().get_queryset()
        extension = self.request.GET.get('extension', None)
        if extension is not None:
            qs = qs.filter(extensions__in=extension)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extension = self.request.GET.get('extension', None)
        context['extensions'] = Extension.objects.first_class_extensions()
        if extension is not None:
            context['selected_extension'] = Extension.objects.get(id=extension)
        return context


class WeaponListView(MaterialListView):
    model = Weapon


class RiotGearListView(MaterialListView):
    model = RiotGear
