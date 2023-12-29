from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.db.models.functions import Trunc
from django.views.generic import TemplateView

from campaigns.models import Roll, Campaign
from characters.models import Character
from worlds.models import WikiPage


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
                context["wiki_pages"] = WikiPage.objects.filter(
                    Q(name_en__icontains=query)
                    | Q(name_de__icontains=query)
                    | Q(text_en__icontains=query)
                    | Q(text_de__icontains=query)
                )
            else:
                context["wiki_pages"] = WikiPage.objects.filter(
                    Q(name_de__icontains=query) | Q(name_en__icontains=query)
                )
            if self.request.user.is_authenticated:
                context["characters"] = Character.objects.filter(
                    Q(created_by=self.request.user) | Q(created_by__isnull=True)
                ).filter(name__icontains=query)
        return context


class ProfileView(TemplateView):
    template_name = "portal/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.request.user
        return context


class YearlyWrapUpView(TemplateView):
    template_name = "portal/yearly_wrapup.html"
    YEAR = 2023

    def get_most_played(self, qs):
        res = []
        for mp in (
            qs.values("character")
            .annotate(total=Count("character"))
            .order_by("-total")[:3]
        ):
            character = Character.objects.get(id=mp["character"])
            days = (
                qs.filter(character=character)
                .annotate(created_at_day=Trunc("created_at", "day"))
                .values("created_at_day")
                .annotate(total=Count("created_at_day"))
                .count()
            )
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Roll.objects.filter(
            character__created_by=User.objects.get(id=self.kwargs["pk"]),
            created_at__year=self.YEAR,
        )
        context.update(
            {
                "year": self.YEAR,
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
        )
        return context
