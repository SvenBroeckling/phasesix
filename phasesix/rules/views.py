from django.views.generic import ListView

from characters.character_objects import TemplateObject, FoeObject
from rules.models import TemplateCategory, FoeType


class TemplateListView(ListView):
    model = TemplateCategory

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "template_list"
        context["character_object"] = TemplateObject(self.request, character=None)
        return context


class FoeListView(ListView):
    model = FoeType

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "foe_list"
        context["character_object"] = FoeObject(self.request, character=None)
        return context
