from django.views.generic import ListView, DetailView

from magic.models import BaseSpell


class BaseSpellListView(ListView):
    def get_queryset(self):
        return BaseSpell.objects.without_homebrew()


class BaseSpellDetailView(DetailView):
    model = BaseSpell
