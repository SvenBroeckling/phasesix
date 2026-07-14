from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from pantheon.models import Entity, PriestAction, PriestActionRoll, EntityCategory


@admin.register(Entity)
class EntityAdmin(ModelAdmin):
    list_display = "name_de", "name_en", "wiki_page"
    filter_horizontal = ("extensions",)
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("short_name_de", "short_name_en"), ("description_de", "description_en"), ("category", "wiki_page", "ordering"), "extensions")}),
        (_("Image"), {"fields": ("image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y")), "classes": ("collapse",)}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), "created_by", ("homebrew_campaign", "homebrew_character")), "classes": ("collapse",)}),
    ]


class PriestActionRollInline(TabularInline):
    model = PriestActionRoll


@admin.register(PriestAction)
class PriestActionAdmin(ModelAdmin):
    list_display = "name_de", "name_en", "grace_cost", "work_type"
    list_editable = "grace_cost", "work_type"
    inlines = [PriestActionRollInline]
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("grace_cost", "work_type"), ("rules_de", "rules_en"), ("quote", "quote_author"))}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), "created_by", ("homebrew_campaign", "homebrew_character")), "classes": ("collapse",)}),
    ]


admin.site.register(EntityCategory, ModelAdmin)
admin.site.register(PriestActionRoll, ModelAdmin)
