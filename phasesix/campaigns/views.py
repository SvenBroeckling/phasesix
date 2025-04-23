from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    TemplateView,
    FormView,
    UpdateView,
)

from campaigns.forms import (
    CampaignSettingsIntegrationForm,
    CampaignSettingsGameForm,
    CampaignSettingsVisibilityForm,
)
from campaigns.models import Campaign, Foe, Roll
from characters.forms import CreateCharacterExtensionsForm
from characters.models import Character
from rules.models import Extension
from worlds.models import WikiPage


class CreateCampaignView(TemplateView):
    template_name = "campaigns/create_campaign.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extensions"] = (
            Extension.objects.exclude(is_mandatory=True)
            .exclude(type__in=["e", "x"])
            .exclude(is_active=False)
        )
        return context


class CreateCampaignEpochView(TemplateView):
    template_name = "campaigns/create_campaign_epoch.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["world_pk"] = self.kwargs["world_pk"]
        context["extensions"] = (
            Extension.objects.exclude(is_mandatory=True)
            .exclude(type__in=["x", "w"])
            .exclude(is_active=False)
        )
        return context


class CreateCampaignExtensionsView(FormView):
    template_name = "campaigns/create_campaign_extensions.html"
    form_class = CreateCharacterExtensionsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["world_pk"] = self.kwargs["world_pk"]
        context["epoch_pk"] = self.kwargs["epoch_pk"]
        context["extensions"] = (
            Extension.objects.exclude(is_mandatory=True)
            .exclude(type__in=["e", "w"])
            .exclude(is_active=False)
        )
        return context


class CreateCampaignDataView(CreateView):
    model = Campaign
    fields = (
        "name",
        "abstract",
        "character_visibility",
        "foe_visibility",
        "currency_map",
        "seed_money",
        "starting_template_points",
    )

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.epoch = Extension.objects.get(pk=self.kwargs["epoch_pk"])
        obj.world = Extension.objects.get(pk=self.kwargs["world_pk"])
        obj.save()

        extensions = Extension.objects.filter(
            pk__in=self.request.GET.getlist("extensions")
        )
        if obj.world.fixed_extensions.exists():
            extensions = obj.world.fixed_extensions.all()
        obj.extensions.set(extensions)
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class CampaignDetailView(DetailView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_join"] = self.kwargs.get("hash", "") == self.object.campaign_hash
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class XhrDiceLogView(ListView):
    template_name = "campaigns/dice_log.html"
    paginate_by = 8

    def get_queryset(self):
        campaign = Campaign.objects.get(id=self.kwargs["pk"])
        return Roll.objects.filter(campaign=campaign)


class XhrCampaignFragmentView(DetailView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fragment_template"] = self.kwargs["fragment_template"]
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context

    def get_template_names(self):
        return ["campaigns/fragments/" + self.kwargs["fragment_template"] + ".html"]


class XhrSwitchCharacterNPCView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs["pk"])
        if campaign.may_edit(request.user):
            character = Character.objects.get(id=kwargs["character_pk"])
            character.switch_pc_npc_campaign()
        return JsonResponse({"status": "ok"})


class XhrRemoveCharacterView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs["pk"])
        if campaign.may_edit(request.user):
            character = Character.objects.get(id=kwargs["character_pk"])
            character.campaign = None
            character.npc_campaign = None
            character.save()
        return JsonResponse({"status": "ok"})


class XhrAddFoeToCampaignView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs["pk"])
        if campaign.may_edit(request.user):
            wiki_page = WikiPage.objects.get(id=kwargs["wiki_page_pk"])
            campaign.foe_set.create(wiki_page=wiki_page)
        return JsonResponse({"status": "ok"})


class XhrRemoveFoeView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs["pk"])
        if campaign.may_edit(request.user):
            campaign.foe_set.filter(id=kwargs["foe_pk"]).delete()
        return JsonResponse({"status": "ok"})


class XhrCampaignSettingsView(UpdateView):
    model = Campaign
    template_name = "campaigns/modals/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = self.kwargs["mode"]
        return context

    def get_form_class(self):
        if self.kwargs["mode"] == "integration":
            return CampaignSettingsIntegrationForm
        elif self.kwargs["mode"] == "game":
            return CampaignSettingsGameForm
        elif self.kwargs["mode"] == "visibility":
            return CampaignSettingsVisibilityForm
        else:
            raise Exception(f"Unknown mode: {self.kwargs['mode']}")


class BaseSidebarView(DetailView):
    def get_template_names(self):
        return ["campaigns/sidebar/" + self.kwargs["sidebar_template"] + ".html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context["may_edit"] = self.object.pc_or_npc_campaign.may_edit(
                self.request.user
            )
        except AttributeError:
            context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class XhrSidebarView(BaseSidebarView):
    model = Campaign


class XhrSettingsSidebarView(BaseSidebarView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SettingsForm(instance=self.object)
        return context


class XhrCharacterSidebarView(BaseSidebarView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.pc_or_npc_campaign.may_edit(self.request.user)
        return context


class XhrFoeSidebarView(BaseSidebarView):
    model = Foe


class XhrSearchFoeSidebarView(DetailView):
    template_name = "campaigns/sidebar/search_foe.html"
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.may_edit(self.request.user)
        wiki_pages = (
            WikiPage.objects.filter(
                Q(wikipagegamevalues__id__isnull=False)
                | Q(wikipagegameaction__id__isnull=False)
            )
            .filter(exclude_from_foe_search=False)
            .distinct()
        )

        if self.request.world_configuration is not None:
            wiki_pages = wiki_pages.filter(world=self.request.world_configuration.world)

        context["wiki_pages"] = wiki_pages
        return context


class XhrCampaignGameLogView(ListView):
    paginate_by = 20

    def get_queryset(self):
        return Roll.objects.filter(campaign_id=self.kwargs["campaign_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = Campaign.objects.get(id=self.kwargs["campaign_pk"])
        return context


class XhrCampaignStatisticsView(DetailView):
    template_name = "campaigns/statistics/roll_list.html"
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mode = self.kwargs["mode"]
        context["object_list"] = self.object.roll_set.order_by(f"-{mode}")[:5]
        return context


class XhrCampaignToggleFavoriteView(View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, pk=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied

        campaign.is_favorite = not campaign.is_favorite
        campaign.save()

        icon_class = "fas" if campaign.is_favorite else "far"
        template = f'<i class="{icon_class} fa-star fa-2x text-warning"></i>'
        return HttpResponse(template)
