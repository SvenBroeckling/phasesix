from django.contrib import admin
from django.utils.translation import gettext_lazy as _
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
    fieldsets = [
        (None, {"fields": (("campaign", "character"), "header", "description", ("roll_string", "modifier", "minimum_roll"), "results_csv")}),
        (_("Roll statistics"), {"fields": (("crit_count", "crit_sum"), ("exploded_dice_count", "exploded_dice_sum"), "highest_single_roll", ("successes_count", "successes_sum"), ("fails_count", "fails_sum"), "total_sum"), "classes": ("collapse",)}),
    ]


class PlotInline(StackedInline):
    model = Plot
    fk_name = "campaign"
    extra = 0
    max_num = 1
    readonly_fields = ("id",)


@admin.register(Campaign)
class CampaignAdmin(ModelAdmin):
    inlines = [PlotInline]
    list_display = ("name", "ruleset", "world_extension", "epoch_extension", "may_appear_on_start_page", "roll_on_site", "created_by")
    list_editable = ("ruleset", "may_appear_on_start_page", "roll_on_site")
    list_filter = ("ruleset", "world_extension", "epoch_extension", "may_appear_on_start_page", "roll_on_site")
    search_fields = ("name", "abstract")
    filter_horizontal = ("extensions", "forbidden_templates")
    fieldsets = [
        (None, {"fields": ("name", "slug", "ruleset", ("epoch_extension", "world_extension"), "extensions", "forbidden_templates", ("ingame_act_date", "may_appear_on_start_page"))}),
        (_("Campaign settings"), {"fields": (("starting_template_points", "seed_money", "currency_map"), "roll_on_site", ("foe_visibility", "npc_visibility", "game_log_visibility", "character_visibility"))}),
        (_("Integrations"), {"fields": (("discord_integration", "tale_spire_integration"), "discord_webhook_url"), "classes": ("collapse",)}),
        (_("Presentation"), {"fields": ("abstract", "image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y"), "backdrop_image", ("backdrop_copyright", "backdrop_copyright_url"), ("backdrop_image_focal_x", "backdrop_image_focal_y")), "classes": ("collapse",)}),
        (_("Ownership"), {"fields": (("created_by", "is_favorite", "cloned_from"),), "classes": ("collapse",)}),
    ]
