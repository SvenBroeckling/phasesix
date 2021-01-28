from django.shortcuts import render
from django.views.generic import TemplateView, CreateView

from armory.models import Item


class IndexView(TemplateView):
    template_name = 'homebrew/index.html'


class CreateItemView(CreateView):
    model = Item
