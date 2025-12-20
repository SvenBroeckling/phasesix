from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import (
    PlotEditorView,
    PlotListView,
    XhrCreatePlotView,
    XhrUpdatePlotView,
    XhrCreatePlotElementView,
    XhrUpdatePlotElementView,
    XhrCreateHandoutView,
    XhrCreateLocationView,
    XhrPlotFragmentView,
    XhrReorderPlotElementView,
)

app_name = "plots"

urlpatterns = [
    path("", staff_member_required(PlotListView.as_view()), name="list_plots"),
    path(
        "create", staff_member_required(XhrCreatePlotView.as_view()), name="create_plot"
    ),
    path(
        "<int:pk>/edit",
        staff_member_required(XhrUpdatePlotView.as_view()),
        name="update_plot",
    ),
    path(
        "<int:pk>/editor",
        staff_member_required(PlotEditorView.as_view()),
        name="plot_editor",
    ),
    path(
        "xhr_plot_fragment/<int:pk>/<fragment_template>",
        staff_member_required(XhrPlotFragmentView.as_view()),
        name="xhr_plot_fragment",
    ),
    path(
        "xhr_reorder_plot_element",
        staff_member_required(XhrReorderPlotElementView.as_view()),
        name="xhr_reorder_plot_element",
    ),
    # PlotElement
    path(
        "<int:plot_pk>/plot_element/create",
        staff_member_required(XhrCreatePlotElementView.as_view()),
        name="create_plot_element",
    ),
    path(
        "plot_element/<int:pk>/update",
        staff_member_required(XhrUpdatePlotElementView.as_view()),
        name="update_plot_element",
    ),
    # Handouts and Locations
    path(
        "<int:plot_element_pk>/handout/create",
        staff_member_required(XhrCreateHandoutView.as_view()),
        name="create_handout",
    ),
    path(
        "<int:plot_element_pk>/location/create",
        staff_member_required(XhrCreateLocationView.as_view()),
        name="create_location",
    ),
]
