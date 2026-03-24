from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from campaigns.models import Campaign, Roll
from plots.models import Plot


@admin.register(Roll)
class RollAdmin(ModelAdmin):
    search_fields = ("header",)
    list_display = (
        "campaign",
        "character",
        "header",
        "roll_string",
        "results_csv",
        "modifier",
        "minimum_roll",
    )
    list_filter = ("campaign", "character", "header")


class PlotInline(StackedInline):
    model = Plot
    fk_name = "campaign"
    extra = 0
    max_num = 1
    readonly_fields = ("id",)


@admin.register(Campaign)
class CampaignAdmin(ModelAdmin):
    inlines = [PlotInline]
