from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views import View
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _

from characters.models import Character, CharacterSpell
from magic.forms import SpellForm
from magic.models import SpellFlavour, SpellType, SpellCost, SpellCastingTime, SpellPower, SpellRange, \
    SpellAreaOfEffect, SpellAreaOfEffectRange, SpellComponents, SpellRule, Spell


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

        cost = sum([
            SpellFlavour.objects.get(id=request.POST.get('flavour')).cost,
            SpellType.objects.get(id=request.POST.get('type')).cost,
            SpellCost.objects.get(id=request.POST.get('cost')).cost,
            SpellCastingTime.objects.get(id=request.POST.get('casting_time')).cost,
            SpellPower.objects.get(id=request.POST.get('power')).cost,
            SpellRange.objects.get(id=request.POST.get('range')).cost,
            SpellAreaOfEffect.objects.get(id=request.POST.get('area_of_effect')).cost,
            SpellAreaOfEffectRange.objects.get(id=request.POST.get('area_of_effect_range')).cost,
            SpellComponents.objects.get(id=request.POST.get('components')).cost,
        ])
        if cost <= character.spell_points_available:
            spell = Spell.objects.create(
                created_by=request.user if request.user.is_authenticated else None,
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                flavour=SpellFlavour.objects.get(id=request.POST.get('flavour')),
                type=SpellType.objects.get(id=request.POST.get('type')),
                cost=SpellCost.objects.get(id=request.POST.get('cost')),
                casting_time=SpellCastingTime.objects.get(id=request.POST.get('casting_time')),
                power=SpellPower.objects.get(id=request.POST.get('power')),
                range=SpellRange.objects.get(id=request.POST.get('range')),
                area_of_effect=SpellAreaOfEffect.objects.get(id=request.POST.get('area_of_effect')),
                area_of_effect_range=SpellAreaOfEffectRange.objects.get(id=request.POST.get('area_of_effect_range')),
                components=SpellComponents.objects.get(id=request.POST.get('components')))
            CharacterSpell.objects.create(
                spell=spell,
                character=character)

        messages.info(self.request, _('Spell created.'))
        return HttpResponseRedirect(character.get_absolute_url())


class XhrSpellFlavourOptionsView(View):
    def get(self, request, *args, **kwargs):
        st = SpellType.objects.get(id=request.GET.get('pk'))
        return HttpResponse(
            "".join([
                '<option value="{}">{}</option>'.format(s.id, str(s))
                for s in st.spellflavour_set.all()
            ])
        )


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


class XhrSpellCostView(View):

    def get(self, request, *args, **kwargs):
        getdata = self.request.GET

        return JsonResponse({'cost': sum([
            SpellFlavour.objects.get(id=getdata.get('flavour')).cost,
            SpellType.objects.get(id=getdata.get('type')).cost,
            SpellCost.objects.get(id=getdata.get('cost')).cost,
            SpellCastingTime.objects.get(id=getdata.get('casting_time')).cost,
            SpellPower.objects.get(id=getdata.get('power')).cost,
            SpellRange.objects.get(id=getdata.get('range')).cost,
            SpellAreaOfEffect.objects.get(id=getdata.get('area_of_effect')).cost,
            SpellAreaOfEffectRange.objects.get(id=getdata.get('area_of_effect_range')).cost,
            SpellComponents.objects.get(id=getdata.get('components')).cost,
        ])})
