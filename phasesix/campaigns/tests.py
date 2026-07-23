from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser
from django.forms import modelform_factory
from django.template import Context
from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from campaigns.models import Campaign
from campaigns.foundry import FoundryModule
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

    def test_campaign_data_form_hides_seed_money(self):
        self.assertNotIn("seed_money", CreateCampaignDataView.fields)

    def test_campaign_visibility_fields_are_removed(self):
        campaign_fields = {field.name for field in Campaign._meta.get_fields()}

        self.assertNotIn("character_visibility", campaign_fields)
        self.assertNotIn("game_log_visibility", campaign_fields)
        self.assertNotIn("plot_visibility", campaign_fields)
        self.assertNotIn("npc_visibility", campaign_fields)
        self.assertNotIn("foe_visibility", campaign_fields)

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

    def test_campaign_detail_exposes_a_foundry_manifest_for_attached_plots(self):
        request = self.factory.get("/", secure=True, HTTP_HOST="tr.localhost:8000")
        request.user = AnonymousUser()
        campaign = SimpleNamespace(
            slug="la-dame-blanche-2",
            campaign_hash="invite-hash",
            foundry_token=uuid4(),
            plot=SimpleNamespace(),
            may_edit=Mock(return_value=True),
        )
        view = CampaignDetailView()
        view.request = request
        view.kwargs = {}
        view.object = campaign

        context = view.get_context_data()

        self.assertIn("/foundry/", context["foundry_manifest_link"])
        self.assertTrue(context["foundry_manifest_link"].endswith("/module.json"))

    def test_foundry_module_manifest_declares_v14_actor_type(self):
        campaign = SimpleNamespace(
            pk=42,
            name="The Glass Road",
            plot=SimpleNamespace(name="The Glass Road", export_version=7),
        )

        manifest = FoundryModule(
            campaign,
            "https://example.test/module.json",
            "https://example.test/download.zip",
        ).manifest()

        self.assertEqual(manifest["version"], "1.0.7")
        self.assertEqual(manifest["title"], "The Glass Road")
        self.assertEqual(manifest["compatibility"]["minimum"], "14")
        self.assertIn("phasesix", manifest["documentTypes"]["Actor"])

    def test_empty_homebrew_notice_is_shown_to_anonymous_visitors(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        empty_relation = SimpleNamespace(exists=lambda: False, all=lambda: [])
        campaign = SimpleNamespace(
            homebrew_armory_item_set=empty_relation,
            homebrew_armory_weapon_set=empty_relation,
            homebrew_armory_riotgear_set=empty_relation,
            homebrew_magic_basespell_set=empty_relation,
            homebrew_worlds_language_set=empty_relation,
            homebrew_horror_quirk_set=empty_relation,
            homebrew_rules_template_set=empty_relation,
            homebrew_rules_foe_set=empty_relation,
        )

        content = get_template("campaigns/fragments/homebrew.html").render(
            {"request": request, "object": campaign, "may_edit": False}
        )

        self.assertIn("No homebrew exists for this campaign yet.", content)

    def test_attached_plot_shows_npc_list_to_anonymous_visitors(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        empty_relation = SimpleNamespace(exists=lambda: False, all=lambda: [])
        campaign = SimpleNamespace(
            id=1,
            plot=SimpleNamespace(id=1, player_abstract="", root_elements=[]),
            ruleset=Campaign.RULESET_PHASESIX,
            character_set=empty_relation,
            essentialcharacter_set=empty_relation,
        )

        content = get_template("campaigns/fragments/dramaturgy.html").render(
            {
                "request": request,
                "object": campaign,
                "may_edit": False,
            }
        )

        self.assertIn('data-sidebar-right-url="/campaigns/sidebar/1/npc"', content)

    def test_character_cast_is_shown_to_anonymous_visitors(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        empty_relation = SimpleNamespace(exists=lambda: True, all=lambda: [])
        campaign = SimpleNamespace(
            id=1,
            plot=None,
            ruleset=Campaign.RULESET_PHASESIX,
            character_set=empty_relation,
            essentialcharacter_set=empty_relation,
        )

        content = get_template("campaigns/fragments/dramaturgy.html").render(
            {
                "request": request,
                "object": campaign,
                "may_edit": False,
            }
        )

        self.assertIn("campaign-section-heading", content)

    def test_attached_plot_loads_for_anonymous_visitors(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        campaign = SimpleNamespace(
            id=1,
            plot=SimpleNamespace(id=1, root_elements=[]),
        )

        content = get_template("campaigns/fragments/dramaturgy.html").render(
            {
                "request": request,
                "object": campaign,
                "may_edit": False,
            }
        )

        self.assertIn('hx-get="/plots/xhr_campaign_plot_view/1/1"', content)
        self.assertIn('hx-trigger="load"', content)
