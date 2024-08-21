import io
import os

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import mail_admins
from django.db.models import Q
from django.db.models.functions import Length
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView, DetailView, FormView
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from armory.models import (
    Weapon,
    RiotGear,
    ItemType,
    Item,
    WeaponModificationType,
    WeaponModification,
    WeaponType,
    WeaponAttackMode,
    CurrencyMapUnit,
    RiotGearType,
)
from campaigns.consumers import roll_and_send
from campaigns.models import Campaign
from characters.forms import (
    CharacterImageForm,
    CreateCharacterDataForm,
    CreateRandomNPCForm,
    CreateCharacterExtensionsForm,
)
from characters.models import (
    Character,
    CharacterWeapon,
    CharacterRiotGear,
    CharacterItem,
    CharacterStatusEffect,
    CharacterSpell,
    CharacterSkill,
    CharacterAttribute,
    CharacterNote,
)
from characters.utils import crit_successes
from horror.models import QuirkCategory, Quirk
from magic.models import (
    SpellType,
    SpellTemplateCategory,
    SpellTemplate,
    BaseSpell,
)
from pantheon.models import Entity, PriestAction
from rules.models import (
    Extension,
    Template,
    Lineage,
    StatusEffect,
    Skill,
    Attribute,
    Knowledge,
    TemplateCategory,
)
from worlds.models import WikiPage, World, WorldLeadImage


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_characters(self):
        context = {}
        characters = Character.objects.filter(image__isnull=False)

        lead_images = WorldLeadImage.objects.all()

        if self.request.world_configuration is not None:
            characters = characters.filter(
                extensions=self.request.world_configuration.world.extension
            )
            lead_images = lead_images.filter(
                world=self.request.world_configuration.world.extension
            )
        if self.request.user.is_authenticated:
            characters = characters.filter(created_by=self.request.user).order_by(
                "-modified_at"
            )
        else:
            characters = characters.filter(may_appear_on_start_page=True).order_by("?")

        context["characters"] = characters[:3]
        try:
            context["lead_image"] = lead_images.order_by("?").first()
        except WorldLeadImage.DoesNotExist:
            context["lead_image"] = None
        return context

    def get_context_campaigns(self):
        context = {}
        campaigns = Campaign.objects.filter(image__isnull=False)
        if self.request.world_configuration is not None:
            campaigns = campaigns.filter(
                world=self.request.world_configuration.world.extension
            )

        if self.request.user.is_authenticated:
            campaigns = campaigns.filter(created_by=self.request.user).order_by(
                "-created_at"
            )
        else:
            campaigns = campaigns.filter(may_appear_on_start_page=True).order_by("?")
        context["campaigns"] = campaigns[:3]
        return context

    def get_context_worlds(self):
        context = {}
        if not self.request.world_configuration:
            context["worlds"] = World.objects.filter(is_active=True)
        return context

    def get_context_wiki_pages(self):
        context = {}
        if self.request.world_configuration is not None:
            world = self.request.world_configuration.world
            context["wiki_pages"] = (
                WikiPage.objects.annotate(text_len=Length("text_de"))
                .filter(world=world, text_len__gte=30)
                .order_by("?")[:3]
            )
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_context_characters())
        context.update(self.get_context_worlds())
        context.update(self.get_context_campaigns())
        context.update(self.get_context_wiki_pages())

        if self.request.world_configuration:
            world = self.request.world_configuration.world
            context["world"] = world
            context["may_edit"] = world.may_edit(self.request.user)
        else:
            context["world"] = None
            context["may_edit"] = False

        return context


class CharacterDetailView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class XhrDeleteCharacterView(View):
    def post(self, request, *args, **kwargs):
        obj = Character.objects.get(id=kwargs["pk"])
        if obj.created_by == self.request.user:
            messages.info(request, _("Character deleted."))
            obj.delete()
        return JsonResponse(
            {
                "status": "ok",
                "url": "/",
            }
        )


class XhrSidebarView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["may_edit"] = self.object.may_edit(self.request.user)
        except AttributeError:
            context["may_edit"] = False
        return context

    def get_template_names(self):
        return ["characters/sidebar/" + self.kwargs["sidebar_template"] + ".html"]


