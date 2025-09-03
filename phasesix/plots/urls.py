from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import PlotEditorView, PlotListView, XhrCreatePlotView

app_name = "plots"

urlpatterns = [
    path("", staff_member_required(PlotListView.as_view()), name="list_plots"),
    path(
        "create", staff_member_required(XhrCreatePlotView.as_view()), name="create_plot"
    ),
    path(
        "editor/<int:pk>",
        staff_member_required(PlotEditorView.as_view()),
        name="plot_editor",
    ),
]
