from django.views.generic import ListView, DetailView

from bestiary.models import Foe


class FoeListView(ListView):
    model = Foe


class FoeDetailView(DetailView):
    model = Foe