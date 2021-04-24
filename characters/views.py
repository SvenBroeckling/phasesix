# -*- coding: utf-8 -*-
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import TemplateView, DetailView, FormView

from armory.models import Weapon, RiotGear, ItemType, Item, WeaponModificationType, WeaponModification, WeaponType
from characters.forms import CharacterImageForm, CreateCharacterForm
from characters.models import Character, CharacterWeapon, CharacterRiotGear, CharacterItem, CharacterStatusEffect
from horror.models import QuirkCategory
from rules.models import Extension, Template, Lineage, StatusEffect, Skill


class IndexView(TemplateView):
    template_name = 'characters/index.html'


class CharacterListView(TemplateView):
    template_name = 'characters/character_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        user = self.request.user

        if user.is_authenticated:
            context['own_characters'] = Character.objects.filter(created_by=user)
        else:
            context['own_characters'] = Character.objects.filter(created_by__isnull=True)
        if user.is_authenticated and user.is_staff:
            context['other_peoples_characters'] = Character.objects.exclude(created_by=user)
        return context


class CharacterDetailView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context


class XhrDeleteCharacterView(View):
    def post(self, request, *args, **kwargs):
        obj = Character.objects.get(id=kwargs['pk'])
        if obj.created_by == self.request.user:
            messages.info(request, _('Character deleted.'))
            obj.delete()
        return JsonResponse({
            'status': 'ok',
            'url': reverse('characters:list'),
        })


class XhrSidebarView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_name'] = self.kwargs['sidebar_name']
        context['status_effects'] = StatusEffect.objects.all()
        context['character_form'] = CharacterImageForm(instance=self.object)
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context

    def get_template_names(self):
        return ['characters/sidebar/' + self.kwargs['sidebar_name'] + '.html']


class XhrDetailFragmentView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fragment_name'] = self.kwargs['fragment_name']
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context

    def get_template_names(self):
        return ['characters/fragments/' + self.kwargs['fragment_name'] + '.html']


class XhrCharacterRestView(TemplateView):
    template_name = 'characters/_rest.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context['object'] = character
        return context


class XhrCharacterStatusEffectsChangeView(View):
    template_name = 'characters/_status_effects.html'

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        status_effect = StatusEffect.objects.get(id=request.POST.get('status_effect_id'))
        value = int(request.POST.get('value'))

        if character.may_edit(request.user):
            if value > 0:
                obj, created = CharacterStatusEffect.objects.get_or_create(
                    character=character,
                    status_effect=status_effect,
                    defaults={'base_value': value}
                )
                if not created:
                    obj.base_value = value
                    obj.save()
            else:
                CharacterStatusEffect.objects.filter(
                    character=character, status_effect=status_effect).delete()

            return JsonResponse({
                'status': 'ok',
                'value': value
            })
        return JsonResponse({'status': 'forbidden', 'value': 0})


class CharacterModifyStressView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.may_edit(request.user):
            if self.kwargs['mode'] == 'gain':
                character.stress += 1
                if character.stress >= character.max_stress:
                    quirk = QuirkCategory.objects.order_by('?')[0].quirk_set.order_by('?')[0]
                    character.quirks.add(quirk)
                    character.stress = 0
            elif self.kwargs['mode'] == 'remove':
                if character.stress > 0:
                    character.stress -= 1
            character.save()
        return JsonResponse({'status': 'ok'})


class CharacterModifyDiceView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.may_edit(request.user):
            if self.kwargs['mode'] == 'add_bonus':
                character.bonus_dice_used -= 1
            elif self.kwargs['mode'] == 'remove_bonus':
                character.bonus_dice_used += 1
            if self.kwargs['mode'] == 'add_destiny':
                character.destiny_dice_used -= 1
            elif self.kwargs['mode'] == 'remove_destiny':
                character.destiny_dice_used += 1
            if self.kwargs['mode'] == 'add_reroll':
                character.rerolls_used -= 1
            elif self.kwargs['mode'] == 'remove_reroll':
                character.rerolls_used += 1
            character.save()
        return JsonResponse({'status': 'ok'})


class CharacterModifyHealthView(View):
    def post(self, request, *args, **kwargs):
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
        return JsonResponse({'status': 'ok'})


class CreateCharacterView(TemplateView):
    template_name = 'characters/create_character.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extensions'] = Extension.objects.exclude(is_mandatory=True).exclude(is_epoch=False)
        return context


class CreateCharacterDataView(FormView):
    form_class = CreateCharacterForm
    template_name = 'characters/character_form.html'

    def form_valid(self, form):
        self.object = Character.objects.create(
            name=form.cleaned_data['name'],
            lineage=form.cleaned_data['lineage'])
        self.object.extensions.add(form.cleaned_data['epoch'])

        for e in form.cleaned_data['extensions']:
            self.object.extensions.add(e)
        for skill in Skill.objects.all():
            self.object.characterskill_set.create(skill=skill, base_value=1)

        self.object.created_by = self.request.user if self.request.user.is_authenticated else None
        self.object.save()

        return super().form_valid(form)

    def get_initial(self):
        lineages = Lineage.objects.filter(
            Q(extensions__id=self.kwargs['extension_pk']) |
            Q(extensions__id__in=Extension.objects.filter(is_mandatory=True)))
        return {
            'epoch': self.kwargs['extension_pk'],
            'lineage': lineages.earliest('id')
        }

    def get_success_url(self):
        return reverse('characters:create_character_constructed', kwargs={'pk': self.object.id})


