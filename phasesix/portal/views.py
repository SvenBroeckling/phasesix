from math import ceil

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q, Count
from django.db.models.functions import Trunc, Length
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.views.generic.edit import FormView
from django_registration.backends.activation.views import (
    ActivationView as BaseActivationView,
)
from django_registration.backends.activation.views import (
    RegistrationView as BaseRegistrationView,
)

from campaigns.models import Roll, Campaign
from characters.models import Character
from characters.utils import is_tirakan_world
from essential_characters.models import EssentialCharacter
from portal.forms import ProfileSettingsForm
from portal.email import activation_url, email_brand_context, send_templated_email
from portal.models import Profile
from worlds.models import WikiPage, WorldLeadImage, World


class RegistrationView(BaseRegistrationView):
    """Preserve a safe on-site destination in an activation email."""

    def get_next_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ""

    def get_email_context(self, activation_key):
        context = super().get_email_context(activation_key)
        context["next"] = self.get_next_url()
        context.update(email_brand_context(self.request))
        context["activation_url"] = activation_url(
            self.request, activation_key, context["next"]
        )
        return context

    def send_activation_email(self, user):
        activation_key = self.get_activation_key(user)
        context = self.get_email_context(activation_key)
        context["user"] = user
        subject = render_to_string(
            self.email_subject_template, context=context, request=self.request
        )
        send_templated_email(
            "".join(subject.splitlines()),
            self.email_body_template,
            "django_registration/activation_email_body.html",
            context,
            [user.email],
        )

    def register(self, form):
        user = super().register(form)
        self.request.session["registration_pending_user_id"] = user.pk
        self.request.session["registration_email_sent_at"] = timezone.now().timestamp()
        return user


class ActivationView(BaseActivationView):
    """Activate, sign in, and continue to a safe requested destination."""

    def get_next_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ""

    def get_activation_data(self, request):
        data = super().get_activation_data(request)
        data["next"] = self.get_next_url()
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.get_next_url()
        lead_images = WorldLeadImage.objects.all()
        if self.request.world is not None:
            lead_images = lead_images.filter(world=self.request.world)
        context["lead_image"] = lead_images.order_by("?").first()
        return context

    def activate(self, form):
        user = super().activate(form)
        login(self.request, user)
        return user

    def get_success_url(self, user=None):
        return self.get_next_url() or super().get_success_url(user)


class ActivationCompleteView(TemplateView):
    template_name = "django_registration/activation_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead_images = WorldLeadImage.objects.all()
        if self.request.world is not None:
            lead_images = lead_images.filter(world=self.request.world)
        context["lead_image"] = lead_images.order_by("?").first()
        return context


class PasswordResetView(BasePasswordResetView):
    email_template_name = "registration/password_reset_email.html"
    html_email_template_name = "registration/password_reset_email_html.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        form.save(
            domain_override=self.request.get_host(),
            use_https=self.request.is_secure(),
            from_email=self.from_email,
            email_template_name=self.email_template_name,
            html_email_template_name=self.html_email_template_name,
            subject_template_name=self.subject_template_name,
            token_generator=self.token_generator,
            extra_email_context=email_brand_context(self.request),
        )
        return FormView.form_valid(self, form)


class RegistrationCompleteView(TemplateView):
    template_name = "django_registration/registration_complete.html"
    resend_cooldown_seconds = 30

    def get_pending_user(self):
        user_id = self.request.session.get("registration_pending_user_id")
        if not user_id:
            return None
        try:
            return User.objects.get(pk=user_id, is_active=False)
        except User.DoesNotExist:
            return None

    def get_resend_remaining_seconds(self):
        sent_at = self.request.session.get("registration_email_sent_at")
        if sent_at is None:
            return 0
        elapsed = timezone.now().timestamp() - float(sent_at)
        return max(0, ceil(self.resend_cooldown_seconds - elapsed))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead_images = WorldLeadImage.objects.all()
        if self.request.world is not None:
            lead_images = lead_images.filter(world=self.request.world)
        context["lead_image"] = lead_images.order_by("?").first()
        context["can_resend_activation_email"] = self.get_pending_user() is not None
        context["resend_remaining_seconds"] = self.get_resend_remaining_seconds()
        context["resend_countdown_template"] = _(
            "You can request another email in %(seconds)s seconds."
        )
        return context

    def post(self, request, *args, **kwargs):
        user = self.get_pending_user()
        if user is None:
            return HttpResponseRedirect(request.path)

        remaining_seconds = self.get_resend_remaining_seconds()
        if remaining_seconds:
            return self.resend_response(remaining_seconds, status=429)

        registration_view = RegistrationView()
        registration_view.setup(request)
        registration_view.send_activation_email(user)
        request.session["registration_email_sent_at"] = timezone.now().timestamp()
        return self.resend_response(self.resend_cooldown_seconds)

    def resend_response(self, remaining_seconds, status=200):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"remaining_seconds": remaining_seconds}, status=status)
        if status == 200:
            messages.success(self.request, _("A new activation email has been sent."))
        else:
            messages.info(
                self.request,
                _("Please wait before requesting another activation email."),
            )
        return HttpResponseRedirect(self.request.path)


