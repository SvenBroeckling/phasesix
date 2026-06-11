from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView
from django.utils.translation import gettext as _
import logging

from plots.forms import (
    PlotForm,
    PlotElementForm,
    HandoutForm,
    LocationForm,
    PlotNpcForm,
    PlotFromDescriptionForm,
)
from plots.models import Plot, PlotElement, Handout, Location
from campaigns.models import Campaign
from plots.openai import PlotOpenAIService
from characters.models import Character
from essential_characters.models import EssentialCharacter
from rules.models import Foe, Extension

logger = logging.getLogger(__name__)


def user_may_use_ai(user):
    return bool(
        user
        and user.is_authenticated
        and hasattr(user, "profile")
        and user.profile.may_use_ai
    )


@method_decorator(csrf_exempt, name="dispatch")
class XhrReorderPlotElementView(View):
    def post(self, request, *args, **kwargs):
        parent_id = request.POST.get("parent_id")
        element_ids = request.POST.getlist("element_ids[]")

        if parent_id == "root":
            parent = None
        else:
            parent = get_object_or_404(PlotElement, id=parent_id)

        for index, element_id in enumerate(element_ids):
            PlotElement.objects.filter(id=element_id).update(
                parent=parent, ordering=index
            )

        return JsonResponse({"status": "ok"})


class PlotEditorView(DetailView):
    template_name = "plots/plot_editor.html"
    model = Plot


class PlotListView(ListView):
    model = Plot
    template_name = "plots/plot_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                cloned_from__isnull=True,
                campaign__isnull=True,
            )
        )


class XhrPlotFragmentView(DetailView):
    model = Plot

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fragment_template"] = self.kwargs["fragment_template"]
        return context

    def get_template_names(self):
        return ["plots/fragments/" + self.kwargs["fragment_template"] + ".html"]


class XhrCampaignPlotViewFragment(View):
    def get(self, request, *args, **kwargs):
        plot = get_object_or_404(Plot, id=kwargs["plot_pk"])
        campaign = get_object_or_404(Campaign, id=kwargs["campaign_pk"])
        if plot.campaign_id != campaign.id:
            raise PermissionDenied()
        if not campaign.may_edit(request.user):
            raise PermissionDenied()
        return render(
            request,
            "plots/fragments/campaign_plot_view.html",
            {"plot": plot, "campaign": campaign},
        )


class XhrCreatePlotView(CreateView):
    model = Plot
    template_name = "plots/xhr_plot_modal.html"
    form_class = PlotForm
    extra_context = {
        "post_url": reverse_lazy("plots:create_plot"),
    }

    def _get_campaign(self):
        campaign_pk = self.request.GET.get("campaign_pk")
        if not campaign_pk:
            return None
        campaign = get_object_or_404(Campaign, id=campaign_pk)
        if not campaign.may_edit(self.request.user):
            raise PermissionDenied()
        return campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self._get_campaign()
        if campaign:
            context["campaign"] = campaign
            context["post_url"] = (
                reverse("plots:create_plot") + "?campaign_pk=" + str(campaign.id)
            )
            context["fetch_form_event_after"] = "refresh-campaign-dramaturgy"
        return context

    def form_valid(self, form):
        campaign = self._get_campaign()
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
            form.instance.is_homebrew = False
        if campaign:
            form.instance.campaign = campaign
            form.instance.ruleset = campaign.ruleset
            if not form.instance.world_extension_id:
                form.instance.world_extension = campaign.world_extension
            if not form.instance.epoch_extension_id:
                form.instance.epoch_extension = campaign.epoch_extension
        response = super().form_valid(form)
        if (
            campaign
            and not self.object.cloned_from_id
            and not self.object.plotelement_set.exists()
        ):
            PlotElement.objects.create(
                plot=self.object,
                name=_("How to edit this plot"),
                gm_notes=_(
                    "Toggle the Edit plot switch, then use Add Element in the properties panel."
                ),
            )
        return response

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.object.pk})


class XhrUpdatePlotView(UpdateView):
    model = Plot
    template_name = "plots/xhr_plot_modal.html"
    form_class = PlotForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_url"] = reverse(
            "plots:update_plot", kwargs={"pk": self.object.pk}
        )
        return context

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.object.pk})


class XhrCreatePlotFromDescriptionView(FormView):
    template_name = "plots/xhr_plot_from_description_modal.html"
    form_class = PlotFromDescriptionForm

    def dispatch(self, request, *args, **kwargs):
        if not user_may_use_ai(request.user):
            raise PermissionDenied()
        self.plot = get_object_or_404(Plot, id=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_url"] = reverse(
            "plots:create_plot_from_description", kwargs={"pk": self.plot.pk}
        )
        context["plot"] = self.plot
        return context

    def get_initial(self):
        initial = super().get_initial()
        if getattr(self, "plot", None):
            initial["language"] = self.plot.language
        return initial

    def form_valid(self, form):
        description = form.cleaned_data.get("description", "").strip()
        language = form.cleaned_data.get("language")
        if not description:
            form.add_error("description", _("Please provide a plot description."))
            return self.form_invalid(form)
        try:
            PlotOpenAIService(self.plot).create_from_description(
                description, language=language
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        except Exception:
            logger.exception("Plot generation failed for plot=%s", self.plot.pk)
            form.add_error(None, _("Plot generation failed. Please try again."))
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.plot.pk})


