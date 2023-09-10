from django.views.generic import ListView

from rules.models import Template, TemplateCategory


class TemplateListView(ListView):
    model = TemplateCategory
    # def get_queryset(self):
        # if self.request.world_configuration is not None:
        #     qs = qs.for_world(self.request.world_configuration.world)
