from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from plots.forms import (
    PlotForm,
    PlotElementForm,
    HandoutForm,
    LocationForm,
    PlotNpcForm,
)
from plots.models import Plot, PlotElement, Handout, Location
from characters.models import Character


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


class XhrPlotFragmentView(DetailView):
    model = Plot

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fragment_template"] = self.kwargs["fragment_template"]
        return context

    def get_template_names(self):
        return ["plots/fragments/" + self.kwargs["fragment_template"] + ".html"]


class XhrCreatePlotView(CreateView):
    model = Plot
    template_name = "plots/xhr_plot_modal.html"
    form_class = PlotForm
    extra_context = {
        "post_url": reverse_lazy("plots:create_plot"),
    }

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


class XhrCreatePlotElementView(CreateView):
    model = PlotElement
    template_name = "plots/xhr_plot_modal.html"
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
    template_name = "plots/xhr_plot_modal.html"
    form_class = PlotElementForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_url"] = reverse(
            "plots:update_plot_element", kwargs={"pk": self.object.pk}
        )
        return context

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.kwargs["pk"]})


class XhrCreateHandoutView(CreateView):
    model = Handout
    template_name = "plots/xhr_plot_modal.html"
    form_class = HandoutForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:create_handout", kwargs={"plot_element_pk": plot_element.pk}
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


class XhrCreateLocationView(CreateView):
    model = Location
    template_name = "plots/xhr_plot_modal.html"
    form_class = LocationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        context["post_url"] = reverse(
            "plots:create_location", kwargs={"plot_element_pk": plot_element.pk}
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


class XhrSelectPlotNpcView(DetailView):
    model = PlotElement
    template_name = "plots/sidebar/select_npc.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot = self.object.plot
        assigned_characters = (
            Character.objects.filter(plotelement__plot=plot)
            .distinct()
            .exclude(id__in=self.object.npc.all())
        )
        context["assigned_characters"] = assigned_characters
        context["characters"] = (
            Character.objects.filter(created_by=self.request.user)
            .exclude(id__in=self.object.npc.all())
            .exclude(id__in=assigned_characters.values_list("id", flat=True))
        )
        return context


class AddPlotNpcView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["pk"])
        character = get_object_or_404(Character, id=kwargs["character_pk"])

        if character.created_by_id != request.user.id:
            raise PermissionDenied()

        clone = character.clone(plot=plot_element.plot)
        plot_element.npc.add(clone)
        return JsonResponse({"status": "ok"})


class AssignPlotNpcView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=kwargs["pk"])
        character = get_object_or_404(Character, id=kwargs["character_pk"])

        if character.plot_campaign_id != plot_element.plot_id:
            raise PermissionDenied()
        if character.created_by_id != request.user.id:
            raise PermissionDenied()

        plot_element.npc.add(character)
        return JsonResponse({"status": "ok"})


class DeletePlotNpcView(View):
    def post(self, request, *args, **kwargs):
        plot_element = get_object_or_404(PlotElement, id=self.kwargs["plot_element_pk"])
        character = get_object_or_404(Character, id=self.kwargs["pk"])

        if character.created_by_id != request.user.id:
            raise PermissionDenied()

        plot_element.npc.remove(character)
        if (
            character.plot_campaign_id == plot_element.plot_id
            and not character.plotelement_set.exists()
        ):
            character.delete()
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
