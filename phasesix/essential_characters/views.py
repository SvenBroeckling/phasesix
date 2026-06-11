from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView

from campaigns.models import Campaign
from plots.models import Plot
from .forms import EssentialCharacterForm
from .models import EssentialCharacter


class EssentialCharacterDetailView(DetailView):
    model = EssentialCharacter


class EssentialCharacterCreateView(LoginRequiredMixin, CreateView):
    model = EssentialCharacter
    form_class = EssentialCharacterForm
    template_name = "essential_characters/essentialcharacter_form.html"

    def get_campaign(self):
        campaign_id = self.request.GET.get("campaign")
        if not campaign_id:
            return None
        campaign = get_object_or_404(Campaign, pk=campaign_id, ruleset=Campaign.RULESET_ESSENTIAL)
        if campaign.world_extension.identifier != "tirakan":
            raise PermissionDenied()
        return campaign

    def get_plot(self):
        plot_id = self.request.GET.get("plot")
        return get_object_or_404(Plot, pk=plot_id, ruleset=Plot.RULESET_ESSENTIAL) if plot_id else None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(campaign=self.get_campaign(), plot=self.get_plot())
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class EssentialCharacterUpdateView(LoginRequiredMixin, UpdateView):
    model = EssentialCharacter
    form_class = EssentialCharacterForm
    template_name = "essential_characters/essentialcharacter_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().may_edit(request.user):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(campaign=self.object.campaign, plot=self.object.plot)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        assignments = self.object.essentialcharacterskill_set.select_related("skill")
        initial["skill_names"] = "\n".join(a.skill.name for a in assignments)
        initial["skill_ranks"] = "\n".join(str(a.rank) for a in assignments)
        return initial
