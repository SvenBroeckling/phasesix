from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from armory.models import Item, RiotGear, Weapon, AttackMode
from campaigns.models import Campaign
from characters.models import Character
from gmtools.utils import get_homebrew_models
from homebrew.forms import (
    CreateItemForm,
    CreateRiotGearForm,
    CreateWeaponForm,
    CreateBaseSpellForm,
)
from magic.models import BaseSpell


class IndexView(TemplateView):
    template_name = "homebrew/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["homebrew_querysets"] = [
            model.objects.filter(is_homebrew=True, keep_as_homebrew=False)
            for model in get_homebrew_models()
        ]
        return context


class XhrCreateBaseView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get("character_pk", None) is not None:
            context["character"] = Character.objects.get(
                id=self.request.GET.get("character_pk")
            )
        if self.request.GET.get("campaign_pk", None) is not None:
            context["campaign"] = Campaign.objects.get(
                id=self.request.GET.get("campaign_pk")
            )
        return context


class XhrCreateItemView(XhrCreateBaseView):
    template_name = "homebrew/modals/create_item.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CreateItemForm(
            initial={"weight": 1, "price": 10, "concealment": 0}
        )
        return context


class CreateBaseView(View):
    def get_character(self):
        if self.request.GET.get("character_pk", "") != "":
            return Character.objects.get(id=self.request.GET.get("character_pk"))
        return None

    def get_campaign(self):
        if self.request.GET.get("campaign_pk", "") != "":
            return Campaign.objects.get(id=self.request.GET.get("campaign_pk"))
        character = self.get_character()
        if character is not None:
            return character.pc_or_npc_campaign
        return None

    @staticmethod
    def may_edit(character, campaign, user):
        if character is not None and character.may_edit(user):
            return True
        if campaign is not None and campaign.may_edit(user):
            return True
        return False


class CreateItemView(CreateBaseView):
    def post(self, request, *args, **kwargs):
        character = self.get_character()
        campaign = self.get_campaign()
        if self.may_edit(character, campaign, request.user):
            form = CreateItemForm(request.POST)
            if form.is_valid():
                item = Item.objects.create(
                    name_de=form.cleaned_data["name"],
                    description_de=form.cleaned_data["description"],
                    type=form.cleaned_data["type"],
                    weight=form.cleaned_data["weight"],
                    price=form.cleaned_data["price"],
                    concealment=form.cleaned_data["concealment"],
                    charges=form.cleaned_data["charges"],
                    is_container=form.cleaned_data["is_container"],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_character=character,
                    homebrew_campaign=campaign,
                )
                if character is not None and form["add_to_character"]:
                    character.characteritem_set.create(item=item)

        return JsonResponse({"status": "ok"})


class XhrCreateRiotGearView(XhrCreateBaseView):
    template_name = "homebrew/modals/create_riot_gear.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CreateRiotGearForm(
            initial={
                "weight": 1,
                "type": 1,
                "protection": 1,
                "encumbrance": 1,
                "price": 10,
                "concealment": 0,
            }
        )
        return context


class CreateRiotGearView(CreateBaseView):
    def post(self, request, *args, **kwargs):
        character = self.get_character()
        campaign = self.get_campaign()
        if self.may_edit(character, campaign, request.user):
            form = CreateRiotGearForm(request.POST)
            if form.is_valid():
                riot_gear = RiotGear.objects.create(
                    type=form.cleaned_data["type"],
                    name_de=form.cleaned_data["name"],
                    description_de=form.cleaned_data["description"],
                    protection_ballistic=form.cleaned_data["protection"],
                    encumbrance=form.cleaned_data["encumbrance"],
                    weight=form.cleaned_data["weight"],
                    price=form.cleaned_data["price"],
                    concealment=form.cleaned_data["concealment"],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_character=character,
                    homebrew_campaign=campaign,
                )
                if character is not None and form["add_to_character"]:
                    character.characterriotgear_set.create(riot_gear=riot_gear)

        return JsonResponse({"status": "ok"})


