# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, DetailView, ListView

from characters.models import Character


class IndexView(TemplateView):
    template_name = 'characters/index.html'


class CharacterListView(ListView):
    model = Character


class RandomCharacterView(TemplateView):
    template_name = 'characters/random_character.html'

    def post(self, request, *args, **kwargs):
        character = Character.objects.create_random_character(request.user)
        return HttpResponseRedirect(character.get_absolute_url())


class CharacterDetailView(DetailView):
    model = Character
