# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView

from armory.models import Weapon, RiotGear, ItemType, Item, WeaponModificationType, WeaponModification
from characters.models import Character, CharacterWeapon, CharacterRiotGear, CharacterItem
from rules.models import Extension, Template


class IndexView(TemplateView):
    template_name = 'characters/index.html'


class CharacterListView(ListView):
    model = Character


class CreateCharacterView(TemplateView):
    template_name = 'characters/create_character.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extensions'] = Extension.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.create_random_character(request.user)
        return HttpResponseRedirect(character.get_absolute_url())


class CreateCharacterDataView(CreateView):
    model = Character
    fields = 'name', 'lineage'

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        self.object.created_by = request.user if request.user.is_authenticated else None
        self.object.creation_mode = kwargs['mode']

        if kwargs['mode'] == 'random':
            self.object.fill_random()
        else:
            self.object.fill_basics()

        self.object.save()
        return res

    def get_success_url(self):
        if self.kwargs['mode'] == 'random':
            return super().get_success_url()
        elif self.kwargs['mode'] == 'draft':
            return reverse('characters:create_character_draft', kwargs={'pk': self.object.id})
        return super().get_success_url()


class CreateCharacterDraftView(DetailView):
    template_name = 'characters/create_character_draft.html'
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_templates'] = Template.objects.order_by('?')[:3]
        return context


class XhrDraftAddTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.created_by == request.user or not request.user.is_authenticated and character.created_by is None:
            template = Template.objects.get(id=request.POST.get('template_id'))
            character.add_template(template)

        templates = Template.objects.exclude(
            id__in=[i.template.id for i in character.charactertemplate_set.all()])
        return render(
            request,
            'characters/_draft_template_list.html',
            {
                'initial_templates': templates.order_by('?')[:3],
                'object': character,
            }
        )


class XhrDraftPreviewView(DetailView):
    model = Character
    template_name = 'characters/fragments/character.html'


class XhrDraftPreviewSelectedTemplatesView(TemplateView):
    model = Character
    template_name = 'characters/_draft_selected_templates.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = Character.objects.get(id=kwargs['pk']).charactertemplate_set.order_by('-id')
        return context


class CharacterDetailView(DetailView):
    model = Character

# gear


class XhrBuyWeaponsView(TemplateView):
    template_name = 'characters/_buy_weapons.html'

    def get_context_data(self, **kwargs):
        context = super(XhrBuyWeaponsView, self).get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=kwargs['pk'])
        return context


class BuyWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = Weapon.objects.get(id=kwargs['weapon_pk'])
        if character.organization.cash < weapon.price or character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())
        character.characterweapon_set.create(weapon=weapon)
        character.organization.cash -= weapon.price
        character.organization.save()
        character.save()
        return HttpResponseRedirect(character.get_absolute_url())


class SellWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])
        if character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())

        character.organization.cash += weapon.weapon.price
        for wm in weapon.modifications.all():
            character.organization.cash += wm.price
        character.organization.save()
        character.save()
        weapon.delete()
        return HttpResponseRedirect(character.get_absolute_url())


class XhrBuyRiotGearView(TemplateView):
    template_name = 'characters/_buy_riot_gear.html'

    def get_context_data(self, **kwargs):
        context = super(XhrBuyRiotGearView, self).get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=kwargs['pk'])
        context['riot_gear'] = RiotGear.objects.all()
        return context


class BuyRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        riot_gear = RiotGear.objects.get(id=kwargs['riot_gear_pk'])
        if character.organization.cash < riot_gear.price or character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())
        character.characterriotgear_set.create(riot_gear=riot_gear)
        character.organization.cash -= riot_gear.price
        character.organization.save()
        character.save()
        return HttpResponseRedirect(character.get_absolute_url())


class SellRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())
        riot_gear = CharacterRiotGear.objects.get(id=kwargs['riot_gear_pk'])
        character.organization.cash += riot_gear.riot_gear.price
        character.organization.save()
        character.save()
        riot_gear.delete()
        return HttpResponseRedirect(character.get_absolute_url())


class XhrBuyItemsView(TemplateView):
    template_name = 'characters/_buy_items.html'

    def get_context_data(self, **kwargs):
        context = super(XhrBuyItemsView, self).get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=kwargs['pk'])
        context['item_types'] = ItemType.objects.all()
        return context


class BuyItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        item = Item.objects.get(id=kwargs['item_pk'])

        if character.organization.cash < item.price or character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())

        if character.characteritem_set.filter(item=item).exists():
            ci = character.characteritem_set.filter(item=item).latest('id')
            ci.quantity += 1
            ci.save()
        else:
            character.characteritem_set.create(item=item)
        character.organization.cash -= item.price
        character.organization.save()
        character.save()
        return HttpResponseRedirect(character.get_absolute_url())


class SellItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())
        item = CharacterItem.objects.get(id=kwargs['item_pk'])
        character.organization.cash += item.item.price
        character.organization.save()
        character.save()
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
        return HttpResponseRedirect(character.get_absolute_url())


class XhrBuyWeaponModView(TemplateView):
    template_name = 'characters/_buy_weapon_mod.html'

    def get_context_data(self, **kwargs):
        context = super(XhrBuyWeaponModView, self).get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=kwargs['pk'])
        context['weapon'] = CharacterWeapon.objects.get(id=self.request.GET.get('weapon_id'))
        context['weapon_modification_types'] = WeaponModificationType.objects.all()
        return context


class BuyWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon_modification = WeaponModification.objects.get(id=kwargs['weapon_modification_pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])

        if character.organization.cash < weapon_modification.price or character.created_by != request.user:
            return HttpResponseRedirect(character.get_absolute_url())

        if weapon.weapon.type in weapon_modification.available_for_weapon_types.all():
            weapon.modifications.add(weapon_modification)

        character.organization.cash -= weapon_modification.price
        character.organization.save()
        character.save()
        return HttpResponseRedirect(character.get_absolute_url())

