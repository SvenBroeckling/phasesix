from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core import mail, signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_registration.backends.activation import REGISTRATION_SALT

from portal.models import Profile
from portal.email import activation_url, email_brand_context
from portal.views import (
    ActivationView,
    ActivationCompleteView,
    PasswordResetView,
    ProfileView,
    RegistrationCompleteView,
)


class IndexTitleTests(TestCase):
    def test_default_domain_index_title_does_not_include_none(self):
        response = self.client.get(reverse("index"), HTTP_HOST="phasesix.org")

        self.assertContains(response, "<title>Phase Six</title>", html=True)
        self.assertNotContains(response, " - None")


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


class RegistrationCompleteViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request_with_session(self):
        request = self.factory.post("/accounts/register/complete/")
        SessionMiddleware(lambda request: None).process_request(request)
        return request

    def test_registration_complete_uses_an_image_from_the_active_world(self):
        request = self.factory.get("/accounts/register/complete/")
        SessionMiddleware(lambda request: None).process_request(request)
        request.world = SimpleNamespace()
        lead_image = SimpleNamespace()
        view = RegistrationCompleteView()
        view.setup(request)

        with (
            patch("portal.views.User.objects") as user_objects,
            patch("portal.views.WorldLeadImage.objects") as objects,
        ):
            images = objects.all.return_value
            images.filter.return_value.order_by.return_value.first.return_value = (
                lead_image
            )
            user_objects.get.side_effect = User.DoesNotExist

            context = view.get_context_data()

        images.filter.assert_called_once_with(world=request.world)
        self.assertEqual(context["lead_image"], lead_image)

    def test_resend_activation_email_starts_a_new_cooldown(self):
        request = self.request_with_session()
        request.session["registration_email_sent_at"] = 0
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        view = RegistrationCompleteView()
        view.setup(request)

        with (
            patch.object(view, "get_pending_user", return_value=Mock()),
            patch("portal.views.RegistrationView.send_activation_email") as send_email,
        ):
            response = view.post(request)

        self.assertEqual(response.status_code, 200)
        send_email.assert_called_once()
        self.assertLessEqual(
            timezone.now().timestamp() - request.session["registration_email_sent_at"],
            1,
        )

    def test_resend_activation_email_respects_the_cooldown(self):
        request = self.request_with_session()
        request.session["registration_email_sent_at"] = timezone.now().timestamp()
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        view = RegistrationCompleteView()
        view.setup(request)

        with (
            patch.object(view, "get_pending_user", return_value=Mock()),
            patch("portal.views.RegistrationView.send_activation_email") as send_email,
        ):
            response = view.post(request)

        self.assertEqual(response.status_code, 429)
        send_email.assert_not_called()


class ActivationViewTests(SimpleTestCase):
    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_activation_page_uses_an_image_from_the_active_world(self):
        request = RequestFactory().get("/accounts/activate/?activation_key=token")
        request.world = SimpleNamespace()
        lead_image = SimpleNamespace()
        view = ActivationView()
        view.setup(request)

        with patch("portal.views.WorldLeadImage.objects") as objects:
            images = objects.all.return_value
            images.filter.return_value.order_by.return_value.first.return_value = (
                lead_image
            )

            context = view.get_context_data()

        images.filter.assert_called_once_with(world=request.world)
        self.assertEqual(context["lead_image"], lead_image)


class ActivationCompleteViewTests(SimpleTestCase):
    def test_activation_complete_uses_an_image_from_the_active_world(self):
        request = RequestFactory().get("/accounts/activate/complete/")
        request.world = SimpleNamespace()
        lead_image = SimpleNamespace()
        view = ActivationCompleteView()
        view.setup(request)

        with patch("portal.views.WorldLeadImage.objects") as objects:
            images = objects.all.return_value
            images.filter.return_value.order_by.return_value.first.return_value = (
                lead_image
            )

            context = view.get_context_data()

        images.filter.assert_called_once_with(world=request.world)
        self.assertEqual(context["lead_image"], lead_image)


class EmailBrandingTests(SimpleTestCase):
    @override_settings(ALLOWED_HOSTS=["tirakans-reiche.de"])
    def test_email_branding_and_activation_url_use_the_request_world_domain(self):
        request = RequestFactory().get(
            "/accounts/register/", secure=True, HTTP_HOST="tirakans-reiche.de"
        )
        request.world = SimpleNamespace(
            brand_name="Tirakan", extension=SimpleNamespace(identifier="tirakan")
        )

        context = email_brand_context(request)

        self.assertEqual(context["email_brand_name"], "Tirakan")
        self.assertEqual(context["email_theme"]["primary"], "#9f784f")
        self.assertEqual(
            activation_url(request, "activation-token", "/characters/new/"),
            "https://tirakans-reiche.de/accounts/activate/?activation_key=activation-token&next=%2Fcharacters%2Fnew%2F",
        )

    @override_settings(ALLOWED_HOSTS=["tirakans-reiche.de"])
    def test_password_reset_uses_the_request_domain_and_html_template_once(self):
        request = RequestFactory().post(
            "/accounts/password_reset/", secure=True, HTTP_HOST="tirakans-reiche.de"
        )
        request.world = SimpleNamespace(
            brand_name="Tirakan", extension=SimpleNamespace(identifier="tirakan")
        )
        view = PasswordResetView()
        view.setup(request)
        form = Mock()

        response = view.form_valid(form)

        self.assertEqual(response.status_code, 302)
        form.save.assert_called_once()
        self.assertEqual(
            form.save.call_args.kwargs["domain_override"], "tirakans-reiche.de"
        )
        self.assertEqual(
            form.save.call_args.kwargs["html_email_template_name"],
            "registration/password_reset_email_html.html",
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


class RegistrationContinuationTests(TestCase):
    target_url = "/characters/create/invited-character/"

    def test_registration_email_preserves_safe_next_url(self):
        registration_url = reverse("django_registration_register")
        response = self.client.post(
            f"{registration_url}?next={self.target_url}",
            {
                "username": "new-invitee",
                "email": "new-invitee@example.com",
                "password1": "secure-password-123",
                "password2": "secure-password-123",
                "email2": "",
                "next": self.target_url,
            },
            HTTP_HOST="phasesix.org",
        )

        self.assertRedirects(
            response,
            reverse("django_registration_complete"),
            fetch_redirect_response=False,
        )
        self.assertIn(
            "&next=%2Fcharacters%2Fcreate%2Finvited-character%2F",
            mail.outbox[0].body,
        )

    def test_activation_signs_in_and_redirects_to_safe_next_url(self):
        user = User.objects.create_user("new-invitee", is_active=False)
        activation_key = signing.dumps(user.username, salt=REGISTRATION_SALT)

        response = self.client.post(
            reverse("django_registration_activate"),
            {"activation_key": activation_key, "next": self.target_url},
            HTTP_HOST="phasesix.org",
        )

        self.assertRedirects(response, self.target_url, fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(str(user.pk), self.client.session["_auth_user_id"])
