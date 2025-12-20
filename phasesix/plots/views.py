from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from plots.forms import PlotForm, PlotElementForm, HandoutForm, LocationForm
from plots.models import Plot, PlotElement, Handout, Location


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
