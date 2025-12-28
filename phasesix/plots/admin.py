from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from plots.models import Plot, PlotElement, Location, Handout


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    pass


@admin.register(Handout)
class HandoutAdmin(ModelAdmin):
    pass


class PlotElementInline(StackedInline):
    model = PlotElement


@admin.register(Plot)
class PlotAdmin(ModelAdmin):
    list_display = ["name", "world_extension", "cloned_from", "campaign"]
    inlines = [PlotElementInline]


@admin.register(PlotElement)
class PlotElementAdmin(ModelAdmin):
    list_display = ["name", "plot", "parent"]
