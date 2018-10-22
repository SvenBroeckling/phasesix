from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

import random

from gmtools.forms import CombatSimDummyForm


class CombatSimView(TemplateView):
    template_name = 'gmtools/combat_sim.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dummy_form_1'] = CombatSimDummyForm(prefix='dummy_form_1', initial={'health': 6, 'attack_value': 2})
        context['dummy_form_2'] = CombatSimDummyForm(prefix='dummy_form_2', initial={'health': 6, 'attack_value': 2})
        return context

    def post(self, request, *args, **kwargs):
        results = []

        form_1 = CombatSimDummyForm(request.POST, prefix='dummy_form_1')
        form_2 = CombatSimDummyForm(request.POST, prefix='dummy_form_2')
        iterations = int(request.POST.get('iterations', '10'))
        if form_1.is_valid() and form_2.is_valid():
            d1 = form_1.cleaned_data
            d2 = form_2.cleaned_data

            d1_max_health = d1['health']
            d2_max_health = d2['health']
            d1_health = d1['health']
            d2_health = d2['health']

            for i in range(iterations):
                actions = []

                hits = self.attack_roll(actions, d1, d2)
                if hits > 0:
                    hits = self.cover_roll(actions, d1, d2, hits)
                wounds = self.armor_roll(actions, d1, d2, hits)
                d2_health -= wounds * d1['weapon'].wounds
                if d2_health < 0:
                    d2_health = 0

                actions.append({'switch_attacker': True})

                if d2_health > 0:
                    hits = self.attack_roll(actions, d2, d1)
                    if hits > 0:
                        hits = self.cover_roll(actions, d2, d1, hits)
                    wounds = self.armor_roll(actions, d2, d1, hits)
                    d1_health -= wounds * d2['weapon'].wounds
                    if d1_health < 0:
                        d1_health = 0

                results.append({
                    'd1_health': range(d1_health),
                    'd1_empty_health': range(d1_max_health - d1_health),
                    'd2_health': range(d2_health),
                    'd2_empty_health': range(d2_max_health - d2_health),
                    'actions': actions[:]
                })

                if d1_health <= 0 or d2_health <= 0:
                    break

            return render(
                request,
                'gmtools/combat_sim_results.html',
                {'dummy_1': d1, 'dummy_2': d2, 'results': results})
        messages.error(self.request, _('You have to select weapons.'))
        return HttpResponseRedirect(reverse('gmtools:combat_sim'))

    @staticmethod
    def attack_roll(actions, attacker, defender):
        dice = []
        hits = 0
        for i in range(attacker['weapon'].attacks_per_action):
            d = random.randint(1, 6)
            if d >= 7 - attacker['attack_value']:
                dice.append((d, True))
                hits += 1
            else:
                dice.append((d, False))
        actions.append({
            'active_character': attacker,
            'mode': _('attack roll'),
            'successes': hits,
            'dice': dice
        })
        return hits

    @staticmethod
    def cover_roll(actions, attacker, defender, hits):
        if not hits:
            return 0
        dice = []
        prevented = 0
        for i in range(hits):
            d = random.randint(1, 6)
            if d >= int(defender['cover']):
                dice.append((d, True))
                prevented += 1
            else:
                dice.append((d, False))
        actions.append({
            'active_character': defender,
            'mode': _('cover roll'),
            'successes': prevented,
            'dice': dice
        })
        return hits - prevented

    @staticmethod
    def armor_roll(actions, attacker, defender, hits):
        if not hits:
            return 0
        dice = []
        prevented = 0
        armor = defender['riot_gear'] and defender['riot_gear'].protection_ballistic or 0
        for i in range(hits):
            d = random.randint(1, 6)
            if d >= 7 - int(armor) + attacker['weapon'].penetration:
                dice.append((d, True))
                prevented += 1
            else:
                dice.append((d, False))
        actions.append({
            'active_character': defender,
            'mode': _('armor roll'),
            'successes': prevented,
            'dice': dice
        })
        actions.append({
            'active_character': defender,
            'damage': (hits - prevented) * attacker['weapon'].wounds,
            'mode': _('damage'),
        })
        return hits - prevented
