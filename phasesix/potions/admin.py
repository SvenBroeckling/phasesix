from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from potions.models import (
    Recipe,
    RecipeDifficulty,
    RecipeIngredientUnit,
    RecipeIngredient,
    RecipeCategory,
)


@admin.register(RecipeDifficulty)
class RecipeDifficultyAdmin(ModelAdmin):
    list_display = ("name_de", "name_en")
    search_fields = ("name_de", "name_en")
    fieldsets = [(None, {"fields": (("name_de", "name_en"),)})]


@admin.register(RecipeIngredientUnit)
class RecipeIngredientUnitAdmin(ModelAdmin):
    list_display = ("name_de", "name_en")
    search_fields = ("name_de", "name_en")
    fieldsets = [(None, {"fields": (("name_de", "name_en"),)})]


class RecipeIngredientInline(TabularInline):
    model = RecipeIngredient
    autocomplete_fields = ("ingredient",)
    extra = 0


@admin.register(RecipeCategory)
class RecipeCategoryAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "ordering")
    list_editable = ("ordering",)
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    fieldsets = [(None, {"fields": (("name_de", "name_en"), ("description_de", "description_en"), "ordering")})]


@admin.register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "category", "difficulty", "expected_amount")
    filter_horizontal = ("extensions",)
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    list_editable = ("category", "difficulty", "expected_amount")
    list_filter = ("category", "difficulty", "extensions", "is_homebrew")
    inlines = [RecipeIngredientInline]
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("description_de", "description_en"), ("category", "difficulty", "expected_amount"), "extensions")}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), "created_by", ("homebrew_campaign", "homebrew_character")), "classes": ("collapse",)}),
    ]
