from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, FormView, TemplateView, UpdateView
from formtools.wizard.views import SessionWizardView

from campaigns.models import Campaign
from plots.models import Plot
from armory.models import Item, RiotGear, Weapon
from magic.models import BaseSpell, SpellOrigin
from rules.models import Extension, Lineage, Template
from .forms import (
    AttributesForm,
    AjaxSearchSelectMultiple,
    ConceptForm,
    EquipmentForm,
    EssentialCharacterForm,
    EssentialCustomMarkForm,
    EssentialAddSkillForm,
    EssentialCustomEquipmentForm,
    EssentialAttributesEditForm,
    EssentialEquipmentEditForm,
    EssentialCharacterImageForm,
    EssentialIdentityEditForm,
    EssentialMarksEditForm,
    EssentialNotesEditForm,
    EssentialSkillsEditForm,
    EssentialSupernaturalEditForm,
    MarksForm,
    SkillsForm,
    SupernaturalForm,
    essential_item_queryset,
    essential_equipment_queryset,
    essential_mark_queryset,
)
from .models import (
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
)
from .rules import ATTRIBUTES, magic_slots
from .openai import translate_custom_mark

WIZARD_FORMS = (
    ("concept", ConceptForm),
    ("attributes", AttributesForm),
    ("marks", MarksForm),
    ("skills", SkillsForm),
    ("equipment", EquipmentForm),
    ("supernatural", SupernaturalForm),
)
WIZARD_STEP_LABELS = {
    "concept": _("Concept"),
    "attributes": _("Attributes"),
    "marks": _("Marks"),
    "skills": _("Skills"),
    "equipment": _("Equipment"),
    "supernatural": _("Supernatural access"),
}
WIZARD_STEP_DESCRIPTIONS = {
    "concept": _(
        "Give your character a name, concept, oath or debt, birth date, and century."
    ),
    "attributes": _("Choose one attribute at 3, two at 2, three at 1, and two at 0."),
    "marks": _("Choose ancestry, path, and bond."),
    "skills": _("Choose one skill at rank 3, three at rank 2, and five at rank 1."),
    "equipment": _("Choose equipment enabled for Tirakan Essential."),
    "supernatural": _("Choose the supernatural access granted by Gift."),
}


class MarkSummaryView(LoginRequiredMixin, TemplateView):
    template_name = "essential_characters/_mark_summary.html"
    mark_models = {
        "ancestry": Lineage,
        "path": Template,
        "bond": EssentialBond,
    }
    mark_labels = {
        "ancestry": _("Ancestry"),
        "path": _("Path"),
        "bond": _("Bond"),
    }

    def get(self, request, *args, **kwargs):
        mark_type = next(
            (
                name
                for name in self.mark_models
                if any(key == name or key.endswith(f"-{name}") for key in request.GET)
            ),
            None,
        )
        if not mark_type:
            return HttpResponseBadRequest()

        mark_id = next(
            (
                value
                for key, value in request.GET.items()
                if key == mark_type or key.endswith(f"-{mark_type}")
            ),
            "",
        )
        campaign = self._campaign_from_request()
        queryset = essential_mark_queryset(
            self.mark_models[mark_type], user=request.user, campaign=campaign
        )
        mark = get_object_or_404(queryset, pk=mark_id) if mark_id else None
        return self.render_to_response(
            {
                "mark": mark,
                "mark_type": mark_type,
                "mark_type_label": self.mark_labels[mark_type],
            }
        )

    def _campaign_from_request(self):
        campaign_id = self.request.GET.get("campaign")
        if not campaign_id:
            return None
        return get_object_or_404(
            Campaign, pk=campaign_id, ruleset=Campaign.RULESET_ESSENTIAL
        )


