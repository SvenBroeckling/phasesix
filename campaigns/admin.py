from django.contrib import admin
from unfold.admin import ModelAdmin

from campaigns.models import Campaign, Roll


class RollAdmin(ModelAdmin):
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


admin.site.register(Campaign)
admin.site.register(Roll, RollAdmin)
