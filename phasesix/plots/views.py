from django.urls import reverse
from django.views.generic import TemplateView, ListView, CreateView

from plots.forms import PlotForm
from plots.models import Plot


class PlotEditorView(TemplateView):
    template_name = "plots/plot_editor.html"


class PlotListView(ListView):
    model = Plot
    template_name = "plots/plot_list.html"


class XhrCreatePlotView(CreateView):
    model = Plot
    template_name = "plots/create_plot.html"
    form_class = PlotForm

    def get_success_url(self):
        return reverse("plots:plot_editor", kwargs={"pk": self.object.pk})