class EssentialCustomMarkCreateView(LoginRequiredMixin, FormView):
    template_name = "essential_characters/_custom_mark_form.html"
    form_class = EssentialCustomMarkForm
    mark_models = {
        "ancestry": Lineage,
        "path": Template,
        "bond": EssentialBond,
    }
    mark_labels = {
        "ancestry": _("Ancestry"),
        "path": _("Path"),
        "bond": _("Bond"),
    }

    def dispatch(self, request, *args, **kwargs):
        if kwargs["mark_type"] not in self.mark_models:
            return HttpResponseBadRequest()
        self.campaign = self.get_campaign()
        return super().dispatch(request, *args, **kwargs)

    def get_campaign(self):
        campaign_id = self.request.GET.get("campaign")
        if not campaign_id:
            return None
        campaign = get_object_or_404(
            Campaign, pk=campaign_id, ruleset=Campaign.RULESET_ESSENTIAL
        )
        if campaign.world_extension.identifier != "tirakan":
            raise PermissionDenied()
        return campaign

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(mark_type=self.kwargs["mark_type"], user=self.request.user)
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "translate_with_openai" in form.fields and not settings.OPENAI_API_KEY:
            form.fields["translate_with_openai"].disabled = True
            form.fields["translate_with_openai"].initial = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mark_type"] = self.kwargs["mark_type"]
        context["mark_type_label"] = self.mark_labels[self.kwargs["mark_type"]]
        context["campaign"] = self.campaign
        context["openai_configured"] = bool(settings.OPENAI_API_KEY)
        return context

    @transaction.atomic
    def form_valid(self, form):
        values = {
            key: form.cleaned_data.get(key, "")
            for key in (
                "name",
                "description",
                "benefit",
                "vulnerability",
                "skills",
                "facet",
            )
            if key in form.fields
        }
        if self.request.user.is_staff and form.cleaned_data.get(
            "translate_with_openai"
        ):
            try:
                localized = translate_custom_mark(values)
            except Exception:
                form.add_error(None, _("Translation failed. Please try again."))
                return self.form_invalid(form)
        else:
            localized = {"de": values, "en": values}

        for language in ("de", "en"):
            localized.setdefault(language, {})
            for key, value in values.items():
                localized[language].setdefault(key, value)

        try:
            with transaction.atomic():
                obj = self._create_mark(localized)
        except IntegrityError:
            form.add_error("name", _("A mark with this name already exists."))
            return self.form_invalid(form)
        except ValueError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        return JsonResponse(
            {"id": obj.pk, "label": str(obj), "mark_type": self.kwargs["mark_type"]}
        )

    def _localized_fields(self, localized, field_map):
        return {
            f"{model_field}_{language}": localized.get(language, {}).get(
                input_field, ""
            )
            for input_field, model_field in field_map.items()
            for language in ("de", "en")
        }

    def _create_mark(self, localized):
        common = {
            "created_by": self.request.user,
            "is_homebrew": True,
            "homebrew_campaign": self.campaign,
        }
        mark_type = self.kwargs["mark_type"]
        if mark_type == "bond":
            fields = self._localized_fields(
                localized,
                {
                    "name": "name",
                    "description": "description",
                    "benefit": "benefit",
                    "vulnerability": "vulnerability",
                },
            )
            return EssentialBond.objects.create(**common, **fields)

        fields = self._localized_fields(
            localized,
            {
                "name": "name",
                "description": "essential_description",
                "benefit": "essential_benefit",
                "vulnerability": "essential_vulnerability",
                "skills": "essential_skills",
                **({"facet": "essential_facet"} if mark_type == "path" else {}),
            },
        )
        if mark_type == "ancestry":
            obj = Lineage.objects.create(essential_enabled=True, **common, **fields)
        else:
            category = (
                Template.objects.filter(essential_enabled=True)
                .values_list("category", flat=True)
                .first()
            )
            if not category:
                raise ValueError(
                    "No template category is available for Essential paths."
                )
            obj = Template.objects.create(
                essential_enabled=True, category_id=category, **common, **fields
            )
        obj.extensions.set(
            Extension.objects.filter(identifier__in=("tirakan", "middleages"))
        )
        return obj


