# -*- coding: utf-8 -*-

from channels.layers import get_channel_layer
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import TemplateView, DetailView, FormView

from armory.models import Weapon, RiotGear, ItemType, Item, WeaponModificationType, WeaponModification, WeaponType, \
    WeaponAttackMode, CurrencyMapUnit
from campaigns.consumers import roll_and_send
from campaigns.models import Campaign
from characters.forms import CharacterImageForm, CreateCharacterDataForm, CreateRandomNPCForm, CreateCharacterExtensionsForm
from characters.models import Character, CharacterWeapon, CharacterRiotGear, CharacterItem, CharacterStatusEffect, \
    CharacterSpell, CharacterSkill, CharacterAttribute, CharacterNote
from horror.models import QuirkCategory, Quirk
from magic.models import SpellType, SpellTemplateCategory, SpellTemplate
from rules.models import Extension, Template, Lineage, StatusEffect, Skill, Attribute, Knowledge


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_characters'] = self.request.user.character_set.all()
        return context


class CharacterListView(TemplateView):
    template_name = 'characters/character_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        user = self.request.user

        if user.is_authenticated:
            context['own_characters'] = Character.objects.with_templates().filter(created_by=user)
        if user.is_authenticated and user.is_staff:
            context['other_peoples_characters'] = Character.objects.with_templates().exclude(
                Q(created_by=user) | Q(created_by__isnull=True))
        context['anonymous_characters'] = Character.objects.with_templates().filter(created_by__isnull=True)
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
        try:
            context['may_edit'] = self.object.may_edit(self.request.user)
        except AttributeError:
            context['may_edit'] = False
        return context

    def get_template_names(self):
        return ['characters/sidebar/' + self.kwargs['sidebar_template'] + '.html']


class XhrCharacterSidebarView(XhrSidebarView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_effects'] = StatusEffect.objects.filter(is_active=True).order_by('ordering')
        context['character_form'] = CharacterImageForm(instance=self.object)
        return context


class XhrCharacterWeaponSidebarView(XhrSidebarView):
    model = CharacterWeapon


class XhrCharacterRiotGearSidebarView(XhrSidebarView):
    model = CharacterRiotGear


class XhrCharacterItemSidebarView(XhrSidebarView):
    model = CharacterItem


class XhrCharacterSpellSidebarView(XhrSidebarView):
    model = CharacterSpell


class XhrCharacterSkillSidebarView(XhrSidebarView):
    model = CharacterSkill


class XhrCharacterAttributeSidebarView(XhrSidebarView):
    model = CharacterAttribute


class XhrCharacterNoteSidebarView(XhrSidebarView):
    model = CharacterNote


class XhrCharacterKnowledgeSidebarView(XhrSidebarView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['knowledge'] = Knowledge.objects.get(id=self.kwargs['knowledge_pk'])
        return context


class XhrCharacterTemplateShadowSidebarView(XhrSidebarView):
    model = Template


class XhrDetailFragmentView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fragment_template'] = self.kwargs['fragment_template']
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context

    def get_template_names(self):
        return ['characters/fragments/' + self.kwargs['fragment_template'] + '.html']


class XhrCharacterRestView(TemplateView):
    template_name = 'characters/modals/rest.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context['object'] = character
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        minimum_roll = character.minimum_roll
        mode = request.POST.get('mode', 'manual')

        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        if mode == 'auto':
            character.bonus_dice_used = 0
            character.destiny_dice_used = 0
            character.rerolls_used = 0

            rest_wound_roll = roll_and_send(
                character.id,
                f'{character.rest_wound_dice}d6',
                ugettext('Rest'),
                ugettext('Wound Roll'))

            for d in filter(lambda x: x >= minimum_roll, rest_wound_roll):
                if character.health < character.max_health:
                    character.health += 1

            if 'magic' in character.extension_enabled:
                rest_arcana_roll = roll_and_send(
                    character.id,
                    f'{character.rest_arcana_dice}d6',
                    ugettext('Rest'),
                    ugettext('Arcana Roll'))

                for d in filter(lambda x: x >= minimum_roll, rest_arcana_roll):
                    if character.arcana < character.max_arcana:
                        character.arcana += 1

            if 'horror' in character.extension_enabled:
                rest_stress_roll = roll_and_send(
                    character.id,
                    f'{character.rest_stress_dice}d6',
                    ugettext('Rest'),
                    ugettext('Stress Roll'))

                if len(list(filter(lambda x: x >= minimum_roll, rest_stress_roll))):
                    if character.stress > 0:
                        character.stress -= 1

            character.save()

        return JsonResponse({'status': 'ok'})


class XhrCharacterStatusEffectsChangeView(View):
    template_name = 'characters/_status_effects.html'

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        status_effect = StatusEffect.objects.get(id=kwargs['status_effect_pk'])

        if character.may_edit(request.user):
            obj, created = CharacterStatusEffect.objects.get_or_create(
                character=character,
                status_effect=status_effect)

            if kwargs['mode'] == 'decrease':
                if obj.base_value > 0:
                    obj.base_value -= 1
                    obj.save()
                if obj.base_value <= 0:
                    obj.delete()
            if kwargs['mode'] == 'increase':
                obj.base_value += 1
                obj.save()

            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'forbidden', 'value': 0})


