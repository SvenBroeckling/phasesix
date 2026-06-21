from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from armory.models import Item, ItemType
from portal.models import Profile
from potions.models import (
    Recipe,
    RecipeCategory,
    RecipeDifficulty,
    RecipeIngredient,
    RecipeIngredientUnit,
)
from rules.models import Extension


class DumpApiViewRecipeTests(TestCase):
    def test_recipes_dump_uses_recursive_natural_keys_and_extension_filtering(self):
        user = User.objects.create_user(username="dump-user")
        Profile.objects.create(user=user, slug="dump-user", api_key="secret")

        core = Extension.objects.create(
            name_de="Kern",
            name_en="Core",
            identifier="core",
            is_mandatory=True,
            fa_icon_latex="core-icon",
        )
        alchemy = Extension.objects.create(
            name_de="Alchemie",
            name_en="Alchemy",
            identifier="alchemy",
            fa_icon_latex="alchemy-icon",
        )
        other = Extension.objects.create(
            name_de="Andere",
            name_en="Other",
            identifier="other",
            type="w",
        )

        category = RecipeCategory.objects.create(
            name_de="Traenke",
            name_en="Potions",
            description_de="Gebräue",
            description_en="Brewed concoctions",
        )
        difficulty = RecipeDifficulty.objects.create(
            name_de="Einfach",
            name_en="Simple",
        )
        unit = RecipeIngredientUnit.objects.create(
            name_de="Prise",
            name_en="Pinch",
        )
        item_type = ItemType.objects.create(
            name_de="Kraut",
            name_en="Herb",
            description_de="Zutat",
            description_en="Ingredient",
        )
        ingredient = Item.objects.create(
            name_de="Mondkraut",
            name_en="Moon herb",
            description_de="Silbrige Blätter",
            description_en="Silver leaves",
            type=item_type,
            weight=Decimal("0.10"),
            price=Decimal("3.00"),
        )
        ingredient.extensions.add(core)

        recipe = Recipe.objects.create(
            category=category,
            difficulty=difficulty,
            name_de="Heiltrank",
            name_en="Healing potion",
            description_de="Heilt Wunden",
            description_en="Restores health",
            expected_amount=2,
        )
        recipe.extensions.add(alchemy)
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            quantity=3,
            unit=unit,
        )

        filtered_recipe = Recipe.objects.create(
            category=category,
            difficulty=difficulty,
            name_de="Schattenelixier",
            name_en="Shadow elixir",
        )
        filtered_recipe.extensions.add(other)

        response = self.client.get(
            reverse("api:dump_api", kwargs={"model": "recipes"}),
            HTTP_AUTHORIZATION="secret",
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "name": "Potions",
                    "description": "Brewed concoctions",
                    "objects": [
                        {
                            "extensions": [
                                {
                                    "name": "Alchemy",
                                    "identifier": "alchemy",
                                    "icon": "alchemy-icon",
                                }
                            ],
                            "name": "Healing potion",
                            "description": "Restores health",
                            "category": "Potions",
                            "difficulty": "Simple",
                            "expected_amount": 2,
                            "ingredients": [
                                {
                                    "ingredient": "Moon herb",
                                    "ingredient_type": "Herb",
                                    "ingredient_description": "Silver leaves",
                                    "quantity": 3,
                                    "unit": "Pinch",
                                }
                            ],
                        }
                    ],
                }
            ],
        )