class EssentialAddSkillView(LoginRequiredMixin, FormView):
    template_name = "essential_characters/_add_skill_form.html"
    form_class = EssentialAddSkillForm

    def form_valid(self, form):
        return JsonResponse(
            {
                "name": form.cleaned_data["name"],
                "rank": form.cleaned_data["rank"],
            }
        )


class EssentialCustomEquipmentCreateView(LoginRequiredMixin, FormView):
    template_name = "essential_characters/_custom_equipment_form.html"
    form_class = EssentialCustomEquipmentForm
    equipment_models = {
        "weapon": Weapon,
        "armor": RiotGear,
        "item": Item,
    }
    equipment_labels = {
        "weapon": _("Weapon"),
        "armor": _("Armor"),
        "item": _("Item"),
    }

    def dispatch(self, request, *args, **kwargs):
        if kwargs["equipment_type"] not in self.equipment_models:
            return HttpResponseBadRequest()
        self.campaign = self.get_campaign()
        return super().dispatch(request, *args, **kwargs)

    def get_campaign(self):
        campaign_id = self.request.GET.get("campaign")
        if not campaign_id:
            return None
        campaign = get_object_or_404(
            Campaign, pk=campaign_id, ruleset=Campaign.RULESET_ESSENTIAL
        )
        if campaign.world_extension.identifier != "tirakan":
            raise PermissionDenied()
        return campaign

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            equipment_type=self.kwargs["equipment_type"], user=self.request.user
        )
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "translate_with_openai" in form.fields and not settings.OPENAI_API_KEY:
            form.fields["translate_with_openai"].disabled = True
            form.fields["translate_with_openai"].initial = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["equipment_type"] = self.kwargs["equipment_type"]
        context["equipment_type_label"] = self.equipment_labels[
            self.kwargs["equipment_type"]
        ]
        context["campaign"] = self.campaign
        context["openai_configured"] = bool(settings.OPENAI_API_KEY)
        return context

    @transaction.atomic
    def form_valid(self, form):
        localized = {
            "de": {
                "name": form.cleaned_data["name"],
                "description": form.cleaned_data["description"],
            },
            "en": {
                "name": form.cleaned_data["name"],
                "description": form.cleaned_data["description"],
            },
        }
        if self.request.user.is_staff and form.cleaned_data.get(
            "translate_with_openai"
        ):
            try:
                localized = translate_custom_mark(localized["de"])
            except Exception:
                form.add_error(None, _("Translation failed. Please try again."))
                return self.form_invalid(form)
        for language in ("de", "en"):
            localized.setdefault(language, {})
            localized[language].setdefault("name", form.cleaned_data["name"])
            localized[language].setdefault(
                "description", form.cleaned_data["description"]
            )
        obj = self._create_equipment(form.cleaned_data, localized)
        target = self.request.GET.get("target", "")
        valid_targets = {
            "weapon": {"primary_weapon", "secondary_weapon"},
            "armor": {"armor"},
            "item": {"items"},
        }
        if target not in valid_targets[self.kwargs["equipment_type"]]:
            target = next(iter(valid_targets[self.kwargs["equipment_type"]]))
        return JsonResponse(
            {
                "id": obj.pk,
                "label": str(obj),
                "equipment_type": self.kwargs["equipment_type"],
                "target": target,
            }
        )

    def _create_equipment(self, data, localized):
        common = {
            "created_by": self.request.user,
            "is_homebrew": True,
            "homebrew_campaign": self.campaign,
            "essential_enabled": True,
            "name_de": localized["de"]["name"],
            "name_en": localized["en"]["name"],
            "description_de": localized["de"]["description"],
            "description_en": localized["en"]["description"],
            "type": data["type"],
        }
        equipment_type = self.kwargs["equipment_type"]
        if equipment_type == "weapon":
            obj = Weapon.objects.create(
                **common,
                weight=0,
                price=0,
                essential_damage=data["damage"],
                essential_range=data["range"],
                essential_grip=data["grip"],
                essential_properties=data["properties"],
            )
        elif equipment_type == "armor":
            obj = RiotGear.objects.create(
                **common,
                encumbrance=0,
                concealment=0,
                weight=0,
                price=0,
                essential_protection=data["protection"],
                essential_load=data["load"],
                essential_sealing=data["sealing"],
                essential_properties=data["properties"],
            )
        else:
            obj = Item.objects.create(
                **common,
                weight=0,
                price=0,
                concealment=0,
            )
        obj.extensions.set(
            Extension.objects.filter(identifier__in=("tirakan", "middleages"))
        )
        return obj


