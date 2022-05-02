from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _

from armory.models import Item, RiotGear, Weapon
from characters.models import Character
from homebrew.forms import CreateItemForm, CreateRiotGearForm, CreateWeaponForm, CreateBaseSpellForm
from magic.models import BaseSpell


class IndexView(TemplateView):
    template_name = 'homebrew/index.html'


class XhrCreateItemView(TemplateView):
    template_name = 'homebrew/modals/create_item.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=self.kwargs['character_pk'])
        context['form'] = CreateItemForm(
            initial={'weight': 1, 'price': 10, 'concealment': 0})
        return context


class CreateItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=self.kwargs['character_pk'])
        if character.may_edit(request.user):
            form = CreateItemForm(request.POST)
            if form.is_valid():
                item = Item.objects.create(
                    name_de=form.cleaned_data['name'],
                    description_de=form.cleaned_data['description'],
                    type=form.cleaned_data['type'],
                    weight=form.cleaned_data['weight'],
                    price=form.cleaned_data['price'],
                    concealment=form.cleaned_data['concealment'],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_campaign=character.campaign)
                for ext in character.extensions.all():
                    item.extensions.add(ext)
                if form['add_to_character']:
                    character.characteritem_set.create(item=item)

        return JsonResponse({'status': 'ok'})


class XhrCreateRiotGearView(TemplateView):
    template_name = 'homebrew/modals/create_riot_gear.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=self.kwargs['character_pk'])
        context['form'] = CreateRiotGearForm(
            initial={'weight': 1,
                     'protection': 1,
                     'evasion': 0,
                     'price': 10,
                     'concealment': 0})
        return context


class CreateRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=self.kwargs['character_pk'])
        if character.may_edit(request.user):
            form = CreateRiotGearForm(request.POST)
            if form.is_valid():
                riot_gear = RiotGear.objects.create(
                    name_de=form.cleaned_data['name'],
                    description_de=form.cleaned_data['description'],
                    protection_ballistic=form.cleaned_data['protection'],
                    evasion=form.cleaned_data['evasion'],
                    weight=form.cleaned_data['weight'],
                    price=form.cleaned_data['price'],
                    concealment=form.cleaned_data['concealment'],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_campaign=character.campaign)
                for ext in character.extensions.all():
                    riot_gear.extensions.add(ext)
                if form['add_to_character']:
                    character.characterriotgear_set.create(riot_gear=riot_gear)

        return JsonResponse({'status': 'ok'})


class XhrCreateWeaponView(TemplateView):
    template_name = 'homebrew/modals/create_weapon.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=self.kwargs['character_pk'])
        context['form'] = CreateWeaponForm(
            initial={
                'bonus_dice': 0,
                'wounds': 0,
                'piercing': 1,
                'range_meter': 20,
                'capacity': 1,
                'weight': 1,
                'price': 10,
                'concealment': 0})
        return context


class CreateWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=self.kwargs['character_pk'])
        if character.may_edit(request.user):
            form = CreateWeaponForm(request.POST)
            if form.is_valid():
                weapon = Weapon.objects.create(
                    name_de=form.cleaned_data['name'],
                    description_de=form.cleaned_data['description'],
                    type=form.cleaned_data['type'],
                    weight=form.cleaned_data['weight'],
                    price=form.cleaned_data['price'],
                    capacity=form.cleaned_data['capacity'],
                    concealment=form.cleaned_data['concealment'],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_campaign=character.campaign)
                for ext in character.extensions.all():
                    weapon.extensions.add(ext)
                if form['add_to_character']:
                    character.characterweapon_set.create(weapon=weapon)
            else:
                print(form.errors)

        return JsonResponse({'status': 'ok'})


class XhrCreateBaseSpellView(TemplateView):
    template_name = 'homebrew/modals/create_base_spell.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=self.kwargs['character_pk'])
        context['form'] = CreateBaseSpellForm(
            initial={
                'rules': _('Spell Rules'),
                'spell_point_cost': 5,
                'arcana_cost': 1,
                'power': 1,
                'range': 10,
                'actions': 1})
        return context


class CreateBaseSpellView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=self.kwargs['character_pk'])
        if character.may_edit(request.user):
            form = CreateBaseSpellForm(request.POST)
            if form.is_valid():
                base_spell = BaseSpell.objects.create(
                    name_de=form.cleaned_data['name'],
                    rules_de=form.cleaned_data['rules'],
                    spell_point_cost=form.cleaned_data['spell_point_cost'],
                    arcana_cost=form.cleaned_data['arcana_cost'],
                    power=form.cleaned_data['power'],
                    range=form.cleaned_data['range'],
                    actions=form.cleaned_data['actions'],
                    type=form.cleaned_data['type'],
                    variant=form.cleaned_data['variant'],
                    shape=form.cleaned_data['shape'],
                    is_ritual=form.cleaned_data['is_ritual'],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_campaign=character.campaign)
                if form['add_to_character']:
                    character.characterspell_set.create(spell=base_spell)
            else:
                print(form.errors)

        return JsonResponse({'status': 'ok'})

