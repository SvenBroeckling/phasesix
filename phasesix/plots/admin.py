from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, StackedInline

from plots.models import Plot, PlotElement, Location, Handout


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    fieldsets = [(None, {"fields": ("name", "description", "image", ("image_focal_x", "image_focal_y"))})]


@admin.register(Handout)
class HandoutAdmin(ModelAdmin):
    fieldsets = [(None, {"fields": ("name", "description", "image", ("image_focal_x", "image_focal_y"))})]


class PlotElementInline(StackedInline):
    model = PlotElement


@admin.register(Plot)
class PlotAdmin(ModelAdmin):
    list_display = ["name", "world_extension", "cloned_from", "campaign"]
    inlines = [PlotElementInline]
    filter_horizontal = ("extensions",)
    fieldsets = [
        (None, {"fields": ("name", ("ruleset", "language"), ("epoch_extension", "world_extension"), "extensions", ("campaign", "created_by", "cloned_from"))}),
        (_("Content"), {"fields": ("player_abstract", "gm_description")}),
        (_("Image"), {"fields": ("image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y")), "classes": ("collapse",)}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), ("homebrew_campaign", "homebrew_character")), "classes": ("collapse",)}),
    ]


@admin.register(PlotElement)
class PlotElementAdmin(ModelAdmin):
    list_display = ["name", "plot", "parent"]
    filter_horizontal = ("npc", "essential_npc", "foes", "handouts", "locations")
    fieldsets = [(None, {"fields": (("plot", "parent", "ordering"), "name", "gm_notes", "player_summary", "npc", "essential_npc", "foes", "handouts", "locations")})]
