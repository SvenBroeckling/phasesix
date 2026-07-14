from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.forms import modelform_factory
from django.template import Context
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from campaigns.models import Campaign
from campaigns.templatetags.campaign_extras import create_campaign_url
from campaigns.views import (
    CampaignDetailView,
    ChooseCampaignRulesetView,
    CreateCampaignDataView,
    CreateCampaignView,
    campaign_creation_ruleset,
)


class CampaignRulesetSelectionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @staticmethod
    def world(identifier="tirakan"):
        fixed_extensions = Mock()
        fixed_extensions.exists.return_value = True
        extension = SimpleNamespace(
            id=10,
            identifier=identifier,
            fixed_epoch=SimpleNamespace(id=20),
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

        self.assertEqual(
            create_campaign_url(Context({"request": request})),
            reverse("campaigns:choose_ruleset"),
        )

    def test_shared_creation_link_keeps_campaign_start_for_other_worlds(self):
        request = self.factory.get("/")
        request.world = self.world(identifier="nexus")

        self.assertEqual(
            create_campaign_url(Context({"request": request})),
            reverse("campaigns:create"),
        )

    def test_campaign_start_redirects_to_ruleset_choice_for_tirakan(self):
        request = self.factory.get(reverse("campaigns:create"))
        request.world = self.world()

        response = CreateCampaignView.as_view()(request)

        self.assertRedirects(
            response,
            reverse("campaigns:choose_ruleset"),
            fetch_redirect_response=False,
        )

    def test_ruleset_choice_links_to_both_campaign_flows(self):
        request = self.factory.get(reverse("campaigns:choose_ruleset"))
        request.world = self.world()
        request.user = AnonymousUser()
        request.resolver_match = resolve(request.path)

        response = ChooseCampaignRulesetView.as_view()(request)
        response.render()

        self.assertContains(
            response,
            f"{reverse('campaigns:create')}?ruleset={Campaign.RULESET_ESSENTIAL}",
        )
        self.assertContains(
            response,
            f"{reverse('campaigns:create')}?ruleset={Campaign.RULESET_PHASESIX}",
        )

    def test_ruleset_choice_redirects_for_other_worlds(self):
        request = self.factory.get(reverse("campaigns:choose_ruleset"))
        request.world = self.world(identifier="nexus")

        response = ChooseCampaignRulesetView.as_view()(request)

        self.assertRedirects(
            response,
            reverse("campaigns:create"),
            fetch_redirect_response=False,
        )

    def test_essential_ruleset_is_only_selected_on_tirakan(self):
        tirakan_request = self.factory.get("/", {"ruleset": Campaign.RULESET_ESSENTIAL})
        tirakan_request.world = self.world()
        nexus_request = self.factory.get("/", {"ruleset": Campaign.RULESET_ESSENTIAL})
        nexus_request.world = self.world(identifier="nexus")

        self.assertEqual(
            campaign_creation_ruleset(tirakan_request), Campaign.RULESET_ESSENTIAL
        )
        self.assertEqual(
            campaign_creation_ruleset(nexus_request), Campaign.RULESET_PHASESIX
        )

    def test_campaign_data_form_does_not_expose_ruleset(self):
        self.assertNotIn("ruleset", CreateCampaignDataView.fields)

    def test_campaign_data_form_hides_visibility_and_seed_money(self):
        self.assertNotIn("character_visibility", CreateCampaignDataView.fields)
        self.assertNotIn("npc_visibility", CreateCampaignDataView.fields)
        self.assertNotIn("foe_visibility", CreateCampaignDataView.fields)
        self.assertNotIn("seed_money", CreateCampaignDataView.fields)

    def test_campaign_visibility_defaults_to_gm_only(self):
        for field_name in (
            "character_visibility",
            "npc_visibility",
            "foe_visibility",
            "game_log_visibility",
        ):
            self.assertEqual(Campaign._meta.get_field(field_name).default, "G")

    def test_essential_campaign_form_hides_currency_and_career_points(self):
        request = self.factory.get("/", {"ruleset": Campaign.RULESET_ESSENTIAL})
        request.world = self.world()
        view = CreateCampaignDataView()
        view.request = request
        view.kwargs = {"world_pk": 10, "epoch_pk": 20}
        view.object = None
        form_class = modelform_factory(Campaign, fields=CreateCampaignDataView.fields)

        form = view.get_form(form_class)

        self.assertNotIn("currency_map", form.fields)
        self.assertNotIn("starting_template_points", form.fields)

    def test_tirakan_phasesix_campaign_form_keeps_career_points(self):
        request = self.factory.get("/", {"ruleset": Campaign.RULESET_PHASESIX})
        request.world = self.world()
        view = CreateCampaignDataView()
        view.request = request
        view.kwargs = {"world_pk": 10, "epoch_pk": 20}
        view.object = None
        form_class = modelform_factory(Campaign, fields=CreateCampaignDataView.fields)

        form = view.get_form(form_class)

        self.assertNotIn("currency_map", form.fields)
        self.assertIn("starting_template_points", form.fields)

    def test_campaign_invite_link_uses_the_request_host(self):
        request = self.factory.get("/", secure=True, HTTP_HOST="tr.localhost:8000")
        request.user = AnonymousUser()
        campaign = SimpleNamespace(
            slug="la-dame-blanche-2",
            campaign_hash="invite-hash",
            may_edit=Mock(return_value=False),
        )
        view = CampaignDetailView()
        view.request = request
        view.kwargs = {}
        view.object = campaign

        context = view.get_context_data()

        self.assertEqual(
            context["invite_link"],
            "https://tr.localhost:8000/campaigns/la-dame-blanche-2/invite/invite-hash",
        )