class XhrCharacterSidebarView(XhrSidebarView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_effects"] = StatusEffect.objects.filter(
            is_active=True
        ).order_by("ordering")
        context["character_form"] = CharacterImageForm(instance=self.object)
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
        context["knowledge"] = Knowledge.objects.get(id=self.kwargs["knowledge_pk"])
        return context


class XhrCharacterPriestActionSidebarView(XhrSidebarView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["priest_action"] = PriestAction.objects.get(
            id=self.kwargs["priest_action_pk"]
        )
        return context


class XhrCharacterTemplateShadowSidebarView(XhrSidebarView):
    model = Template


class XhrDetailFragmentView(DetailView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fragment_template"] = self.kwargs["fragment_template"]
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context

    def get_template_names(self):
        return ["characters/fragments/" + self.kwargs["fragment_template"] + ".html"]


class XhrCharacterRestView(TemplateView):
    template_name = "characters/modals/rest.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["object"] = character
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        minimum_roll = character.minimum_roll + character.get_aspect_modifier(
            "base_rest_minimum_roll"
        )
        mode = request.POST.get("mode", "manual")

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        if mode == "auto":
            character.bonus_dice_used = 0
            character.destiny_dice_used = 0
            character.rerolls_used = 0

            rest_wound_roll = roll_and_send(
                character.id,
                f"{character.rest_wound_dice}d6",
                gettext("Rest"),
                gettext("Wound Roll"),
                minimum_roll=minimum_roll,
            )

            for d in filter(lambda x: x >= minimum_roll, rest_wound_roll):
                for n in range(crit_successes(d) + 1):
                    if character.health < character.max_health:
                        character.health += 1

            character.boost = 0

            if "magic" in character.extension_enabled:
                rest_arcana_roll = roll_and_send(
                    character.id,
                    f"{character.rest_arcana_dice}d6",
                    gettext("Rest"),
                    gettext("Arcana Roll"),
                    minimum_roll=minimum_roll,
                )

                for d in filter(lambda x: x >= minimum_roll, rest_arcana_roll):
                    for n in range(crit_successes(d) + 1):
                        if character.arcana < character.max_arcana:
                            character.arcana += 1

            if "horror" in character.extension_enabled:
                rest_stress_roll = roll_and_send(
                    character.id,
                    f"{character.rest_stress_dice}d6",
                    gettext("Rest"),
                    gettext("Stress Roll"),
                    minimum_roll=minimum_roll,
                )

                if len(list(filter(lambda x: x >= minimum_roll, rest_stress_roll))):
                    if character.stress > 0:
                        character.stress -= 1

            character.save()

        return JsonResponse({"status": "ok"})


class XhrCharacterStatusEffectsChangeView(View):
    template_name = "characters/_status_effects.html"

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        status_effect = StatusEffect.objects.get(id=kwargs["status_effect_pk"])

        if character.may_edit(request.user):
            obj, created = CharacterStatusEffect.objects.get_or_create(
                character=character, status_effect=status_effect
            )

            if kwargs["mode"] == "decrease":
                if obj.base_value > 0:
                    obj.base_value -= 1
                    obj.save()
                if obj.base_value <= 0:
                    obj.delete()
            if kwargs["mode"] == "increase":
                obj.base_value += 1
                obj.save()

            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "forbidden", "value": 0})


class CharacterModifyStressView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if character.may_edit(request.user):
            if self.kwargs["mode"] == "gain":
                character.stress += 1
                if character.stress >= character.max_stress:
                    character.quirks_gained += 1
                    character.stress = 0
            elif self.kwargs["mode"] == "remove":
                if character.stress > 0:
                    character.stress -= 1
            character.save()
        return JsonResponse({"status": "ok"})


class XhrAddQuirkView(TemplateView):
    template_name = "characters/modals/add_quirk.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["quirk_categories"] = QuirkCategory.objects.all()
        return context


