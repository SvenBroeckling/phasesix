from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.template import Context
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve, reverse

from armory.models import CurrencyMap, Item, ItemType
from characters.models import Character, CharacterItem, CharacterRecipe, Pronoun
from characters.views import ChooseCharacterRulesetView
from portal.templatetags.portal_extras import create_character_url
from potions.models import (
    Recipe,
    RecipeCategory,
    RecipeDifficulty,
    RecipeIngredient,
    RecipeIngredientUnit,
)
from rules.models import Extension, Lineage


class CharacterRulesetSelectionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @staticmethod
    def world(identifier="tirakan", fixed_epoch=True, has_fixed_extensions=True):
        epoch = SimpleNamespace(id=20) if fixed_epoch else None
        fixed_extensions = Mock()
        fixed_extensions.exists.return_value = has_fixed_extensions
        extension = SimpleNamespace(
            id=10,
            identifier=identifier,
            fixed_epoch=epoch,
            fixed_extensions=fixed_extensions,
        )
        return SimpleNamespace(
            extension=extension,
            brand_name="Tirakan",
            dns_domain_name="tr.localhost",
            description_1="",
            brand_logo=SimpleNamespace(url="/static/logo.png"),
            scss_file_static="/static/theme/tirakan.scss",
        )

    def test_shared_creation_link_opens_ruleset_choice_for_tirakan(self):
        request = self.factory.get("/")
        request.world = self.world()

        url = create_character_url(Context({"request": request}))

        self.assertEqual(url, reverse("characters:choose_character_ruleset"))

    def test_shared_creation_link_keeps_direct_wizard_for_other_worlds(self):
        request = self.factory.get("/")
        request.world = self.world(identifier="nexus")

        url = create_character_url(Context({"request": request}))

        self.assertEqual(
            url,
            reverse(
                "characters:create_character_data",
                kwargs={"world_pk": 10, "epoch_pk": 20},
            ),
        )

    def test_ruleset_choice_links_to_both_character_wizards(self):
        request = self.factory.get(reverse("characters:choose_character_ruleset"))
        request.world = self.world()
        request.user = AnonymousUser()
        request.resolver_match = resolve(request.path)

        response = ChooseCharacterRulesetView.as_view()(request)
        response.render()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("essential_characters:create"))
        self.assertEqual(
            response.context_data["phasesix_creation_url"],
            reverse(
                "characters:create_character_data",
                kwargs={"world_pk": 10, "epoch_pk": 20},
            ),
        )
        self.assertContains(response, response.context_data["phasesix_creation_url"])

    def test_ruleset_choice_redirects_for_other_worlds(self):
        request = self.factory.get(reverse("characters:choose_character_ruleset"))
        request.world = self.world(identifier="nexus")

        response = ChooseCharacterRulesetView.as_view()(request)

        self.assertRedirects(
            response,
            reverse(
                "characters:create_character_data",
                kwargs={"world_pk": 10, "epoch_pk": 20},
            ),
            fetch_redirect_response=False,
        )


class CharacterRecipeMechanicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="recipe-user")
        self.currency_map = CurrencyMap.objects.create(name="Coins")
        self.pronoun = Pronoun.objects.create(
            nominative="they",
            dative="them",
            possessive="their",
            copula_verb="are",
        )
        self.extension = Extension.objects.create(
            name="Potions",
            identifier="potions",
        )
        self.lineage = Lineage.objects.create(name="Human")
        self.lineage.extensions.add(self.extension)
        self.character = Character.objects.create(
            name="Alchemist",
            pronoun=self.pronoun,
            lineage=self.lineage,
            currency_map=self.currency_map,
            created_by=self.user,
        )
        self.character.extensions.add(self.extension)

        item_type = ItemType.objects.create(name="Herbs")
        self.herb = Item.objects.create(
            name="Moon Herb",
            type=item_type,
            weight=0,
            price=0,
        )
        self.herb.extensions.add(self.extension)
        self.difficulty = RecipeDifficulty.objects.create(name="Simple")
        self.category = RecipeCategory.objects.create(name="Potions")
        self.recipe = Recipe.objects.create(
            category=self.category,
            difficulty=self.difficulty,
            name="Healing Draught",
            expected_amount=2,
        )
        self.recipe.extensions.add(self.extension)
        self.unit = RecipeIngredientUnit.objects.create(name="bundle")
        self.ingredient = RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.herb,
            quantity=3,
            unit=self.unit,
        )
        self.character_recipe = CharacterRecipe.objects.create(
            character=self.character,
            recipe=self.recipe,
        )
        self.client.force_login(self.user)

    def test_brew_consumes_ingredients_and_tracks_prepared_amount(self):
        CharacterItem.objects.create(
            character=self.character,
            item=self.herb,
            quantity=4,
        )

        response = self.client.post(
            reverse(
                "characters:recipe_action",
                kwargs={"pk": self.character_recipe.id, "mode": "brew"},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.character_recipe.refresh_from_db()
        self.assertEqual(self.character_recipe.prepared_amount, 2)
        self.assertEqual(
            self.character.characteritem_set.get(item=self.herb).quantity,
            1,
        )

    def test_brew_fails_when_ingredients_are_missing(self):
        CharacterItem.objects.create(
            character=self.character,
            item=self.herb,
            quantity=2,
        )

        response = self.client.post(
            reverse(
                "characters:recipe_action",
                kwargs={"pk": self.character_recipe.id, "mode": "brew"},
            )
        )

        self.assertEqual(response.status_code, 400)
        self.character_recipe.refresh_from_db()
        self.assertEqual(self.character_recipe.prepared_amount, 0)
        self.assertEqual(
            self.character.characteritem_set.get(item=self.herb).quantity,
            2,
        )

    def test_recipe_ingredient_actions_track_character_resources(self):
        add_url = reverse(
            "characters:recipe_ingredient_action",
            kwargs={
                "pk": self.character_recipe.id,
                "mode": "add_ingredient",
                "ingredient_pk": self.ingredient.id,
            },
        )
        remove_url = reverse(
            "characters:recipe_ingredient_action",
            kwargs={
                "pk": self.character_recipe.id,
                "mode": "remove_ingredient",
                "ingredient_pk": self.ingredient.id,
            },
        )

        self.client.post(add_url)
        self.client.post(add_url)
        self.client.post(remove_url)

        self.assertEqual(
            self.character.characteritem_set.get(item=self.herb).quantity,
            1,
        )

    def test_recipe_ingredient_bulk_actions_fill_and_empty_requirement(self):
        CharacterItem.objects.create(
            character=self.character,
            item=self.herb,
            quantity=1,
        )
        fill_url = reverse(
            "characters:recipe_ingredient_action",
            kwargs={
                "pk": self.character_recipe.id,
                "mode": "fill_ingredient",
                "ingredient_pk": self.ingredient.id,
            },
        )
        empty_url = reverse(
            "characters:recipe_ingredient_action",
            kwargs={
                "pk": self.character_recipe.id,
                "mode": "empty_ingredient",
                "ingredient_pk": self.ingredient.id,
            },
        )

        self.client.post(fill_url)

        self.assertEqual(
            self.character.characteritem_set.get(item=self.herb).quantity,
            3,
        )

        self.client.post(fill_url)
        self.client.post(empty_url)

        self.assertFalse(
            self.character.characteritem_set.filter(item=self.herb).exists()
        )

    def test_character_recipe_related_manager_exposes_summary_methods(self):
        self.character_recipe.prepared_amount = 2
        self.character_recipe.save()
        CharacterItem.objects.create(
            character=self.character,
            item=self.herb,
            quantity=3,
        )

        self.assertEqual(
            self.character.characterrecipe_set.with_recipe_details().count(), 1
        )
        self.assertEqual(self.character.characterrecipe_set.prepared_recipe_amount(), 2)
        self.assertEqual(self.character.characterrecipe_set.brewable_recipe_count(), 1)

    def test_use_prepared_recipe_spends_one_prepared_amount(self):
        self.character_recipe.prepared_amount = 2
        self.character_recipe.save()

        response = self.client.post(
            reverse(
                "characters:recipe_action",
                kwargs={"pk": self.character_recipe.id, "mode": "use"},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.character_recipe.refresh_from_db()
        self.assertEqual(self.character_recipe.prepared_amount, 1)
