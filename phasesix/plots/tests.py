from types import SimpleNamespace

from django.test import SimpleTestCase
from django.urls import Resolver404, resolve, reverse

from plots.models import PlotElement


class PlotElementVisibilityTests(SimpleTestCase):
    def setUp(self):
        self.element = PlotElement(name="Ambush")
        self.campaign = SimpleNamespace(
            may_edit=lambda user: user == "gm",
            is_player=lambda user: user == "player",
        )

    def test_visibility_fields_default_to_gm_only(self):
        for field_name in (
            "player_summary_visibility",
            "gm_notes_visibility",
            "npc_visibility",
            "handouts_visibility",
            "foes_visibility",
            "locations_visibility",
        ):
            self.assertEqual(PlotElement._meta.get_field(field_name).default, "G")

    def test_visibility_allows_the_configured_audience(self):
        self.element.npc_visibility = "P"

        self.assertTrue(self.element.may_view("gm", self.campaign, "npc_visibility"))
        self.assertTrue(
            self.element.may_view("player", self.campaign, "npc_visibility")
        )
        self.assertFalse(
            self.element.may_view("visitor", self.campaign, "npc_visibility")
        )

    def test_visibility_control_url_resolves(self):
        self.assertEqual(
            reverse(
                "plots:plot_element_visibility",
                kwargs={
                    "pk": 1,
                    "visibility_field": "npc_visibility",
                    "action": "cycle",
                },
            ),
            "/plots/plot_element/1/visibility/npc_visibility/cycle",
        )

    def test_dedicated_plot_editor_routes_are_unavailable(self):
        with self.assertRaises(Resolver404):
            resolve("/plots/")
        with self.assertRaises(Resolver404):
            resolve("/plots/1/editor")


# Create your tests here.