class EquipmentSummaryView(LoginRequiredMixin, TemplateView):
    template_name = "essential_characters/_equipment_summary.html"
    equipment_models = {
        "primary_weapon": ("weapon", Weapon),
        "secondary_weapon": ("weapon", Weapon),
        "armor": ("armor", RiotGear),
        "items": ("items", Item),
    }

    def get(self, request, *args, **kwargs):
        field_name = next(
            (
                name
                for name in self.equipment_models
                if any(key == name or key.endswith(f"-{name}") for key in request.GET)
            ),
            None,
        )
        if not field_name:
            return HttpResponseBadRequest()

        resource_type, model = self.equipment_models[field_name]
        key = next(
            key
            for key in request.GET
            if key == field_name or key.endswith(f"-{field_name}")
        )
        values = [value for value in request.GET.getlist(key) if value]
        resources = essential_equipment_queryset(
            model,
            user=request.user,
            campaign=self._campaign_from_request(),
        ).filter(pk__in=values)
        return self.render_to_response(
            {
                "resources": resources,
                "resource_type": resource_type,
            }
        )

    def _campaign_from_request(self):
        campaign_id = self.request.GET.get("campaign")
        if not campaign_id:
            return None
        return get_object_or_404(
            Campaign, pk=campaign_id, ruleset=Campaign.RULESET_ESSENTIAL
        )


class SupernaturalSummaryView(LoginRequiredMixin, TemplateView):
    template_name = "essential_characters/_supernatural_summary.html"

    def get(self, request, *args, **kwargs):
        field_name = next(
            (
                key.split("-")[-1]
                for key in request.GET
                if key.split("-")[-1].startswith(("magic_aspect_", "spell_"))
            ),
            None,
        )
        if not field_name:
            return HttpResponseBadRequest()
        key = next(key for key in request.GET if key.endswith(field_name))
        value = request.GET.get(key)
        context = {"origin": None, "spell": None}
        if field_name.startswith("magic_aspect_"):
            context["origin"] = (
                get_object_or_404(SpellOrigin, pk=value) if value else None
            )
        else:
            context["spell"] = (
                get_object_or_404(BaseSpell.objects.select_related("origin"), pk=value)
                if value
                else None
            )
        return self.render_to_response(context)


class EssentialCharacterDetailInfoView(TemplateView):
    template_name = "essential_characters/_detail_info.html"
    sections = {"marks", "conditions", "derived"}

    def get(self, request, *args, **kwargs):
        if self.kwargs["section"] not in self.sections:
            return HttpResponseBadRequest()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(
            EssentialCharacter, slug=self.kwargs["slug"]
        )
        context["section"] = self.kwargs["section"]
        return context


class EssentialCharacterDetailView(DetailView):
    model = EssentialCharacter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class EssentialCharacterImageView(LoginRequiredMixin, View):
    def get_character(self):
        character = get_object_or_404(EssentialCharacter, slug=self.kwargs["slug"])
        if not character.may_edit(self.request.user):
            raise PermissionDenied()
        return character

    def get(self, request, *args, **kwargs):
        self.get_character()
        return HttpResponseBadRequest()

    def post(self, request, *args, **kwargs):
        character = self.get_character()
        if request.POST.get("remove_image"):
            character.image = None
            character.save(update_fields=["image", "modified_at"])
        else:
            form = EssentialCharacterImageForm(
                request.POST, request.FILES, instance=character
            )
            if form.is_valid():
                form.save()
        return HttpResponseRedirect(character.get_absolute_url())


