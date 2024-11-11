from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from characters.models import Character, CharacterTemplate


class CharacterTemplateInline(TabularInline):
    model = CharacterTemplate


class CharacterAdmin(ModelAdmin):
    list_display = (
        "name",
        "may_appear_on_start_page",
        "created_by",
        "campaign",
        "npc_campaign",
        "reputation",
    )
    list_editable = "may_appear_on_start_page", "campaign", "npc_campaign"
    list_filter = "campaign", "extensions", "npc_campaign", "created_by"
    search_fields = ("name",)
    inlines = [CharacterTemplateInline]


admin.site.register(Character, CharacterAdmin)
