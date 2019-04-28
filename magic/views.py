from django.http import JsonResponse
from django.views.generic import TemplateView

from characters.models import Character
from magic.forms import SpellForm
from magic.models import SpellFlavour, SpellType, SpellCost, SpellCastingTime, SpellPower, SpellRange, \
    SpellAreaOfEffect, SpellAreaOfEffectRange, SpellComponents, SpellRule


class XhrSpellView(TemplateView):
    template_name = 'magic/_spell.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrSpellView, self).get_context_data(**kwargs)
        context['object'] = character
        context['form'] = SpellForm()
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        return JsonResponse({'status': 'ok'})


class XhrSpellSummaryView(TemplateView):
    template_name = 'magic/_spell_summary.html'

    def get_context_data(self, **kwargs):
        getdata = self.request.GET
        context = super().get_context_data(**kwargs)

        try:
            spell_rule = SpellRule.objects.get(
                power__id=getdata.get('power'),
                flavour__id=getdata.get('flavour'))
        except SpellRule.DoesNotExist:
            spell_rule = None

        selections = {
            'flavour': SpellFlavour.objects.get(id=getdata.get('flavour')),
            'type': SpellType.objects.get(id=getdata.get('type')),
            'cost': SpellCost.objects.get(id=getdata.get('cost')),
            'casting_time': SpellCastingTime.objects.get(id=getdata.get('casting_time')),
            'power': SpellPower.objects.get(id=getdata.get('power')),
            'range': SpellRange.objects.get(id=getdata.get('range')),
            'area_of_effect': SpellAreaOfEffect.objects.get(
                id=getdata.get('area_of_effect')),
            'area_of_effect_range': SpellAreaOfEffectRange.objects.get(
                id=getdata.get('area_of_effect_range')),
            'components': SpellComponents.objects.get(id=getdata.get('components')),
        }
        spell_points = sum([s.cost for s in selections.values()])

        context.update({
            'name': getdata.get('name'),
            'description': getdata.get('description'),
            'spell_points': spell_points,
            'spell_rule': spell_rule,
        })
        context.update(selections)

        return context
