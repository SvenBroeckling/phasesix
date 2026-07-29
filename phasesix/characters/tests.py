from base64 import b64encode
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse

from armory.models import CurrencyMap, Item, ItemType
from characters.forms import AddCharacterToStartPageForm
from characters.models import Character, CharacterItem, CharacterRecipe, Pronoun
from characters.openai import CharacterLeadImageService
from characters.views import ChooseCharacterRulesetView, CreateCharacterInfoView
from portal.templatetags.portal_extras import create_character_url
from potions.models import (
    Recipe,
    RecipeCategory,
    RecipeDifficulty,
    RecipeIngredient,
    RecipeIngredientUnit,
)
from rules.models import Extension, Lineage
from worlds.models import World


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


class CharacterCreationInfoTests(SimpleTestCase):
    def test_pronoun_help_is_available_for_the_pronoun_field(self):
        context = CreateCharacterInfoView().pronoun_info("")

        self.assertTrue(context["title"])
        self.assertTrue(context["description"])

    def test_entity_help_explains_empty_selection(self):
        context = CreateCharacterInfoView().entity_info("")

        self.assertTrue(context["title"])
        self.assertTrue(context["description"])


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


class CharacterStartPageImageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "test")
        self.user = User.objects.create_user("user")
        self.currency_map = CurrencyMap.objects.create(name="Coins")
        self.pronoun = Pronoun.objects.create(
            nominative="they",
            dative="them",
            possessive="their",
            copula_verb="are",
        )
        self.lineage = Lineage.objects.create(name="Human")
        self.character = Character.objects.create(
            name="Jasmin Keller",
            slug="jasmin-keller",
            pronoun=self.pronoun,
            lineage=self.lineage,
            currency_map=self.currency_map,
            created_by=self.admin,
            image=SimpleUploadedFile(
                "jasmin.gif",
                b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
                b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
                b"\x00\x02\x02D\x01\x00;",
                content_type="image/gif",
            ),
        )
        self.world = World.objects.create(name="Tirakan", brand_name="Tirakan")
        self.url = reverse(
            "characters:add_to_start_page", kwargs={"slug": self.character.slug}
        )

    def test_only_superusers_can_open_start_page_action(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_action_creates_a_lead_image_for_the_selected_world(self):
        self.client.force_login(self.admin)

        with patch("characters.views.CharacterLeadImageService") as service:
            response = self.client.post(self.url, {"world": self.world.pk})

        self.assertRedirects(response, self.character.get_absolute_url())
        service.assert_called_once_with(character=self.character, world=self.world)
        service.return_value.create.assert_called_once_with()

    def test_inactive_default_world_is_available_for_the_start_page(self):
        default_world = World.objects.create(
            name="PhaseSix",
            brand_name="PhaseSix",
            is_active=False,
            is_default=True,
        )

        form = AddCharacterToStartPageForm()

        self.assertIn(default_world, form.fields["world"].queryset)

    @override_settings(OPENAI_API_KEY="test-key")
    def test_service_saves_transparent_openai_image_as_world_lead_image(self):
        png = b"\x89PNG\r\n\x1a\ntransparent-image"
        response = SimpleNamespace(
            data=[SimpleNamespace(b64_json=b64encode(png).decode())]
        )

        with patch("characters.openai.OpenAI") as openai:
            openai.return_value.images.edit.return_value = response
            lead_image = CharacterLeadImageService(self.character, self.world).create()

        self.assertEqual(lead_image.world, self.world)
        self.assertEqual(lead_image.character, self.character)
        self.assertEqual(lead_image.image.read(), png)
        self.assertEqual(
            openai.return_value.images.edit.call_args.kwargs["background"],
            "transparent",
        )
        image_upload = openai.return_value.images.edit.call_args.kwargs["image"]
        self.assertEqual(image_upload[0], "jasmin.gif")
        self.assertEqual(image_upload[1], self.character.image.read())