class XhrCreatePlotElementView(CreateView):
    model = PlotElement
    template_name = "plots/xhr_plot_element_modal.html"
    form_class = PlotElementForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot = get_object_or_404(Plot, id=self.kwargs["plot_pk"])
        url = reverse("plots:create_plot_element", kwargs={"plot_pk": plot.pk})
        if self.request.GET.get("parent_pk"):
            url += "?parent_pk=" + self.request.GET.get("parent_pk")
        context["post_url"] = url
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        parent_pk = self.request.GET.get("parent_pk")
        if parent_pk:
            obj.parent = get_object_or_404(PlotElement, id=parent_pk)
        obj.plot = get_object_or_404(Plot, id=self.kwargs["plot_pk"])
        obj.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.kwargs["plot_pk"]})


class XhrUpdatePlotElementView(UpdateView):
    model = PlotElement
    template_name = "plots/xhr_plot_element_modal.html"
    form_class = PlotElementForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_url"] = reverse(
            "plots:update_plot_element", kwargs={"pk": self.object.pk}
        )
        context["delete_url"] = reverse(
            "plots:delete_plot_element", kwargs={"pk": self.object.pk}
        )
        return context

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.kwargs["pk"]})


class DeletePlotElementView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["pk"])
        new_parent = plot_element.parent

        if new_parent is None:
            sibling_qs = PlotElement.objects.filter(
                plot=plot_element.plot, parent__isnull=True
            ).exclude(id=plot_element.id)
        else:
            sibling_qs = PlotElement.objects.filter(parent=new_parent).exclude(
                id=plot_element.id
            )

        children = list(plot_element.children.order_by("ordering"))
        child_count = len(children)
        shift_by = child_count - 1
        insertion_point = plot_element.ordering

        with transaction.atomic():
            if shift_by != 0:
                sibling_qs.filter(ordering__gt=insertion_point).update(
                    ordering=F("ordering") + shift_by
                )

            for index, child in enumerate(children):
                child.parent = new_parent
                child.ordering = insertion_point + index
                child.save(update_fields=["parent", "ordering"])

            plot_element.delete()

        return JsonResponse({"status": "ok"})


class XhrCreateHandoutView(CreateView):
    model = Handout
    template_name = "plots/xhr_handout_modal.html"
    form_class = HandoutForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:create_handout", kwargs={"plot_element_pk": plot_element.pk}
        )
        context["plot_element"] = plot_element
        context["existing_handouts"] = (
            Handout.objects.filter(plotelement__plot=plot_element.plot)
            .distinct()
            .exclude(id__in=plot_element.handouts.all())
        )
        return context

    def form_valid(self, form):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        plot_element.handouts.add(form.save())
        return super().form_valid(form)

    def get_success_url(self):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        return reverse("plots:plot_editor", kwargs={"pk": plot_element.plot.pk})


class XhrUpdateHandoutView(UpdateView):
    model = Handout
    template_name = "plots/xhr_handout_modal.html"
    form_class = HandoutForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:update_handout",
            kwargs={"plot_element_pk": plot_element.pk, "pk": self.object.pk},
        )
        context["plot_element"] = plot_element
        return context

    def get_success_url(self):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        return reverse("plots:plot_editor", kwargs={"pk": plot_element.plot.pk})


class DeleteHandoutView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        handout = get_object_or_404(Handout, id=self.kwargs["pk"])
        plot_element.handouts.remove(handout)
        if not handout.plotelement_set.exists():
            handout.delete()
        return JsonResponse({"status": "ok"})


class AssignHandoutView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["plot_element_pk"])
        handout = get_object_or_404(Handout, id=kwargs["handout_pk"])

        if handout.plotelement_set.first().plot != plot_element.plot:
            raise PermissionDenied()

        plot_element.handouts.add(handout)
        return JsonResponse({"status": "ok"})


class XhrCreateLocationView(CreateView):
    model = Location
    template_name = "plots/xhr_location_modal.html"
    form_class = LocationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:create_location", kwargs={"plot_element_pk": plot_element.pk}
        )
        context["plot_element"] = plot_element
        context["existing_locations"] = (
            Location.objects.filter(plotelement__plot=plot_element.plot)
            .distinct()
            .exclude(id__in=plot_element.locations.all())
        )
        return context

    def form_valid(self, form):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        plot_element.locations.add(form.save())
        return super().form_valid(form)

    def get_success_url(self):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        return reverse("plots:plot_editor", kwargs={"pk": plot_element.plot.pk})