class AddQuirkView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        quirk = Quirk.objects.get(id=kwargs["quirk_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        character.quirks.add(quirk)
        return JsonResponse({"status": "ok"})


class XhrRemoveQuirkView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        quirk = Quirk.objects.get(id=kwargs["quirk_pk"])

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        character.quirks.remove(quirk)
        character.quirks_healed += 1
        character.save()

        return JsonResponse({"status": "ok"})


class CharacterAttackView(View):
    def post(self, request, *args, **kwargs):
        character_weapon = CharacterWeapon.objects.get(id=kwargs["characterweapon_pk"])
        weapon_attack_mode = WeaponAttackMode.objects.get(
            id=kwargs["weapon_attackmode_pk"]
        )

        if not character_weapon.character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        character_weapon.capacity_used += weapon_attack_mode.capacity_consumed
        character_weapon.save()

        return JsonResponse({"status": "ok"})


class CharacterReloadView(View):
    def post(self, request, *args, **kwargs):
        character_weapon = CharacterWeapon.objects.get(id=kwargs["characterweapon_pk"])

        if not character_weapon.character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        character_weapon.capacity_used = 0
        character_weapon.save()

        return JsonResponse({"status": "ok"})


class CharacterModifyDiceView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if character.may_edit(request.user):
            if self.kwargs["mode"] == "add_bonus":
                character.bonus_dice_used -= 1
            elif self.kwargs["mode"] == "remove_bonus":
                character.bonus_dice_used += 1
            if self.kwargs["mode"] == "add_destiny":
                character.destiny_dice_used -= 1
            elif self.kwargs["mode"] == "remove_destiny":
                character.destiny_dice_used += 1
            if self.kwargs["mode"] == "add_reroll":
                character.rerolls_used -= 1
            elif self.kwargs["mode"] == "remove_reroll":
                character.rerolls_used += 1
            character.save()
        return JsonResponse({"status": "ok"})


class CharacterModifyHealthView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if character.may_edit(request.user):
            if self.kwargs["mode"] == "heal":
                if character.health < character.max_health:
                    character.health += 1
            elif self.kwargs["mode"] == "wound":
                if character.boost > 0:
                    character.boost -= 1
                elif character.health > 0:
                    character.health -= 1
            elif self.kwargs["mode"] == "boost":
                character.boost += 1
            character.save()
        return JsonResponse({"status": "ok"})


class CreateCharacterView(TemplateView):
    template_name = "characters/create_character.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extensions"] = (
            Extension.objects.exclude(is_mandatory=True)
            .exclude(type__in=["e", "x"])
            .exclude(is_active=False)
        )
        return context


class CreateCharacterEpochView(TemplateView):
    template_name = "characters/create_character_epoch.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["world_pk"] = self.kwargs["world_pk"]
        context["extensions"] = (
            Extension.objects.exclude(is_mandatory=True)
            .exclude(type__in=["x", "w"])
            .exclude(is_active=False)
        )
        return context


class CreateCharacterExtensionsView(FormView):
    template_name = "characters/create_character_extensions.html"
    form_class = CreateCharacterExtensionsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["world_pk"] = self.kwargs["world_pk"]
        context["epoch_pk"] = self.kwargs["epoch_pk"]
        context["extensions"] = (
            Extension.objects.exclude(is_mandatory=True)
            .exclude(type__in=["e", "w"])
            .exclude(is_active=False)
        )
        return context


class CreateCharacterDataView(FormView):
    form_class = CreateCharacterDataForm
    template_name = "characters/character_form.html"

    @property
    def campaign_to_join(self):
        campaign_pk = self.kwargs.get("campaign_pk", None)
        if campaign_pk is not None:
            campaign = Campaign.objects.get(id=campaign_pk)
            if campaign.campaign_hash == self.kwargs.get("hash", ""):
                return campaign
        return None

    @property
    def lineages(self):
        return Lineage.objects.filter(
            Q(extensions__id=self.kwargs["epoch_pk"])
            | Q(extensions__id=self.kwargs["world_pk"])
            | Q(
                extensions__id__in=Extension.objects.filter(
                    Q(is_mandatory=True)
                    | Q(id__in=self.request.GET.getlist("extensions"))
                )
            )
        )

    @property
    def entities(self):
        return Entity.objects.filter(
            Q(extensions__id=self.kwargs["epoch_pk"])
            | Q(extensions__id=self.kwargs["world_pk"])
            | Q(
                extensions__id__in=Extension.objects.filter(
                    Q(is_mandatory=True)
                    | Q(id__in=self.request.GET.getlist("extensions"))
                )
            )
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["lineage"].queryset = self.lineages
        form.fields["entity"].queryset = self.entities

        world = Extension.objects.get(id=self.kwargs["world_pk"])
        if world.currency_map is not None:
            form.fields["currency_map"].widget = forms.HiddenInput()
        if self.campaign_to_join:
            form.fields["currency_map"].widget = forms.HiddenInput()
            form.fields["seed_money"].widget = forms.HiddenInput()
        qs = Extension.objects.filter(
            id__in=self.request.GET.getlist("extensions"), identifier="pantheon"
        )
        if (
            not qs.exists()
            and not world.fixed_extensions.filter(identifier="pantheon").exists()
        ):
            form.fields["entity"].widget = forms.HiddenInput()
            form.fields["attitude"].widget = forms.HiddenInput()

        return form

    def form_valid(self, form):
        self.object = Character.objects.create(
            name=form.cleaned_data["name"],
            currency_map=form.cleaned_data["currency_map"],
            lineage=form.cleaned_data["lineage"],
            size=form.cleaned_data["size"],
            weight=form.cleaned_data["weight"],
            entity=form.cleaned_data["entity"],
            attitude=form.cleaned_data["attitude"],
        )
        self.object.extensions.add(form.cleaned_data["epoch"])
        self.object.extensions.add(form.cleaned_data["world"])

        self.object.charactercurrency_set.create(
            currency_map_unit=CurrencyMapUnit.objects.get(
                currency_map=form.cleaned_data["currency_map"], is_common=True
            ),
            quantity=form.cleaned_data["seed_money"],
        )

        for e in form.cleaned_data["extensions"]:
            self.object.extensions.add(e)
        for skill in Skill.objects.all():
            self.object.characterskill_set.create(skill=skill)
        for attribute in Attribute.objects.all():
            self.object.characterattribute_set.create(attribute=attribute)

        if self.object.lineage.template is not None:
            self.object.add_template(self.object.lineage.template)

        if self.campaign_to_join is not None:
            for ext in self.campaign_to_join.extensions.all():
                self.object.extensions.add(ext)
            if self.kwargs.get("type", "pc") == "pc":
                self.object.campaign = self.campaign_to_join
            else:
                self.object.npc_campaign = self.campaign_to_join

        self.object.created_by = (
            self.request.user if self.request.user.is_authenticated else None
        )
        self.object.save()

        return super().form_valid(form)

    def get_initial(self):
        world = Extension.objects.get(id=self.kwargs["world_pk"])

        extensions = Extension.objects.filter(
            id__in=self.request.GET.getlist("extensions")
        )
        if world.fixed_extensions.exists():
            extensions = world.fixed_extensions.all()

        initial = {
            "epoch": self.kwargs["epoch_pk"],
            "world": self.kwargs["world_pk"],
            "lineage": self.lineages.earliest("id"),
            "extensions": extensions,
        }

        if world.currency_map is not None:
            initial["currency_map"] = world.currency_map

        # Campaign overrides world currency map and seed money
        if self.campaign_to_join is not None:
            initial["seed_money"] = self.campaign_to_join.seed_money
            initial["currency_map"] = self.campaign_to_join.currency_map
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extensions"] = Extension.objects.filter(
            type__in=["x", "w"], is_mandatory=False, is_active=True
        )
        context["campaign"] = self.campaign_to_join
        context["world_pk"] = self.kwargs["world_pk"]
        context["epoch_pk"] = self.kwargs["epoch_pk"]
        return context

    def get_success_url(self):
        return reverse(
            "characters:create_character_constructed", kwargs={"pk": self.object.id}
        )


class CreateCharacterInfoView(TemplateView):
    template_name = "characters/_create_character_info.html"

    def get_context_data(self, **kwargs):
        field = self.request.GET.get("field")
        value = self.request.GET.get("value")
        try:
            return getattr(self, f"{field}_info")(value)
        except AttributeError:
            return {}

    def entity_info(self, value):
        try:
            entity = Entity.objects.get(id=value)
        except ValueError:
            return {}
        return {
            "title": entity.name,
            "description": entity.description,
            "image": entity.image,
        }

    def name_info(self, value):
        return {
            "title": gettext("Name"),
            "description": gettext("Choose a suitable name for your character."),
        }

    def size_info(self, value):
        world = Extension.objects.get(id=self.kwargs["world_pk"]).world_set.latest("id")
        return {
            "title": gettext("Size"),
            "description": gettext(
                f"Enter the size of your character in {world.info_name_cm}."
            ),
        }

    def weight_info(self, value):
        world = Extension.objects.get(id=self.kwargs["world_pk"]).world_set.latest("id")
        return {
            "title": gettext("Weight"),
            "description": gettext(
                f"Enter the weight of your character in {world.info_name_kg}."
            ),
        }

    def date_of_birth_info(self, value):
        return {
            "title": gettext("Date of birth"),
            "description": gettext("Enter the birthdate of your character."),
        }

    def seed_money_info(self, value):
        return {
            "title": gettext("Seed Money"),
            "description": gettext(
                """Specify a starting capital for your character. The seed money is usually
            defined by the game master and determines how much equipment the character can have at the
            beginning of the game."""
            ),
        }

    def lineage_info(self, value):
        lineage = Lineage.objects.get(id=value)
        return {
            "title": lineage.name,
            "description": lineage.description,
            "lineage": lineage,
        }

    def attitude_info(self, value):
        return {
            "title": gettext("Attitude"),
            "description": gettext(
                """The attitude indicates the morality of the character. The value ranges
            from 0 to 100, with an attitude of 0 corresponding to a deeply evil character and a value of 100
            corresponding to a good character. The value is freely selectable and can be changed by actions in the game.
            """
            ),
        }

    def currency_map_info(self, value):
        return {
            "title": gettext("Currency Map"),
            "description": gettext(
                """The currency map specifies which currency units are available to the character.
            It is usually set by the campaign or the world."""
            ),
        }


class CreateRandomNPCView(CreateCharacterDataView):
    form_class = CreateRandomNPCForm
    template_name = "characters/random_npc_form.html"

    def form_valid(self, form):
        result = super().form_valid(form)
        self.object.randomize(form.cleaned_data["starting_reputation"])
        self.object.set_initial_reputation(
            self.object.reputation_spent + self.object.remaining_template_points
        )
        return result

    def get_success_url(self):
        return reverse("campaigns:detail", kwargs={"pk": self.campaign_to_join.id})


class XhrCreateCharacterPreviewView(DetailView):
    model = Character
    template_name = "characters/fragments/character.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"fragment_template": "character", "model_name": "Character"})
        return context


class CreateCharacterConstructedView(DetailView):
    template_name = "characters/create_character_constructed.html"
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_categories"] = TemplateCategory.objects.filter(
            allow_at_character_creation=True
        )
        context["warnings"] = self.object.warnings(self.request.world_configuration)
        context["character_template_ids"] = [
            ct.template.id for ct in self.object.charactertemplate_set.all()
        ]
        return context

    def post(self, request, *args, **kwargs):
        obj = Character.objects.get(id=kwargs["pk"])
        obj.set_initial_reputation(obj.reputation_spent + obj.remaining_template_points)
        obj.health = obj.max_health
        obj.arcana = obj.max_arcana
        obj.save()
        mail_admins(
            "PhaseSix: New Character",
            render_to_string(
                "characters/mail/character_created_admin_notification.html",
                {"character": obj, "base_url": settings.BASE_URL},
            ),
        )
        return HttpResponseRedirect(obj.get_absolute_url())


class XhrConstructedAddTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])

        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get("template_id"))
            remaining_points = character.remaining_template_points
            if template.cost > remaining_points:
                return JsonResponse({"status": "notenoughpoints"})
            character.add_template(template)
            return JsonResponse(
                {
                    "status": "ok",
                    "warnings": character.warnings(self.request.world_configuration),
                    "remaining_points": remaining_points - template.cost,
                }
            )

        return JsonResponse({"status": "noop"})


class XhrConstructedRemoveTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])

        if character.may_edit(request.user):
            template = Template.objects.get(id=request.POST.get("template_id"))
            character.remove_template(template)
            return JsonResponse(
                {
                    "status": "ok",
                    "warnings": character.warnings(self.request.world_configuration),
                    "remaining_points": character.remaining_template_points,
                }
            )

        return JsonResponse({"status": "noop"})


class ChangeImageView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
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
    template_name = "characters/modals/reputation.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["object"] = character
        context["template_categories"] = TemplateCategory.objects.filter(
            allow_for_reputation=True
        )
        context["character_template_ids"] = [
            ct.template.id for ct in character.charactertemplate_set.all()
        ]
        return context

    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        operation = request.POST.get("operation", "noop")
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        if operation == "add":
            try:
                character.reputation += int(request.POST.get("reputation", 0))
                character.save()
            except ValueError:
                pass
        if operation == "add-template":
            template = Template.objects.get(id=request.POST.get("template_id"))
            if not template.cost <= character.reputation_available:
                return JsonResponse({"status": "notenoughpoints"})
            character.add_template(template)
        return JsonResponse(
            {"status": "ok", "remaining_reputation": character.reputation_available}
        )


