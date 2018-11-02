# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView

from armory.models import Weapon, RiotGear, ItemType, Item, WeaponModificationType, WeaponModification, WeaponType
from characters.forms import CharacterImageForm
from characters.models import Character, CharacterWeapon, CharacterRiotGear, CharacterItem
from rules.models import Extension, Template, Lineage


class IndexView(TemplateView):
    template_name = 'characters/index.html'


class CharacterListView(ListView):
    model = Character


class CharacterDetailView(DetailView):
    model = Character


class CharacterModifyHealthView(View):
    def get(self, request, *args, **kwargs):
        # TODO: Change this to Xhr/Fragments
        character = Character.objects.get(id=kwargs['pk'])
        if character.may_edit(request.user):
            if self.kwargs['mode'] == 'heal':
                if character.health < character.max_health:
                    character.health += 1
            elif self.kwargs['mode'] == 'wound':
                if character.boost > 0:
                    character.boost -= 1
                elif character.health > 0:
                    character.health -= 1
            elif self.kwargs['mode'] == 'boost':
                character.boost += 1
            character.save()
        return HttpResponseRedirect(character.get_absolute_url())


class CreateCharacterView(TemplateView):
    template_name = 'characters/create_character.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extensions'] = Extension.objects.exclude(is_mandatory=True)
        return context


class CreateCharacterDataView(CreateView):
    model = Character
    fields = 'name', 'lineage', 'extensions'

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

    def get_initial(self):
        lineages = Lineage.objects.filter(
            Q(extension__id=self.kwargs['extension_pk']) |
            Q(extension__id__in=Extension.objects.filter(is_mandatory=True)))
        return {
            'extensions': self.kwargs['extension_pk'],
            'lineage': lineages.earliest('id')
        }

    def get_success_url(self):
        if self.kwargs['mode'] == 'random':
            return super().get_success_url()
        elif self.kwargs['mode'] == 'draft':
            return reverse('characters:create_character_draft', kwargs={'pk': self.object.id})
        return reverse('characters:create_character_constructed', kwargs={'pk': self.object.id})


class XhrCreateCharacterPreviewView(DetailView):
    model = Character
    template_name = 'characters/fragments/character.html'


class CreateCharacterDraftView(DetailView):
    template_name = 'characters/create_character_draft.html'
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_templates'] = Template.objects.for_extensions(self.object.extensions).order_by('?')[:3]
        return context


class XhrDraftAddTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get('template_id'))
            character.add_template(template)

        templates = Template.objects.for_extensions(character.extensions).exclude(
            id__in=[i.template.id for i in character.charactertemplate_set.all()])
        return render(
            request,
            'characters/_draft_template_list.html',
            {
                'initial_templates': templates.order_by('?')[:3],
                'object': character,
            }
        )


class XhrDraftPreviewSelectedTemplatesView(TemplateView):
    model = Character
    template_name = 'characters/_draft_selected_templates.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = Character.objects.get(id=kwargs['pk']).charactertemplate_set.order_by('-id')
        return context


class CreateCharacterConstructedView(DetailView):
    template_name = 'characters/create_character_constructed.html'
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_points'] = self.object.lineage.lineagetemplatepoints_set.all()
        context['character_template_ids'] = [
            ct.template.id for ct in self.object.charactertemplate_set.all()]
        return context


class XhrConstructedAddTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])

        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get('template_id'))
            available_points = character.lineage.lineagetemplatepoints_set.get(
                template_category=template.category).points
            spent_points = character.charactertemplate_set.filter(
                template__category=template.category).aggregate(Sum('template__cost'))['template__cost__sum'] or 0
            if spent_points + template.cost > available_points:
                return JsonResponse({'status': 'notenoughpoints'})
            character.add_template(template)
            return JsonResponse({'status': 'ok', 'remaining_points': available_points - spent_points - template.cost})

        return JsonResponse({'status': 'noop'})


class XhrConstructedRemoveTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])

        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get('template_id'))
            character.remove_template(template)
            available_points = character.lineage.lineagetemplatepoints_set.get(
                template_category=template.category).points
            spent_points = character.charactertemplate_set.filter(
                template__category=template.category).aggregate(Sum('template__cost'))['template__cost__sum'] or 0
            return JsonResponse({'status': 'ok', 'remaining_points': available_points - spent_points})

        return JsonResponse({'status': 'noop'})


class XhrChangeImageView(TemplateView):
    template_name = 'characters/_change_image.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrChangeImageView, self).get_context_data(**kwargs)
        context['character'] = character
        context['form'] = CharacterImageForm(instance=character)
        return context


class ChangeImageView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        form = CharacterImageForm(request.POST, instance=character, files=request.FILES)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(character.get_absolute_url())

# gear


class XhrAddWeaponsView(TemplateView):
    template_name = 'characters/_add_weapons.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrAddWeaponsView, self).get_context_data(**kwargs)
        context['character'] = character
        context['weapon_types'] = WeaponType.objects.for_extensions(character.extensions)
        return context


class AddWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = Weapon.objects.get(id=kwargs['weapon_pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        character.characterweapon_set.create(weapon=weapon)
        return HttpResponseRedirect(character.get_absolute_url())


class RemoveWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        weapon.delete()
        return HttpResponseRedirect(character.get_absolute_url())


class XhrAddRiotGearView(TemplateView):
    template_name = 'characters/_add_riot_gear.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrAddRiotGearView, self).get_context_data(**kwargs)
        context['character'] = character
        context['riot_gear'] = RiotGear.objects.for_extensions(character.extensions)
        return context


class AddRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        riot_gear = RiotGear.objects.get(id=kwargs['riot_gear_pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        character.characterriotgear_set.create(riot_gear=riot_gear)
        return HttpResponseRedirect(character.get_absolute_url())


class RemoveRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        riot_gear = CharacterRiotGear.objects.get(id=kwargs['riot_gear_pk'])
        riot_gear.delete()
        return HttpResponseRedirect(character.get_absolute_url())


class XhrAddItemsView(TemplateView):
    template_name = 'characters/_add_items.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrAddItemsView, self).get_context_data(**kwargs)
        context['character'] = character
        context['item_types'] = ItemType.objects.for_extensions(character.extensions)
        return context


class AddItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        item = Item.objects.get(id=kwargs['item_pk'])

        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())

        if character.characteritem_set.filter(item=item).exists():
            ci = character.characteritem_set.filter(item=item).latest('id')
            ci.quantity += 1
            ci.save()
        else:
            character.characteritem_set.create(item=item)
        return HttpResponseRedirect(character.get_absolute_url())


class RemoveItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        item = CharacterItem.objects.get(id=kwargs['item_pk'])
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
        return HttpResponseRedirect(character.get_absolute_url())


class XhrAddWeaponModView(TemplateView):
    template_name = 'characters/_add_weapon_mod.html'

    def get_context_data(self, **kwargs):
        context = super(XhrAddWeaponModView, self).get_context_data(**kwargs)
        context['character'] = Character.objects.get(id=kwargs['pk'])
        context['weapon'] = CharacterWeapon.objects.get(id=self.request.GET.get('weapon_id'))
        context['weapon_modification_types'] = WeaponModificationType.objects.all()
        return context


class AddWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon_modification = WeaponModification.objects.get(id=kwargs['weapon_modification_pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])

        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())

        if weapon.weapon.type in weapon_modification.available_for_weapon_types.all():
            weapon.modifications.add(weapon_modification)
        return HttpResponseRedirect(character.get_absolute_url())
