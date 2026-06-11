from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView
from formtools.wizard.views import SessionWizardView

from campaigns.models import Campaign
from plots.models import Plot
from .forms import (
    AttributesForm,
    ConceptForm,
    EquipmentForm,
    EssentialCharacterForm,
    MarksForm,
    OathForm,
    SkillsForm,
    SupernaturalForm,
)
from .models import (
    EssentialAncestry,
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterArmor,
    EssentialCharacterItem,
    EssentialCharacterSkill,
    EssentialCharacterSpell,
    EssentialCharacterWeapon,
    EssentialPath,
    EssentialSkill,
)
from .rules import ATTRIBUTES, CENTURY_LEVELS, magic_slots

WIZARD_FORMS = (
    ("concept", ConceptForm),
    ("attributes", AttributesForm),
    ("marks", MarksForm),
    ("skills", SkillsForm),
    ("oath", OathForm),
    ("equipment", EquipmentForm),
    ("supernatural", SupernaturalForm),
)
WIZARD_STEP_LABELS = {
    "concept": _("Concept"),
    "attributes": _("Attributes"),
    "marks": _("Marks"),
    "skills": _("Skills"),
    "oath": _("Oath or debt"),
    "equipment": _("Equipment"),
    "supernatural": _("Supernatural access"),
}
WIZARD_STEP_DESCRIPTIONS = {
    "concept": _("Give your character a name, concept, birth date, and century."),
    "attributes": _("Choose one attribute at 3, two at 2, three at 1, and two at 0."),
    "marks": _("Choose ancestry, path, and bond."),
    "skills": _("Choose one skill at rank 3, three at rank 2, and five at rank 1."),
    "oath": _("Describe the oath or debt that drives your character."),
    "equipment": _("Choose shared equipment with an Essential profile."),
    "supernatural": _("Choose the supernatural access granted by Gift."),
}


def show_supernatural_step(wizard):
    attributes = wizard.get_cleaned_data_for_step("attributes") or {}
    return attributes.get("gift", 0) > 0


@login_required
def mark_summary(request):
    mark_models = {
        "ancestry": EssentialAncestry,
        "path": EssentialPath,
        "bond": EssentialBond,
    }
    mark_labels = {
        "ancestry": _("Ancestry"),
        "path": _("Path"),
        "bond": _("Bond"),
    }
    mark_type = next(
        (
            name
            for name in mark_models
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
    mark = get_object_or_404(mark_models[mark_type], pk=mark_id) if mark_id else None
    return render(
        request,
        "essential_characters/_mark_summary.html",
        {
            "mark": mark,
            "mark_type": mark_type,
            "mark_type_label": mark_labels[mark_type],
        },
    )


class EssentialCharacterDetailView(DetailView):
    model = EssentialCharacter


class EssentialCharacterCreateWizard(LoginRequiredMixin, SessionWizardView):
    template_name = "essential_characters/essentialcharacter_wizard.html"

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
                [value.strip() for value in path.skills.split(",") if value.strip()]
                if path
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
        attributes = self.get_cleaned_data_for_step("attributes") or {}
        concept = self.get_cleaned_data_for_step("concept") or {}
        if attributes and concept:
            faith, magic = CENTURY_LEVELS[concept.get("century", 1)]
            context["derived_preview"] = {
                "wounds": 3 + attributes["body"],
                "burden": 5 + attributes["will"] // 2,
                "initiative": 30 + attributes["dexterity"] * 10,
                "faith": faith,
                "magic": magic,
                "arkana": 3 + attributes["mind"],
                "favor": 3 + attributes["will"],
            }
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
            notes=data.get("notes", ""),
            focus=data.get("focus", ""),
            regeneration_ritual=data.get("regeneration_ritual", ""),
            **{attribute: data[attribute] for attribute in ATTRIBUTES},
        )
        character.omen = character.omen_max
        character.arkana = character.arkana_max
        character.favor = character.favor_max
        character.save()

        for name, rank in data["skills"]:
            skill, _ = EssentialSkill.objects.get_or_create(name=name)
            EssentialCharacterSkill.objects.create(
                character=character, skill=skill, rank=rank
            )
        for slot in ("primary", "secondary"):
            profile = data.get(f"{slot}_weapon")
            if profile:
                EssentialCharacterWeapon.objects.create(
                    character=character, profile=profile, slot=slot
                )
        if data.get("armor_profile"):
            EssentialCharacterArmor.objects.create(
                character=character, profile=data["armor_profile"]
            )
        for item in data.get("item_profiles", ()):
            EssentialCharacterItem.objects.create(character=character, item=item)
        character.magic_aspects.set(data.get("magic_aspect_profiles", ()))
        for profile in data.get("spell_profiles", ()):
            EssentialCharacterSpell.objects.create(character=character, profile=profile)
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
        assignments = self.object.essentialcharacterskill_set.select_related("skill")
        initial["skill_names"] = "\n".join(a.skill.name for a in assignments)
        initial["skill_ranks"] = "\n".join(str(a.rank) for a in assignments)
        return initial
