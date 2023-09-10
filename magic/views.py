from django.views.generic import ListView, DetailView

from magic.models import BaseSpell, SpellOrigin


class SpellOriginView(ListView):
    model = SpellOrigin


class BaseSpellListView(ListView):
    def get_queryset(self):
        return BaseSpell.objects.without_homebrew().filter(
            origin__id=self.kwargs["origin_pk"]
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["origin"] = SpellOrigin.objects.get(id=self.kwargs["origin_pk"])
        return context


class BaseSpellDetailView(DetailView):
    model = BaseSpell