class CharacterModifyStressView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.may_edit(request.user):
            if self.kwargs['mode'] == 'gain':
                character.stress += 1
                if character.stress >= character.max_stress:
                    character.quirks_gained += 1
                    character.stress = 0
            elif self.kwargs['mode'] == 'remove':
                if character.stress > 0:
                    character.stress -= 1
            character.save()
        return JsonResponse({'status': 'ok'})


class XhrAddQuirkView(TemplateView):
    template_name = 'characters/modals/add_quirk.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context['character'] = character
        context['quirk_categories'] = QuirkCategory.objects.all()
        return context


class AddQuirkView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        quirk = Quirk.objects.get(id=kwargs['quirk_pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        character.quirks.add(quirk)
        return JsonResponse({'status': 'ok'})



class CharacterAttackView(View):
    def post(self, request, *args, **kwargs):
        character_weapon = CharacterWeapon.objects.get(id=kwargs['characterweapon_pk'])
        weapon_attack_mode = WeaponAttackMode.objects.get(id=kwargs['weapon_attackmode_pk'])

        if not character_weapon.character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        character_weapon.capacity_used += weapon_attack_mode.capacity_consumed
        character_weapon.save()

        return JsonResponse({'status': 'ok'})


class CharacterReloadView(View):
    def post(self, request, *args, **kwargs):
        character_weapon = CharacterWeapon.objects.get(id=kwargs['characterweapon_pk'])

        if not character_weapon.character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        character_weapon.capacity_used = 0
        character_weapon.save()

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
        context['extensions'] = Extension.objects.exclude(
            is_mandatory=True).exclude(type__in=['e', 'x']).exclude(is_active=False)
        return context


class CreateCharacterEpochView(TemplateView):
    template_name = 'characters/create_character_epoch.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['world_pk'] = self.kwargs['world_pk']
        context['extensions'] = Extension.objects.exclude(
            is_mandatory=True).exclude(type__in=['x', 'w']).exclude(is_active=False)
        return context


class CreateCharacterExtensionsView(FormView):
    template_name = 'characters/create_character_extensions.html'
    form_class = CreateCharacterExtensionsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['world_pk'] = self.kwargs['world_pk']
        context['epoch_pk'] = self.kwargs['epoch_pk']
        context['extensions'] = Extension.objects.exclude(
            is_mandatory=True).exclude(type__in=['e', 'w']).exclude(is_active=False)
        return context


class CreateCharacterDataView(FormView):
    form_class = CreateCharacterDataForm
    template_name = 'characters/character_form.html'

    @property
    def campaign_to_join(self):
        campaign_pk = self.kwargs.get('campaign_pk', None)
        if campaign_pk is not None:
            campaign = Campaign.objects.get(id=campaign_pk)
            if campaign.campaign_hash == self.kwargs.get('hash', ''):
                return campaign
        return None

    @property
    def lineages(self):
        return Lineage.objects.filter(
            Q(extensions__id=self.kwargs['epoch_pk']) |
            Q(extensions__id=self.kwargs['world_pk']) |
            Q(extensions__id__in=Extension.objects.filter(
                Q(is_mandatory=True) | Q(id__in=self.request.GET.getlist('extensions'))))
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['lineage'].queryset = self.lineages
        return form

    def form_valid(self, form):
        self.object = Character.objects.create(
            name=form.cleaned_data['name'],
            lineage=form.cleaned_data['lineage'])
        self.object.extensions.add(form.cleaned_data['epoch'])
        self.object.extensions.add(form.cleaned_data['world'])

        for e in form.cleaned_data['extensions']:
            self.object.extensions.add(e)
        for skill in Skill.objects.all():
            self.object.characterskill_set.create(skill=skill)
        for attribute in Attribute.objects.all():
            self.object.characterattribute_set.create(attribute=attribute)

        if self.campaign_to_join is not None:
            for ext in self.campaign_to_join.extensions.all():
                self.object.extensions.add(ext)
            if self.kwargs.get('type', 'pc') == 'pc':
                self.object.campaign = self.campaign_to_join
            else:
                self.object.npc_campaign = self.campaign_to_join

        self.object.created_by = self.request.user if self.request.user.is_authenticated else None
        self.object.save()

        return super().form_valid(form)

    def get_initial(self):
        return {
            'epoch': self.kwargs['epoch_pk'],
            'world': self.kwargs['world_pk'],
            'lineage': self.lineages.earliest('id'),
            'extensions': Extension.objects.filter(id__in=self.request.GET.getlist('extensions'))
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extensions'] = Extension.objects.filter(type__in=['x', 'w'], is_mandatory=False, is_active=True)
        context['campaign'] = self.campaign_to_join
        return context

    def get_success_url(self):
        return reverse('characters:create_character_constructed', kwargs={'pk': self.object.id})


class CreateRandomNPCView(CreateCharacterDataView):
    form_class = CreateRandomNPCForm
    template_name = 'characters/random_npc_form.html'

    def form_valid(self, form):
        result = super().form_valid(form)
        self.object.randomize(form.cleaned_data['starting_reputation'])
        self.object.set_initial_reputation(self.object.reputation_spent + self.object.remaining_template_points)
        return result

    def get_success_url(self):
        return reverse('campaigns:detail', kwargs={'pk': self.campaign_to_join.id})


class XhrCreateCharacterPreviewView(DetailView):
    model = Character
    template_name = 'characters/fragments/character.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'fragment_template': 'character',
            'model_name': 'Character'
        })
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
        if not request.user.is_authenticated:  # anonymous users may not upload images
            return HttpResponseRedirect(character.get_absolute_url())
        form = CharacterImageForm(request.POST, instance=character, files=request.FILES)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(character.get_absolute_url())


# reputation


class XhrReputationView(TemplateView):
    template_name = 'characters/modals/reputation.html'

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
    template_name = 'characters/modals/add_weapons.html'

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


class XhrWeaponConditionView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon = CharacterWeapon.objects.get(id=kwargs['weapon_pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        if kwargs['mode'] == 'damage':
            weapon.condition -= 10
        else:
            weapon.condition += 10

        weapon.save()
        return JsonResponse({'status': 'ok'})


class XhrAddRiotGearView(TemplateView):
    template_name = 'characters/modals/add_riot_gear.html'

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


class XhrRiotGearConditionView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        riot_gear = CharacterRiotGear.objects.get(id=kwargs['riot_gear_pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        if kwargs['mode'] == 'damage':
            riot_gear.condition -= 10
        else:
            riot_gear.condition += 10

        riot_gear.save()
        return JsonResponse({'status': 'ok'})


class XhrAddItemsView(TemplateView):
    template_name = 'characters/modals/add_items.html'

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

        # Containers don't stack
        if character.characteritem_set.filter(item=item).exists() and not item.is_container:
            ci = character.characteritem_set.filter(item=item).latest('id')
            ci.quantity += 1
            ci.save()
        else:
            character.characteritem_set.create(item=item)
        return JsonResponse({'status': 'ok'})


class XhrUpdateItemSortOrderView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        for pk, order in request.POST.items():
            character.characteritem_set.filter(id=pk).update(ordering=order)

        return JsonResponse({'status': 'ok'})


class XhrModifyItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        item = CharacterItem.objects.get(id=kwargs['item_pk'])

        if self.kwargs['mode'] == 'add':
            item.quantity += 1
        if self.kwargs['mode'] == 'remove':
            if item.quantity > 0:
                item.quantity -= 1
        if self.kwargs['mode'] == 'add_charge':
            item.charges_used -= 1
        if self.kwargs['mode'] == 'remove_charge':
            item.charges_used += 1
        item.save()
        if item.quantity <= 0:
            item.delete()

        return JsonResponse({'status': 'ok'})


class XhrPutIntoView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        item = CharacterItem.objects.get(id=kwargs['item_pk'])

        container = None
        if kwargs.get('container_pk', None) is not None:
            container = CharacterItem.objects.get(id=kwargs['container_pk'])

        if not item.item.is_container:
            item.in_container = container
            item.save()
        return JsonResponse({'status': 'ok'})


class XhrAddWeaponModView(TemplateView):
    template_name = 'characters/modals/add_weapon_mod.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        character_weapon = CharacterWeapon.objects.get(id=self.request.GET.get('character_weapon_id'))

        context = super(XhrAddWeaponModView, self).get_context_data(**kwargs)
        context['character'] = character
        context['character_weapon'] = character_weapon
        context['weapon_modification_types'] = WeaponModificationType.objects.for_extensions(
            character.extensions).filter(
            weaponmodification__in=WeaponModification.objects.for_extensions(
                character.extensions))
        return context


class AddWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        weapon_modification = WeaponModification.objects.get(id=kwargs['weapon_modification_pk'])
        character_weapon = CharacterWeapon.objects.get(id=kwargs['character_weapon_pk'])

        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        if character_weapon.weapon.type in weapon_modification.available_for_weapon_types.all():
            if weapon_modification.type.unique_equip:
                for active_weapon_mod in character_weapon.modifications.filter(type=weapon_modification.type):
                    character_weapon.modifications.remove(active_weapon_mod)
            character_weapon.modifications.add(weapon_modification)
        return JsonResponse({'status': 'ok'})


# Magic


class CharacterModifyArcanaView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        if character.may_edit(request.user):
            if self.kwargs['mode'] == 'restore':
                if character.arcana < character.max_arcana:
                    character.arcana += 1
            elif self.kwargs['mode'] == 'use':
                if character.arcana > 0:
                    character.arcana -= 1
            character.save()
        return JsonResponse({'status': 'ok'})


class CharacterCastSpellView(View):
    def post(self, request, *args, **kwargs):
        character_spell = CharacterSpell.objects.get(id=kwargs['pk'])
        character = character_spell.character
        if character.may_edit(request.user):
            if character_spell.arcana_cost <= character.arcana:
                character.arcana -= character_spell.arcana_cost
                character.save()
        return JsonResponse({'status': 'ok'})


class XhrAddSpellView(TemplateView):
    template_name = 'characters/modals/add_spell.html'

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context['character'] = character
        context['spell_types'] = SpellType.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        from magic.models import BaseSpell
        character = Character.objects.get(id=kwargs['pk'])
        operation = request.POST.get('operation', 'noop')
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        if operation == 'add-spell':
            spell = BaseSpell.objects.get(id=request.POST.get('spell_id'))
            if not spell.spell_point_cost <= character.spell_points_available:
                return JsonResponse({'status': 'notenoughpoints'})
            character.characterspell_set.create(spell=spell)
        return JsonResponse({'status': 'ok', 'remaining_spell_points': character.spell_points_available})


class XhrRemoveSpellView(View):
    def post(self, request, *args, **kwargs):
        character_spell = CharacterSpell.objects.get(id=kwargs['pk'])
        character = character_spell.character
        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})
        character_spell.delete()
        return JsonResponse({'status': 'ok'})


class XhrAddSpellTemplateView(TemplateView):
    template_name = 'characters/modals/add_spell_template.html'

    def get_context_data(self, **kwargs):
        character_spell = CharacterSpell.objects.get(id=kwargs['pk'])
        character = character_spell.character

        context = super().get_context_data(**kwargs)
        context['character'] = character
        context['character_spell'] = character_spell
        context['spell_template_categories'] = SpellTemplateCategory.objects.all()
        return context


class AddSpellTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])
        spell_template = SpellTemplate.objects.get(id=kwargs['spell_template_pk'])
        character_spell = CharacterSpell.objects.get(id=kwargs['character_spell_pk'])

        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        character_spell.characterspelltemplate_set.create(spell_template=spell_template)
        return JsonResponse({'status': 'ok'})


class XhrModifyCurrencyView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])

        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        for k, v in request.POST.items():
            unit_id = k.split('-')[-1]
            qs = character.charactercurrency_set.filter(currency_map_unit__id=unit_id)
            if qs.exists():
                qs.update(quantity=int(v))
            else:
                character.charactercurrency_set.create(
                    currency_map_unit=CurrencyMapUnit.objects.get(id=unit_id),
                    quantity=v)
        return JsonResponse({'status': 'ok'})


class XhrCreateNoteView(View):

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs['pk'])

        if not character.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        character.characternote_set.create(
            is_private=request.POST.get('private', 'off') == 'on',
            subject=request.POST.get('subject', None),
            text=request.POST.get('text', None)
        )

        return JsonResponse({'status': 'ok'})


class XhrUpdateNoteView(View):

    def post(self, request, *args, **kwargs):
        note = CharacterNote.objects.get(id=kwargs['note_pk'])

        if not note.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        note.is_private = request.POST.get('private', 'off') == 'on'
        note.subject = request.POST.get('subject', None)
        note.text = request.POST.get('text', None)
        note.save()
        return JsonResponse({'status': 'ok'})


class XhrDeleteNoteView(View):

    def post(self, request, *args, **kwargs):
        note = CharacterNote.objects.get(id=kwargs['note_pk'])

        if not note.may_edit(request.user):
            return JsonResponse({'status': 'forbidden'})

        note.delete()
        return JsonResponse({'status': 'ok'})
