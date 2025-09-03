from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView

from plots.forms import PlotForm, PlotElementForm
from plots.models import Plot, PlotElement


class PlotEditorView(DetailView):
    template_name = "plots/plot_editor.html"
    model = Plot


class PlotListView(ListView):
    model = Plot
    template_name = "plots/plot_list.html"


class XhrCreatePlotView(CreateView):
    model = Plot
    template_name = "plots/create_plot.html"
    form_class = PlotForm
    extra_context = {
        "post_url": reverse_lazy("plots:create_plot"),
    }

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.object.pk})


class XhrUpdatePlotView(UpdateView):
    model = Plot
    template_name = "plots/create_plot.html"
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
    template_name = "plots/create_plot.html"
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