class UpdateImageFocalPointView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()

        content_type = get_object_or_404(
            ContentType,
            app_label=request.POST.get("app_label"),
            model=request.POST.get("model"),
        )
        model = content_type.model_class()
        if model is None:
            return JsonResponse({"error": "Unsupported model."}, status=400)
        obj = get_object_or_404(model, pk=request.POST.get("pk"))
        field_name = request.POST.get("field_name", "image")

        try:
            image_field = model._meta.get_field(field_name)
            model._meta.get_field(f"{field_name}_focal_x")
            model._meta.get_field(f"{field_name}_focal_y")
            x = int(request.POST.get("x"))
            y = int(request.POST.get("y"))
        except (models.FieldDoesNotExist, TypeError, ValueError):
            return JsonResponse({"error": "Unsupported image field."}, status=400)

        if not isinstance(image_field, models.ImageField) or not getattr(
            obj, field_name, None
        ):
            return JsonResponse({"error": "Unsupported image field."}, status=400)
        if not 0 <= x <= 100 or not 0 <= y <= 100:
            return JsonResponse({"error": "Invalid focal point."}, status=400)

        setattr(obj, f"{field_name}_focal_x", x)
        setattr(obj, f"{field_name}_focal_y", y)
        obj.save(update_fields=[f"{field_name}_focal_x", f"{field_name}_focal_y"])
        return JsonResponse({"x": x, "y": y})


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_characters(self):
        context = {}
        characters = Character.objects.filter(image__isnull=False)

        lead_images = WorldLeadImage.objects.all()

        if self.request.world is not None:
            characters = characters.filter(extensions=self.request.world.extension)
            lead_images = lead_images.filter(world=self.request.world)
        if self.request.user.is_authenticated:
            characters = characters.filter(
                created_by=self.request.user, npc_campaign__isnull=True
            ).order_by("-is_favorite", "modified_at")
        else:
            characters = characters.filter(may_appear_on_start_page=True).order_by("?")

        context["characters"] = characters[:3]
        try:
            context["lead_image"] = lead_images.order_by("?").first()
        except WorldLeadImage.DoesNotExist:
            context["lead_image"] = None
        return context

    def get_context_campaigns(self):
        context = {}
        campaigns = Campaign.objects.filter(image__isnull=False)
        if self.request.world is not None:
            campaigns = campaigns.filter(world_extension=self.request.world.extension)

        if self.request.user.is_authenticated:
            campaigns = campaigns.filter(created_by=self.request.user).order_by(
                "-created_at"
            )
        else:
            campaigns = campaigns.filter(may_appear_on_start_page=True).order_by("?")
        context["campaigns"] = campaigns[:3]
        return context

    def get_context_worlds(self):
        context = {}
        if not self.request.world:
            context["worlds"] = World.objects.filter(is_active=True)
        return context

    def get_context_wiki_pages(self):
        context = {}
        if self.request.world is not None:
            context["wiki_pages"] = (
                WikiPage.objects.annotate(text_len=Length("text_de"))
                .filter(world=self.request.world, text_len__gte=30)
                .order_by("?")[:3]
            )
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_context_characters())
        context.update(self.get_context_worlds())
        context.update(self.get_context_campaigns())
        context.update(self.get_context_wiki_pages())

        if self.request.world:
            world = self.request.world
            context["world"] = world
            context["may_edit"] = world.may_edit(self.request.user)
        else:
            context["world"] = None
            context["may_edit"] = False

        return context


class SidebarSearchView(TemplateView):
    template_name = "portal/sidebar/search.html"


class XhrSearchResultsView(TemplateView):
    template_name = "portal/sidebar/search_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        search_descriptions = self.request.GET.get("search_descriptions", "off")

        if query:
            if search_descriptions == "on":
                characters = Character.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )
                campaigns = Campaign.objects.filter(
                    Q(name__icontains=query) | Q(abstract__icontains=query)
                )
                wiki_pages = WikiPage.objects.filter(
                    Q(name_en__icontains=query)
                    | Q(name_de__icontains=query)
                    | Q(text_en__icontains=query)
                    | Q(text_de__icontains=query)
                )
            else:
                characters = Character.objects.filter(Q(name__icontains=query))
                campaigns = Campaign.objects.filter(Q(name__icontains=query))
                wiki_pages = WikiPage.objects.filter(
                    Q(name_de__icontains=query) | Q(name_en__icontains=query)
                )

            if self.request.world:
                wiki_pages = wiki_pages.filter(Q(world=self.request.world))
                characters = characters.filter(extensions=self.request.world.extension)
                campaigns = campaigns.filter(
                    world_extension=self.request.world.extension
                )

            context["wiki_pages"] = wiki_pages
            context["characters"] = characters
            context["campaigns"] = campaigns

        return context


