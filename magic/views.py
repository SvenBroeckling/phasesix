from django.views.generic import ListView

from magic.models import BaseSpell


class BaseSpellListView(ListView):
    model = BaseSpell



