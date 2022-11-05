# -*- coding: utf-8 -*-
from django.views.generic import DetailView

from worlds.models import World


class DetailView(DetailView):
    model = World
    template_name = 'world/world_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context
