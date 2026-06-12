from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.template import Context
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from characters.views import ChooseCharacterRulesetView
from portal.templatetags.portal_extras import create_character_url


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