class ProfileView(DetailView):
    template_name = "portal/profile.html"
    model = Profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.request.user == self.object.user
        context["form"] = ProfileSettingsForm(instance=self.object)
        essential_characters = EssentialCharacter.objects.none()
        if is_tirakan_world(self.request.world):
            essential_characters = EssentialCharacter.objects.filter(
                created_by=self.object.user
            )
        context["essential_pc_characters"] = essential_characters.pc()
        context["essential_npc_characters"] = essential_characters.npc()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.user == request.user:
            raise PermissionDenied("You are not the owner of this profile.")
        form = ProfileSettingsForm(request.POST, request.FILES, instance=self.object)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile settings saved.")
            return redirect(self.object.get_absolute_url())
        else:
            context = self.get_context_data(form=form)
            return self.render_to_response(context)


class YearlyWrapUpView(TemplateView):
    template_name = "portal/yearly_wrapup.html"

    def get_most_played(self, qs):
        res = []
        for mp in (
            qs.values("character")
            .annotate(total=Count("character"))
            .order_by("-total")[:3]
        ):
            character = Character.objects.get(id=mp["character"])
            days = self._get_days(qs, character)
            res.append((character, mp["total"], days))
        return res

    def get_played_campaigns(self, qs):
        return [
            (Campaign.objects.get(id=mp["campaign"]), mp["total"])
            for mp in qs.exclude(campaign__isnull=True)
            .values("campaign")
            .annotate(total=Count("campaign"))
            .order_by("-total")
        ]

    def get_highest_roll(self, qs, mode):
        try:
            return qs.order_by(f"-{mode}")[0]
        except IndexError:
            return None

    def get_platform_stats(self):
        qs = Roll.objects.filter(
            created_at__year=self.kwargs["year"], character__isnull=False
        )
        return {
            "platform_crit_count": self.get_highest_roll(qs, "crit_count"),
            "platform_exploded_dice_count": self.get_highest_roll(
                qs, "exploded_dice_count"
            ),
            "platform_successes_count": self.get_highest_roll(qs, "successes_count"),
            "platform_fails_count": self.get_highest_roll(qs, "fails_count"),
            "platform_highest_single_roll": self.get_highest_roll(
                qs, "highest_single_roll"
            ),
            "platform_total_sum": self.get_highest_roll(qs, "total_sum"),
            "platform_roll_count": qs.count(),
            "platform_days": self._get_days(qs),
            "platform_characters_created": Character.objects.filter(
                created_at__year=self.kwargs["year"]
            ).count(),
            "platform_campaigns_created": Campaign.objects.filter(
                created_at__year=self.kwargs["year"]
            ).count(),
        }

    def get_user_stats(self):
        qs = Roll.objects.filter(
            character__created_by=User.objects.get(id=self.kwargs["pk"]),
            created_at__year=self.kwargs["year"],
        )
        return {
            "wrapup_user": User.objects.get(id=self.kwargs["pk"]),
            "year": self.kwargs["year"],
            "qs": qs,
            "most_played": self.get_most_played(qs),
            "played_campaigns": self.get_played_campaigns(qs),
            "roll_crit_count": self.get_highest_roll(qs, "crit_count"),
            "roll_exploded_dice_count": self.get_highest_roll(
                qs, "exploded_dice_count"
            ),
            "roll_successes_count": self.get_highest_roll(qs, "successes_count"),
            "roll_fails_count": self.get_highest_roll(qs, "fails_count"),
            "roll_highest_single_roll": self.get_highest_roll(
                qs, "highest_single_roll"
            ),
            "roll_total_sum": self.get_highest_roll(qs, "total_sum"),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_stats())
        context.update(self.get_platform_stats())
        if self.kwargs["year"] == 2023:
            context["header_image"] = static("img/wrapup_2023.png")
        elif self.kwargs["year"] == 2024:
            context["header_image"] = static("img/wrapup_2024.png")
        else:
            context["header_image"] = static("img/wrapup_2025.png")
        return context

    def _get_days(self, qs, character=None):
        if character:
            qs = qs.filter(character=character)

        return (
            qs.annotate(created_at_day=Trunc("created_at", "day"))
            .values("created_at_day")
            .annotate(total=Count("created_at_day"))
            .count()
        )
