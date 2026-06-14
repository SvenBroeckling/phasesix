from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
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
from rules.models import Lineage, Template
from .forms import (
    AttributesForm,
    AjaxSearchSelectMultiple,
    ConceptForm,
    EquipmentForm,
    EssentialCharacterForm,
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
)
from .models import (
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
)
from .rules import ATTRIBUTES, magic_slots

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
        queryset = self.mark_models[mark_type].objects.all()
        if mark_type != "bond":
            queryset = queryset.filter(essential_enabled=True)
        mark = get_object_or_404(queryset, pk=mark_id) if mark_id else None
        return self.render_to_response(
            {
                "mark": mark,
                "mark_type": mark_type,
                "mark_type_label": self.mark_labels[mark_type],
            }
        )


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
        resources = (
            essential_item_queryset().filter(pk__in=values)
            if model is Item
            else model.objects.filter(pk__in=values, essential_enabled=True)
        )
        return self.render_to_response(
            {
                "resources": resources,
                "resource_type": resource_type,
            }
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
        if step == "skills":
            marks = self.get_cleaned_data_for_step("marks") or {}
            kwargs["path"] = marks.get("path")
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

        for name, rank in data["skills"]:
            EssentialCharacterSkill.objects.create(
                character=character, name=name, rank=rank
            )
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