class XhrCreateWeaponView(XhrCreateBaseView):
    template_name = "homebrew/modals/create_weapon.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CreateWeaponForm(
            initial={
                "damage_potential": 0,
                "actions_to_ready": 1,
                "piercing": 1,
                "range_meter": 20,
                "capacity": 1,
                "weight": 1,
                "price": 10,
                "concealment": 0,
            }
        )
        return context


class CreateWeaponView(CreateBaseView):
    def post(self, request, *args, **kwargs):
        character = self.get_character()
        campaign = self.get_campaign()
        if self.may_edit(character, campaign, request.user):
            form = CreateWeaponForm(request.POST)
            if form.is_valid():
                weapon = Weapon.objects.create(
                    name_de=form.cleaned_data["name"],
                    description_de=form.cleaned_data["description"],
                    type=form.cleaned_data["type"],
                    is_hand_to_hand_weapon=form.cleaned_data["is_hand_to_hand_weapon"],
                    is_throwing_weapon=form.cleaned_data["is_throwing_weapon"],
                    damage_potential=form.cleaned_data["damage_potential"],
                    capacity=form.cleaned_data["capacity"],
                    actions_to_ready=form.cleaned_data["actions_to_ready"],
                    piercing=form.cleaned_data["piercing"],
                    concealment=form.cleaned_data["concealment"],
                    weight=form.cleaned_data["weight"],
                    price=form.cleaned_data["price"],
                    range_meter=form.cleaned_data["range_meter"],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_character=character,
                    homebrew_campaign=campaign,
                )
                if weapon.is_hand_to_hand_weapon:
                    weapon.attack_modes.add(
                        AttackMode.objects.get(name_en="Hand to Hand")
                    )
                elif weapon.is_throwing_weapon:
                    weapon.attack_modes.add(AttackMode.objects.get(name_en="Throwing"))
                else:
                    weapon.attack_modes.add(
                        AttackMode.objects.get(name_en="Burst mode")
                    )
                    weapon.attack_modes.add(
                        AttackMode.objects.get(name_en="Single shot")
                    )

                if character is not None and form["add_to_character"]:
                    character.characterweapon_set.create(weapon=weapon)
            else:
                print(form.errors)

        return JsonResponse({"status": "ok"})


class XhrCreateBaseSpellView(XhrCreateBaseView):
    template_name = "homebrew/modals/create_base_spell.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CreateBaseSpellForm(
            initial={
                "rules": _("Spell Rules"),
                "spell_point_cost": 5,
                "arcana_cost": 1,
                "power": 1,
                "range": 10,
                "actions": 1,
            }
        )
        return context


class CreateBaseSpellView(CreateBaseView):
    def post(self, request, *args, **kwargs):
        character = self.get_character()
        campaign = self.get_campaign()
        if self.may_edit(character, campaign, request.user):
            form = CreateBaseSpellForm(request.POST)
            if form.is_valid():
                base_spell = BaseSpell.objects.create(
                    name_de=form.cleaned_data["name"],
                    rules_de=form.cleaned_data["rules"],
                    spell_point_cost=form.cleaned_data["spell_point_cost"],
                    arcana_cost=form.cleaned_data["arcana_cost"],
                    power=form.cleaned_data["power"],
                    range=form.cleaned_data["range"],
                    actions=form.cleaned_data["actions"],
                    origin=form.cleaned_data["origin"],
                    type=form.cleaned_data["type"],
                    variant=form.cleaned_data["variant"],
                    shape=form.cleaned_data["shape"],
                    is_ritual=form.cleaned_data["is_ritual"],
                    created_by=request.user,
                    is_homebrew=True,
                    homebrew_character=character,
                    homebrew_campaign=campaign,
                )
                if character is not None and form["add_to_character"]:
                    character.characterspell_set.create(spell=base_spell)
            else:
                print(form.errors)

        return JsonResponse({"status": "ok"})
