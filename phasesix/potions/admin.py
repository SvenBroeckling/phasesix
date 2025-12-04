from django.contrib import admin
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
    pass


@admin.register(RecipeIngredientUnit)
class RecipeIngredientUnitAdmin(ModelAdmin):
    pass


class RecipeIngredientInline(TabularInline):
    model = RecipeIngredient
    autocomplete_fields = ("ingredient",)
    extra = 0


@admin.register(RecipeCategory)
class RecipeCategoryAdmin(ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "category", "expected_amount")
    filter_horizontal = ("extensions",)
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    inlines = [RecipeIngredientInline]