class XhrUpdateLocationView(UpdateView):
    model = Location
    template_name = "plots/xhr_location_modal.html"
    form_class = LocationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:update_location",
            kwargs={"plot_element_pk": plot_element.pk, "pk": self.object.pk},
        )
        context["plot_element"] = plot_element
        return context

    def get_success_url(self):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        return reverse("plots:plot_editor", kwargs={"pk": plot_element.plot.pk})


class DeleteLocationView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        location = get_object_or_404(Location, id=self.kwargs["pk"])
        plot_element.locations.remove(location)
        if not location.plotelement_set.exists():
            location.delete()
        return JsonResponse({"status": "ok"})


class AssignLocationView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["plot_element_pk"])
        location = get_object_or_404(Location, id=kwargs["location_pk"])

        if location.plotelement_set.first().plot != plot_element.plot:
            raise PermissionDenied()

        plot_element.locations.add(location)
        return JsonResponse({"status": "ok"})


class XhrSelectPlotNpcView(DetailView):
    model = PlotElement
    template_name = "plots/sidebar/select_npc.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot = self.object.plot
        model = EssentialCharacter if plot.ruleset == Plot.RULESET_ESSENTIAL else Character
        relation = "essential_plot_elements__plot" if model is EssentialCharacter else "plotelement__plot"
        current = self.object.essential_npc if model is EssentialCharacter else self.object.npc
        assigned_characters = (
            model.objects.filter(**{relation: plot})
            .distinct()
            .exclude(id__in=current.all())
        )
        context["assigned_characters"] = assigned_characters
        context["characters"] = (
            model.objects.filter(created_by=self.request.user)
            .exclude(id__in=current.all())
            .exclude(id__in=assigned_characters.values_list("id", flat=True))
        )
        return context


class XhrSelectPlotFoeView(DetailView):
    model = PlotElement
    template_name = "plots/sidebar/select_foe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot = self.object.plot
        foes = Foe.objects.all()
        if plot.world_extension_id:
            extensions = Extension.objects.filter(
                Q(id__in=[p.id for p in plot.extensions.all()])
                | Q(id=plot.world_extension.id)
            )
            foes = foes.for_extensions(extensions)
        context["foes"] = foes.exclude(id__in=self.object.foes.all()).order_by(
            "name_de"
        )
        return context


class AddPlotNpcView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["pk"])
        model = EssentialCharacter if plot_element.plot.ruleset == Plot.RULESET_ESSENTIAL else Character
        character = get_object_or_404(model, id=kwargs["character_pk"])

        if character.created_by_id != request.user.id:
            raise PermissionDenied()

        clone = character.clone(plot=plot_element.plot)
        (plot_element.essential_npc if model is EssentialCharacter else plot_element.npc).add(clone)
        return JsonResponse({"status": "ok"})


class AssignPlotNpcView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["pk"])
        model = EssentialCharacter if plot_element.plot.ruleset == Plot.RULESET_ESSENTIAL else Character
        character = get_object_or_404(model, id=kwargs["character_pk"])

        if character.plot_id != plot_element.plot_id:
            raise PermissionDenied()
        if character.created_by_id != request.user.id:
            raise PermissionDenied()

        (plot_element.essential_npc if model is EssentialCharacter else plot_element.npc).add(character)
        return JsonResponse({"status": "ok"})


class DeletePlotNpcView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        model = EssentialCharacter if plot_element.plot.ruleset == Plot.RULESET_ESSENTIAL else Character
        character = get_object_or_404(model, id=self.kwargs["pk"])

        if character.created_by_id != request.user.id:
            raise PermissionDenied()

        (plot_element.essential_npc if model is EssentialCharacter else plot_element.npc).remove(character)
        if (
            character.plot_id == plot_element.plot_id
            and not (character.essential_plot_elements.exists() if model is EssentialCharacter else character.plotelement_set.exists())
        ):
            character.delete()
        return JsonResponse({"status": "ok"})


class AssignPlotFoeView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["pk"])
        foe = get_object_or_404(Foe, id=kwargs["foe_pk"])
        plot_element.foes.add(foe)
        return JsonResponse({"status": "ok"})


class DeletePlotFoeView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        foe = get_object_or_404(Foe, id=self.kwargs["pk"])
        plot_element.foes.remove(foe)
        return JsonResponse({"status": "ok"})


class XhrUpdatePlotNpcView(UpdateView):
    model = Character
    template_name = "plots/xhr_plot_npc_modal.html"
    form_class = PlotNpcForm

    def get_queryset(self):
        return Character.objects.filter(plotelement__id=self.kwargs["plot_element_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:update_plot_npc",
            kwargs={"plot_element_pk": plot_element.pk, "pk": self.object.pk},
        )
        context["plot_element"] = plot_element
        return context

    def get_success_url(self):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        return reverse("plots:plot_editor", kwargs={"pk": plot_element.plot.pk})


class XhrUpdatePlotFoeView(DetailView):
    model = Foe
    template_name = "plots/xhr_plot_foe_modal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plot_element"] = get_object_or_404(
            PlotElement, id=self.kwargs["plot_element_pk"]
        )
        return context
