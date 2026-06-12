from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from portal.views import ProfileView


class ProfileEssentialCharacterContextTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Mock()
        self.profile = Mock(user=self.user)

    def get_context(self, world_identifier):
        request = self.factory.get("/portal/profile/sven")
        request.user = self.user
        request.world = SimpleNamespace(
            extension=SimpleNamespace(identifier=world_identifier)
        )
        view = ProfileView()
        view.setup(request)
        view.object = self.profile
        with (
            patch("portal.views.ProfileSettingsForm"),
            patch("portal.views.EssentialCharacter.objects") as objects,
        ):
            characters = objects.filter.return_value
            characters.pc.return_value = ["essential-pc"]
            characters.npc.return_value = ["essential-npc"]
            context = view.get_context_data()
        return context, objects

    def test_tirakan_profile_includes_essential_characters(self):
        context, objects = self.get_context("tirakan")

        objects.filter.assert_called_once_with(created_by=self.user)
        self.assertEqual(context["essential_pc_characters"], ["essential-pc"])
        self.assertEqual(context["essential_npc_characters"], ["essential-npc"])

    def test_other_world_profile_excludes_essential_characters(self):
        context, objects = self.get_context("nexus")

        objects.filter.assert_not_called()
        self.assertEqual(
            context["essential_pc_characters"],
            objects.none.return_value.pc.return_value,
        )
        self.assertEqual(
            context["essential_npc_characters"],
            objects.none.return_value.npc.return_value,
        )
