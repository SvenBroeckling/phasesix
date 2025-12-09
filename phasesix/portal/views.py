from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.db.models.functions import Trunc, Length
from django.shortcuts import redirect
from django.templatetags.static import static
from django.views.generic import TemplateView, DetailView

from campaigns.models import Roll, Campaign
from characters.models import Character
from portal.forms import ProfileSettingsForm
from portal.models import Profile
from worlds.models import WikiPage, WorldLeadImage, World


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