class EssentialCharacterEditSectionView(LoginRequiredMixin, FormView):
    template_name = "essential_characters/_edit_section_form.html"
    sections = {
        "identity": (EssentialIdentityEditForm, _("Identity")),
        "marks": (EssentialMarksEditForm, _("Marks")),
        "attributes": (EssentialAttributesEditForm, _("Attributes")),
        "skills": (EssentialSkillsEditForm, _("Skills")),
        "equipment": (EssentialEquipmentEditForm, _("Equipment")),
        "supernatural": (EssentialSupernaturalEditForm, _("Magic and belief")),
        "notes": (EssentialNotesEditForm, _("Notes")),
    }

    def dispatch(self, request, *args, **kwargs):
        self.character = get_object_or_404(EssentialCharacter, slug=kwargs["slug"])
        if not self.character.may_edit(request.user):
            raise PermissionDenied()
        if kwargs["section"] not in self.sections:
            return HttpResponseBadRequest()
        self.form_class, self.section_label = self.sections[kwargs["section"]]
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.kwargs["section"] == "skills":
            kwargs["character"] = self.character
        else:
            kwargs["instance"] = self.character
        if self.kwargs["section"] == "marks":
            kwargs["user"] = self.request.user
            kwargs["campaign"] = self.character.campaign or self.character.npc_campaign
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        search_url = reverse(
            "essential_characters:edit_search", kwargs={"slug": self.character.slug}
        )
        for field in form.fields.values():
            if isinstance(field.widget, AjaxSearchSelectMultiple):
                field.widget.attrs["data-search-url"] = search_url
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.character
        context["section"] = self.kwargs["section"]
        context["section_label"] = self.section_label
        if self.kwargs["section"] == "skills":
            context["skill_rows"] = [
                (
                    context["form"][f"skill_{index}_name"],
                    context["form"][f"skill_{index}_rank"],
                )
                for index in range(9)
            ]
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.save()
        condition_limits = {
            "wounds": self.character.wound_threshold,
            "burden": self.character.burden_threshold,
            "omen": self.character.omen_max,
            "arkana": self.character.arkana_max,
            "favor": self.character.favor_max,
        }
        changed_conditions = []
        for condition, limit in condition_limits.items():
            if getattr(self.character, condition) > limit:
                setattr(self.character, condition, limit)
                changed_conditions.append(condition)
        if changed_conditions:
            self.character.save(update_fields=[*changed_conditions, "modified_at"])
        return HttpResponseRedirect(self.character.get_absolute_url())


class EssentialCharacterConditionView(LoginRequiredMixin, View):
    condition_limits = {
        "wounds": lambda character: character.wound_threshold,
        "burden": lambda character: character.burden_threshold,
        "omen": lambda character: character.omen_max,
        "arkana": lambda character: character.arkana_max,
        "favor": lambda character: character.favor_max,
        "corruption": lambda character: max(6, character.corruption),
    }

    def post(self, request, *args, **kwargs):
        character = get_object_or_404(EssentialCharacter, slug=kwargs["slug"])
        if not character.may_edit(request.user):
            raise PermissionDenied()
        condition = kwargs["condition"]
        if condition not in self.condition_limits:
            return HttpResponseBadRequest()
        try:
            value = int(request.POST.get("value", ""))
        except ValueError:
            return HttpResponseBadRequest()
        if not 0 <= value <= self.condition_limits[condition](character):
            return HttpResponseBadRequest()
        setattr(character, condition, value)
        character.save(update_fields=[condition, "modified_at"])
        return HttpResponse(status=204)


class EssentialCharacterEditSearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        character = get_object_or_404(EssentialCharacter, slug=kwargs["slug"])
        if not character.may_edit(request.user):
            raise PermissionDenied()
        search_type = request.GET.get("type")
        query = request.GET.get("q", "").strip()
        query_filter = Q(name_de__icontains=query) | Q(name_en__icontains=query)
        querysets = {
            "weapons": Weapon.objects.filter(essential_enabled=True),
            "armor": RiotGear.objects.filter(essential_enabled=True),
            "items": essential_item_queryset(),
            "magic_aspects": SpellOrigin.objects.all(),
            "spells": BaseSpell.objects.select_related("origin"),
        }
        if search_type not in querysets:
            return HttpResponseBadRequest()
        queryset = querysets[search_type]
        if search_type == "spells":
            origins = request.GET.getlist("origin")
            queryset = (
                queryset.filter(origin_id__in=origins) if origins else queryset.none()
            )
        results = []
        for resource in queryset.filter(query_filter).distinct()[:12]:
            meta = ""
            if search_type in {"weapons", "armor", "items"}:
                meta = str(resource.type)
            elif search_type == "spells":
                meta = str(resource.origin or "")
            results.append({"id": resource.pk, "text": str(resource), "meta": meta})
        return JsonResponse({"results": results})


