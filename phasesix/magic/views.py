from django.views.generic import ListView, DetailView

from magic.models import BaseSpell, SpellOrigin


class SpellOriginView(ListView):
    model = SpellOrigin

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "spell_origin_list"
        return context


class BaseSpellDetailView(DetailView):
    model = BaseSpell

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "spell_origin_list"
        return context
