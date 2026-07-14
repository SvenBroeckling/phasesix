from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from characters.models import Character, CharacterTemplate, Pronoun


class CharacterTemplateInline(TabularInline):
    model = CharacterTemplate


@admin.register(Pronoun)
class PronounAdmin(ModelAdmin):
    list_display = (
        "nominative_de",
        "nominative_en",
        "dative_de",
        "dative_en",
        "possessive_de",
        "possessive_en",
        "copula_verb_de",
        "copula_verb_en",
    )
    search_fields = ("nominative_de", "nominative_en", "dative_de", "dative_en")
    fieldsets = [(None, {"fields": (("nominative_de", "nominative_en"), ("dative_de", "dative_en"), ("possessive_de", "possessive_en"), ("copula_verb_de", "copula_verb_en"))})]


@admin.register(Character)
class CharacterAdmin(ModelAdmin):
    list_display = (
        "name",
        "created_by",
        "pronoun",
        "plot",
        "campaign",
        "npc_campaign",
        "may_appear_on_start_page",
    )
    list_editable = ("may_appear_on_start_page",)
    list_filter = "campaign", "extensions", "plot", "npc_campaign", "created_by"
    search_fields = ("name",)
    inlines = [CharacterTemplateInline]
    filter_horizontal = ("extensions",)
    fieldsets = [
        (None, {"fields": ("name", "slug", "description", ("pronoun", "lineage", "currency_map"), "extensions", ("campaign", "npc_campaign", "plot"), "may_appear_on_start_page")}),
        (_("Character values"), {"fields": (("size", "weight", "date_of_birth"), ("entity", "attitude", "grace", "reputation"), ("health", "boost", "arcana"), ("base_stress", "stress"), ("bonus_dice_used", "destiny_dice_used", "rerolls_used"), "latest_initiative")}),
        (_("Horror"), {"fields": (("quirks_gained", "quirks_healed"),), "classes": ("collapse",)}),
        (_("Images"), {"fields": ("image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y"), "backdrop_image", ("backdrop_copyright", "backdrop_copyright_url"), ("backdrop_image_focal_x", "backdrop_image_focal_y")), "classes": ("collapse",)}),
        (_("Ownership"), {"fields": (("created_by", "is_favorite", "cloned_from"),), "classes": ("collapse",)}),
    ]