class EssentialCharacterCreateWizard(LoginRequiredMixin, SessionWizardView):
    template_name = "essential_characters/essentialcharacter_wizard.html"

    @staticmethod
    def show_supernatural_step(wizard):
        attributes = wizard.get_cleaned_data_for_step("attributes") or {}
        return attributes.get("gift", 0) > 0

    def get(self, request, *args, **kwargs):
        requested_step = request.GET.get("step")
        if not requested_step:
            self.storage.reset()
            self._store_assignment_query_parameters()
            self.get_campaign()
            self.get_plot()
            self.storage.current_step = self.steps.first
            return HttpResponseRedirect(self.get_step_url(self.steps.first))
        if self.storage.current_step is None:
            self.storage.reset()
        self._store_assignment_query_parameters()
        self.get_campaign()
        self.get_plot()
        if requested_step in self.get_form_list():
            self.storage.current_step = requested_step
        else:
            if self.storage.current_step not in self.get_form_list():
                self.storage.current_step = self.steps.first
            return HttpResponseRedirect(self.get_step_url(self.steps.current))
        return self.render(
            self.get_form(
                data=self.storage.get_step_data(self.steps.current),
                files=self.storage.get_step_files(self.steps.current),
            )
        )

    def _store_assignment_query_parameters(self):
        for name in ("campaign", "plot"):
            if name in self.request.GET:
                self.storage.extra_data[f"{name}_id"] = self.request.GET.get(name)

    def get_step_url(self, step):
        query = self.request.GET.copy()
        query["step"] = step
        return f"{reverse('essential_characters:create')}?{query.urlencode()}"

    def render_next_step(self, form, **kwargs):
        self.storage.current_step = self.steps.next
        return HttpResponseRedirect(self.get_step_url(self.steps.current))

    def render_goto_step(self, goto_step, **kwargs):
        self.storage.current_step = goto_step
        return HttpResponseRedirect(self.get_step_url(goto_step))

    def get_campaign(self):
        campaign_id = self.storage.extra_data.get("campaign_id")
        if not campaign_id:
            return None
        campaign = get_object_or_404(
            Campaign, pk=campaign_id, ruleset=Campaign.RULESET_ESSENTIAL
        )
        if campaign.world_extension.identifier != "tirakan":
            raise PermissionDenied()
        return campaign

    def get_plot(self):
        plot_id = self.storage.extra_data.get("plot_id")
        if not plot_id:
            return None
        return get_object_or_404(Plot, pk=plot_id, ruleset=Plot.RULESET_ESSENTIAL)

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        if step == "concept":
            campaign = self.get_campaign()
            if campaign:
                initial["concept"] = ""
        if step == "skills":
            marks = self.get_cleaned_data_for_step("marks") or {}
            path = marks.get("path")
            suggestions = (
                [
                    value.strip()
                    for value in path.essential_skills.split(",")
                    if value.strip()
                ]
                if path and path.essential_skills
                else []
            )
            for index, name in enumerate(suggestions[:9]):
                initial[f"skill_{index}_name"] = name
        return initial

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == "marks":
            kwargs["user"] = self.request.user
            kwargs["campaign"] = self.get_campaign()
        if step == "skills":
            marks = self.get_cleaned_data_for_step("marks") or {}
            kwargs["path"] = marks.get("path")
        if step == "equipment":
            kwargs["user"] = self.request.user
            kwargs["campaign"] = self.get_campaign()
        if step == "supernatural":
            attributes = self.get_cleaned_data_for_step("attributes") or {}
            kwargs["gift"] = attributes.get("gift", 0)
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context["step_label"] = WIZARD_STEP_LABELS[self.steps.current]
        context["step_description"] = WIZARD_STEP_DESCRIPTIONS[self.steps.current]
        context["step_number"] = (
            list(self.get_form_list()).index(self.steps.current) + 1
        )
        context["total_steps"] = len(self.get_form_list())
        context["step_navigation"] = [
            {
                "name": step,
                "label": WIZARD_STEP_LABELS[step],
                "url": self.get_step_url(step),
                "active": step == self.steps.current,
                "reached": index
                <= list(self.get_form_list()).index(self.steps.current),
            }
            for index, step in enumerate(self.get_form_list())
        ]
        context["previous_step_url"] = (
            self.get_step_url(self.steps.prev) if self.steps.prev else None
        )
        context["campaign"] = self.get_campaign()
        if self.steps.current == "skills":
            context["skill_rows"] = [
                (form[f"skill_{index}_name"], form[f"skill_{index}_rank"])
                for index in range(9)
            ]
        if self.steps.current == "supernatural":
            slots = magic_slots(form.gift)
            context["supernatural_text_fields"] = (
                form["focus"],
                form["regeneration_ritual"],
            )
            context["supernatural_aspect_fields"] = [
                form[f"magic_aspect_{index}"] for index in range(slots["aspects"])
            ]
            context["supernatural_spell_fields"] = [
                form[f"spell_{index}"] for index in range(slots["spells"])
            ]
        attributes = self.get_cleaned_data_for_step("attributes") or {}
        if attributes:
            context["magic_slots"] = magic_slots(attributes["gift"])
        return context

    @transaction.atomic
    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        character = EssentialCharacter(
            created_by=self.request.user,
            campaign=self.get_campaign(),
            plot=self.get_plot(),
            name=data["name"],
            concept=data["concept"],
            birth_date=data["birth_date"],
            century=data["century"],
            ancestry=data.get("ancestry"),
            path=data.get("path"),
            bond=data.get("bond"),
            oath_or_debt=data.get("oath_or_debt", ""),
            focus=data.get("focus", ""),
            regeneration_ritual=data.get("regeneration_ritual", ""),
            **{attribute: data[attribute] for attribute in ATTRIBUTES},
        )
        character.omen = character.omen_max
        character.arkana = character.arkana_max
        character.favor = character.favor_max
        character.save()

        EssentialCharacterSkill.replace_for_character(character, data["skills"])
        character.weapons.set(
            filter(None, (data.get("primary_weapon"), data.get("secondary_weapon")))
        )
        character.armor.set(filter(None, (data.get("armor"),)))
        character.items.set(data.get("items", ()))
        character.magic_aspects.set(data.get("magic_aspects", ()))
        character.spells.set(data.get("spells", ()))
        character.validate_assignments()
        return HttpResponseRedirect(character.get_absolute_url())


class EssentialCharacterUpdateView(LoginRequiredMixin, UpdateView):
    model = EssentialCharacter
    form_class = EssentialCharacterForm
    template_name = "essential_characters/essentialcharacter_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().may_edit(request.user):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(campaign=self.object.campaign, plot=self.object.plot)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        assignments = self.object.essentialcharacterskill_set.all()
        initial["skill_names"] = "\n".join(a.name for a in assignments)
        initial["skill_ranks"] = "\n".join(str(a.rank) for a in assignments)
        return initial