# gear


class XhrAddWeaponsView(TemplateView):
    template_name = "characters/modals/add_weapons.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["weapon_types"] = WeaponType.objects.for_extensions(
            character.extensions
        )
        context["homebrew"] = Weapon.objects.homebrew(
            character=character, campaign=character.campaign
        )
        return context


class AddWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        weapon = Weapon.objects.get(id=kwargs["weapon_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        character.characterweapon_set.create(weapon=weapon)
        return JsonResponse({"status": "ok"})


class XhrRemoveWeaponView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        weapon = CharacterWeapon.objects.get(id=kwargs["weapon_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        weapon.delete()
        return JsonResponse({"status": "ok"})


class XhrRemoveWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        weapon = CharacterWeapon.objects.get(id=kwargs["weapon_pk"])
        weapon_mod = WeaponModification.objects.get(id=kwargs["weapon_modification_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        weapon.modifications.remove(weapon_mod)
        return JsonResponse({"status": "ok"})


class XhrWeaponConditionView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        weapon = CharacterWeapon.objects.get(id=kwargs["weapon_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        if kwargs["mode"] == "damage":
            weapon.condition -= 10
        else:
            weapon.condition += 10

        weapon.save()
        return JsonResponse({"status": "ok"})


class XhrAddRiotGearView(TemplateView):
    template_name = "characters/modals/add_riot_gear.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["riot_gear_types"] = RiotGearType.objects.for_extensions(
            character.extensions
        )
        context["homebrew"] = RiotGear.objects.homebrew(
            character=character, campaign=character.campaign
        )
        return context


class AddRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        riot_gear = RiotGear.objects.get(id=kwargs["riot_gear_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        character.characterriotgear_set.create(riot_gear=riot_gear)
        return JsonResponse({"status": "ok"})


class XhrRemoveRiotGearView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        riot_gear = CharacterRiotGear.objects.get(id=kwargs["riot_gear_pk"])
        riot_gear.delete()
        return JsonResponse({"status": "ok"})


class XhrRiotGearConditionView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        riot_gear = CharacterRiotGear.objects.get(id=kwargs["riot_gear_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        if kwargs["mode"] == "damage":
            riot_gear.condition -= 10
        else:
            riot_gear.condition += 10

        riot_gear.save()
        return JsonResponse({"status": "ok"})


class XhrAddItemsView(TemplateView):
    template_name = "characters/modals/add_items.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["item_types"] = ItemType.objects.for_extensions(character.extensions)
        context["homebrew"] = Item.objects.homebrew(
            character=character, campaign=character.campaign
        )
        return context


class AddItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        item = Item.objects.get(id=kwargs["item_pk"])

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        # Containers don't stack
        if (
            character.characteritem_set.filter(item=item).exists()
            and not item.is_container
        ):
            ci = character.characteritem_set.filter(item=item).latest("id")
            ci.quantity += 1
            ci.save()
        else:
            character.characteritem_set.create(item=item)
        return JsonResponse({"status": "ok"})


class XhrUpdateItemSortOrderView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        for pk, order in request.POST.items():
            character.characteritem_set.filter(id=pk).update(ordering=order)

        return JsonResponse({"status": "ok"})


class XhrTurnItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        item = CharacterItem.objects.get(id=kwargs["item_pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        if kwargs["mode"] == "damage":
            item.condition -= 10
        else:
            item.condition += 10

        item.save()
        return JsonResponse({"status": "ok"})


class XhrModifyItemView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        item = CharacterItem.objects.get(id=kwargs["item_pk"])

        if self.kwargs["mode"] == "add":
            item.quantity += 1
        if self.kwargs["mode"] == "remove":
            if item.quantity > 0:
                item.quantity -= 1
        if self.kwargs["mode"] == "add_charge":
            item.charges_used -= 1
        if self.kwargs["mode"] == "remove_charge":
            item.charges_used += 1
        item.save()
        if item.quantity <= 0:
            item.delete()

        return JsonResponse({"status": "ok"})


class XhrPutIntoView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        item = CharacterItem.objects.get(id=kwargs["item_pk"])

        container = None
        if kwargs.get("container_pk", None) is not None:
            container = CharacterItem.objects.get(id=kwargs["container_pk"])

        if not item.item.is_container:
            item.in_container = container
            item.save()
        return JsonResponse({"status": "ok"})


class XhrAddWeaponModView(TemplateView):
    template_name = "characters/modals/add_weapon_mod.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        character_weapon = CharacterWeapon.objects.get(
            id=self.request.GET.get("character_weapon_id")
        )

        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["character_weapon"] = character_weapon
        context[
            "weapon_modification_types"
        ] = WeaponModificationType.objects.for_extensions(character.extensions).filter(
            weaponmodification__in=WeaponModification.objects.for_extensions(
                character.extensions
            )
        )
        return context


class AddWeaponModificationView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        weapon_modification = WeaponModification.objects.get(
            id=kwargs["weapon_modification_pk"]
        )
        character_weapon = CharacterWeapon.objects.get(id=kwargs["character_weapon_pk"])

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        if (
            character_weapon.weapon.type
            in weapon_modification.available_for_weapon_types.all()
        ):
            if weapon_modification.type.unique_equip:
                for active_weapon_mod in character_weapon.modifications.filter(
                    type=weapon_modification.type
                ):
                    character_weapon.modifications.remove(active_weapon_mod)
            character_weapon.modifications.add(weapon_modification)
        return JsonResponse({"status": "ok"})


# Magic


class CharacterModifyArcanaView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if character.may_edit(request.user):
            if self.kwargs["mode"] == "restore":
                if character.arcana < character.max_arcana:
                    character.arcana += 1
            elif self.kwargs["mode"] == "use":
                if character.arcana > 0:
                    character.arcana -= 1
            character.save()
        return JsonResponse({"status": "ok"})


class CharacterCastSpellView(View):
    def post(self, request, *args, **kwargs):
        character_spell = CharacterSpell.objects.get(id=kwargs["pk"])
        character = character_spell.character
        if character.may_edit(request.user):
            if character_spell.arcana_cost <= character.arcana:
                character.arcana -= character_spell.arcana_cost
                character.save()
        return JsonResponse({"status": "ok"})


class XhrAddSpellView(TemplateView):
    template_name = "characters/modals/add_spell.html"

    def get_context_data(self, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["categories"] = SpellType.objects.all()
        context["homebrew"] = BaseSpell.objects.homebrew(
            character=character, campaign=character.campaign
        )
        return context

    def post(self, request, *args, **kwargs):
        from magic.models import BaseSpell

        character = Character.objects.get(id=kwargs["pk"])
        operation = request.POST.get("operation", "noop")
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        if operation == "add-spell":
            spell = BaseSpell.objects.get(id=request.POST.get("spell_id"))
            if not spell.spell_point_cost <= character.spell_points_available:
                return JsonResponse({"status": "notenoughpoints"})
            character.characterspell_set.create(spell=spell)
        return JsonResponse(
            {"status": "ok", "remaining_spell_points": character.spell_points_available}
        )


class XhrAddSpellByOriginView(XhrAddSpellView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = context["character"].unlocked_spell_origins
        return context


class XhrRemoveSpellView(View):
    def post(self, request, *args, **kwargs):
        character_spell = CharacterSpell.objects.get(id=kwargs["pk"])
        character = character_spell.character
        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})
        character_spell.delete()
        return JsonResponse({"status": "ok"})


class XhrAddSpellTemplateView(TemplateView):
    template_name = "characters/modals/add_spell_template.html"

    def get_context_data(self, **kwargs):
        character_spell = CharacterSpell.objects.get(id=kwargs["pk"])
        character = character_spell.character

        context = super().get_context_data(**kwargs)
        context["character"] = character
        context["character_spell"] = character_spell
        context["spell_template_categories"] = SpellTemplateCategory.objects.all()
        return context


class AddSpellTemplateView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        spell_template = SpellTemplate.objects.get(id=kwargs["spell_template_pk"])
        character_spell = CharacterSpell.objects.get(id=kwargs["character_spell_pk"])

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        character_spell.characterspelltemplate_set.create(spell_template=spell_template)
        return JsonResponse({"status": "ok"})


class XhrModifyCurrencyView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        for k, v in request.POST.items():
            unit_id = k.split("-")[-1]
            qs = character.charactercurrency_set.filter(currency_map_unit__id=unit_id)
            if qs.exists():
                qs.update(quantity=int(v))
            else:
                character.charactercurrency_set.create(
                    currency_map_unit=CurrencyMapUnit.objects.get(id=unit_id),
                    quantity=v,
                )
        return JsonResponse({"status": "ok"})


class XhrCreateNoteView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])

        if not character.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        character.characternote_set.create(
            is_private=request.POST.get("private", "off") == "on",
            subject=request.POST.get("subject", None),
            text=request.POST.get("text", None),
        )

        return JsonResponse({"status": "ok"})


class XhrUpdateNoteView(View):
    def post(self, request, *args, **kwargs):
        note = CharacterNote.objects.get(id=kwargs["note_pk"])

        if not note.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        note.is_private = request.POST.get("private", "off") == "on"
        note.subject = request.POST.get("subject", None)
        note.text = request.POST.get("text", None)
        note.save()
        return JsonResponse({"status": "ok"})


class XhrDeleteNoteView(View):
    def post(self, request, *args, **kwargs):
        note = CharacterNote.objects.get(id=kwargs["note_pk"])

        if not note.may_edit(request.user):
            return JsonResponse({"status": "forbidden"})

        note.delete()
        return JsonResponse({"status": "ok"})


class CharacterPDFView(View):
    def get(self, request, *args, **kwargs):
        font_config = FontConfiguration()
        html = HTML(
            file_obj=io.BytesIO(
                bytes(
                    render_to_string(
                        "characters/pdf/character_pdf.html",
                        {
                            "object": Character.objects.get(id=kwargs["pk"]),
                            "data_path": os.path.join(
                                settings.BASE_DIR, "characters/templates/characters/pdf"
                            ),
                        },
                    ),
                    encoding="utf-8",
                )
            ),
            base_url="src/",
            encoding="utf-8",
        )
        response = HttpResponse(content_type="application/pdf")
        response.headers["Content-Disposition"] = "inline"
        html.write_pdf(response, font_config=font_config)
        return response


# Pantheon


class CharacterModifyGraceView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if character.may_edit(request.user):
            if self.kwargs["mode"] == "restore":
                character.grace += 1
            elif self.kwargs["mode"] == "use":
                character.grace -= 1
            character.save()
        return JsonResponse({"status": "ok"})


class CharacterModifyAttitudeView(View):
    def post(self, request, *args, **kwargs):
        character = Character.objects.get(id=kwargs["pk"])
        if character.may_edit(request.user):
            if self.kwargs["mode"] == "restore":
                character.attitude += 5
            elif self.kwargs["mode"] == "use":
                character.attitude -= 5
            character.save()
        return JsonResponse({"status": "ok"})
