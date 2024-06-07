from django.views.generic import ListView, DetailView

from magic.models import BaseSpell, SpellOrigin


class SpellOriginView(ListView):
    model = SpellOrigin

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "spell_origin_list"
        return context


class BaseSpellListView(ListView):
    def get_queryset(self):
        return BaseSpell.objects.without_homebrew().filter(
            origin__id=self.kwargs["origin_pk"]
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["origin"] = SpellOrigin.objects.get(id=self.kwargs["origin_pk"])
        context["navigation"] = "spell_origin_list"
        return context


class BaseSpellDetailView(DetailView):
    model = BaseSpell

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "spell_origin_list"
        return context
