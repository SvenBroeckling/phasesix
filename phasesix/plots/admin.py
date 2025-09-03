from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from plots.models import Plot, PlotElement


class PlotElementInline(StackedInline):
    model = PlotElement


@admin.register(Plot)
class PlotAdmin(ModelAdmin):
    inlines = [PlotElementInline]