class XhrCreateCharacterPreviewView(DetailView):
    model = Character
    template_name = 'characters/fragments/character.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'fragment_name': 'character'})
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

    def post(self, request, *args, **kwargs):
        obj = Character.objects.get(id=kwargs['pk'])
        obj.set_initial_reputation(obj.reputation_spent + obj.remaining_template_points)
        obj.health = obj.max_health
        obj.arcana = obj.max_arcana
        obj.save()
        return HttpResponseRedirect(obj.get_absolute_url())


class XhrConstructedAddTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])

        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get('template_id'))
            remaining_points = character.remaining_template_points
            if template.cost > remaining_points:
                return JsonResponse({'status': 'notenoughpoints'})
            character.add_template(template)
            return JsonResponse({'status': 'ok', 'remaining_points': remaining_points - template.cost})

        return JsonResponse({'status': 'noop'})


class XhrConstructedRemoveTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])

        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get('template_id'))
            character.remove_template(template)
            return JsonResponse({'status': 'ok', 'remaining_points': character.remaining_template_points})

        return JsonResponse({'status': 'noop'})


class ChangeImageView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return HttpResponseRedirect(character.get_absolute_url())
        form = CharacterImageForm(request.POST, instance=character, files=request.FILES)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(character.get_absolute_url())

# reputation


class XhrReputationView(TemplateView):
    template_name = 'characters/_reputation.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super(XhrReputationView, self).get_context_data(**kwargs)
        context['object'] = character
        context['template_points'] = character.lineage.lineagetemplatepoints_set.filter(
            template_category__allow_for_reputation=True)
        context['character_template_ids'] = [
            ct.template.id for ct in character.charactertemplate_set.all()]
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        operation = request.POST.get('operation', 'noop')
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        if operation == 'add':
            character.reputation += int(request.POST.get('reputation', 0))
            character.save()
        if operation == 'add-template':
            template = Template.objects.get(id=request.POST.get('template_id'))
            if not template.cost <= character.reputation_available:
                return JsonResponse({'status': 'notenoughpoints'})
            character.add_template(template)
        return JsonResponse({'status': 'ok', 'remaining_reputation': character.reputation_available})


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
            return JsonResponse({'status': 'forbidden'})
        character.characterweapon_set.create(weapon=weapon)
        return JsonResponse({'status': 'ok'})


class XhrRemoveWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        weapon.delete()
        return JsonResponse({'status': 'ok'})


class XhrRemoveWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])
        weapon_mod = WeaponModification.objects.get(id=kwargs['weapon_modification_pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        weapon.modifications.remove(weapon_mod)
        return JsonResponse({'status': 'ok'})


class XhrDamageWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        weapon.condition -= 10
        weapon.save()
        return JsonResponse({'status': 'ok'})


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
            return JsonResponse({'status': 'forbidden'})
        character.characterriotgear_set.create(riot_gear=riot_gear)
        return JsonResponse({'status': 'ok'})


class XhrRemoveRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        riot_gear = CharacterRiotGear.objects.get(id=kwargs['riot_gear_pk'])
        riot_gear.delete()
        return JsonResponse({'status': 'ok'})


class XhrDamageRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        riot_gear = CharacterRiotGear.objects.get(id=kwargs['riot_gear_pk'])
        riot_gear.condition -= 10
        riot_gear.save()
        return JsonResponse({'status': 'ok'})


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
            return JsonResponse({'status': 'forbidden'})

        if character.characteritem_set.filter(item=item).exists():
            ci = character.characteritem_set.filter(item=item).latest('id')
            ci.quantity += 1
            ci.save()
        else:
            character.characteritem_set.create(item=item)
        return JsonResponse({'status': 'ok'})


class XhrRemoveItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        item = CharacterItem.objects.get(id=kwargs['item_pk'])
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
        return JsonResponse({'status': 'ok'})


class XhrAddWeaponModView(TemplateView):
    template_name = 'characters/_add_weapon_mod.html'

    def get_context_data(self, **kwargs):
        character =  Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=self.request.GET.get('weapon_id'))
        context = super(XhrAddWeaponModView, self).get_context_data(**kwargs)
        context['character'] = character
        context['weapon'] = weapon
        context['weapon_modification_types'] = WeaponModificationType.objects.for_extensions(
            character.extensions).filter(
            weaponmodification__in=WeaponModification.objects.for_extensions(
                character.extensions))
        return context


class AddWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon_modification = WeaponModification.objects.get(id=kwargs['weapon_modification_pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])

        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        if weapon.weapon.type in weapon_modification.available_for_weapon_types.all():
            weapon.modifications.filter(type=weapon_modification.type).delete()
            weapon.modifications.add(weapon_modification)
        return JsonResponse({'status': 'ok'})

