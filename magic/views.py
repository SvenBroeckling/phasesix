from django.views.generic import ListView, DetailView

from magic.models import BaseSpell


class BaseSpellListView(ListView):
    model = BaseSpell


class BaseSpellDetailView(DetailView):
    model = BaseSpell
