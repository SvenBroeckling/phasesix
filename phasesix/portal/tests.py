from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from portal.models import Profile
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


class ImageFocalPointHelperTests(SimpleTestCase):
    def test_center_crop_uses_focal_point(self):
        profile = Profile(image_focal_x=25, image_focal_y=75)

        self.assertEqual(profile.get_image_crop(), "25% 75%")
        self.assertEqual(profile.get_image_crop("top"), "top")

    def test_independent_image_field_uses_its_focal_point(self):
        profile = Profile(backdrop_image_focal_x=10, backdrop_image_focal_y=90)

        self.assertEqual(profile.get_image_crop(field_name="backdrop_image"), "10% 90%")


class ImageFocalPointTests(TestCase):
    image = SimpleUploadedFile(
        "focus.gif",
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02D\x01\x00;",
        content_type="image/gif",
    )

    def setUp(self):
        self.staff = User.objects.create_user("staff", is_staff=True)
        self.user = User.objects.create_user("user")
        self.profile = Profile.objects.get(user=self.staff)
        self.profile.image = self.image
        self.profile.save()
        self.url = reverse("portal:update_image_focal_point")
        self.payload = {
            "app_label": "portal",
            "model": "profile",
            "pk": self.profile.pk,
            "field_name": "image",
            "x": 25,
            "y": 75,
        }

    def test_staff_can_update_image_focal_point(self):
        self.client.force_login(self.staff)

        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.get_image_crop(), "25% 75%")

    def test_non_staff_cannot_update_image_focal_point(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 403)

    def test_invalid_focal_point_is_rejected(self):
        self.client.force_login(self.staff)
        self.payload["x"] = 101

        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 400)
