from django.views.generic import ListView

from characters.character_objects import TemplateObject
from rules.models import TemplateCategory


class TemplateListView(ListView):
    model = TemplateCategory

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "template_list"
        context["character_object"] = TemplateObject(self.request, character=None)
        return context
