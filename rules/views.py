# -*- coding: utf-8 -*-
from django.views.generic import ListView

from rules.models import Template


class TemplateListView(ListView):
    def get_queryset(self):
        qs = Template.objects.all()
        if self.request.world_configuration is not None:
            qs = qs.for_world(self.request.world_configuration.world)
        return qs.distinct()
