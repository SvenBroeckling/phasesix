from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
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
from campaigns.models import Campaign, CampaignFoe, Roll
from characters.forms import CreateCharacterExtensionsForm
from characters.models import Character
from plots.models import Plot, PlotElement, Handout, Location, _copy_field_file
from rules.models import Extension, Foe
from worlds.models import WikiPage


class CreateCampaignView(TemplateView):
    template_name = "campaigns/create_campaign_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            world_extension = self.request.world.extension
        except AttributeError:
            world_extension = None
        plots = Plot.objects.filter(
            cloned_from__isnull=True,
            campaign__isnull=True,
        )
        if world_extension:
            plots = plots.filter(world_extension=world_extension)
            if world_extension.fixed_epoch:
                plots = plots.filter(epoch_extension=world_extension.fixed_epoch)
        context["plots"] = plots.order_by("name")
        context["world_extension"] = world_extension
        if world_extension:
            if world_extension.fixed_epoch:
                if world_extension.fixed_extensions.exists():
                    context["own_plot_url"] = reverse(
                        "campaigns:create_data",
                        kwargs={
                            "world_pk": world_extension.id,
                            "epoch_pk": world_extension.fixed_epoch.id,
                        },
                    )
                else:
                    context["own_plot_url"] = reverse(
                        "campaigns:create_extensions",
                        kwargs={
                            "world_pk": world_extension.id,
                            "epoch_pk": world_extension.fixed_epoch.id,
                        },
                    )
            else:
                context["own_plot_url"] = reverse(
                    "campaigns:create_epoch",
                    kwargs={"world_pk": world_extension.id},
                )
        else:
            context["own_plot_url"] = reverse("campaigns:create_world")
        return context


class CreateCampaignWorldView(TemplateView):
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
        "ingame_act_date",
        "character_visibility",
        "npc_visibility",
        "foe_visibility",
        "currency_map",
        "seed_money",
        "starting_template_points",
    )

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.epoch_extension = Extension.objects.get(pk=self.kwargs["epoch_pk"])
        obj.world_extension = Extension.objects.get(pk=self.kwargs["world_pk"])
        plot_pk = self.request.GET.get("plot_pk")
        if plot_pk:
            plot = get_object_or_404(
                Plot.objects.filter(cloned_from__isnull=True, campaign__isnull=True),
                pk=plot_pk,
            )
            if (
                plot.world_extension_id != obj.world_extension_id
                or plot.epoch_extension_id != obj.epoch_extension_id
            ):
                form.add_error(
                    None,
                    _("Selected plot does not match the chosen world or epoch."),
                )
                return self.form_invalid(form)
            if plot.image:
                obj.image = _copy_field_file(plot.image)
        obj.save()

        extensions = Extension.objects.filter(
            pk__in=self.request.GET.getlist("extensions")
        )
        if obj.world_extension.fixed_extensions.exists():
            extensions = obj.world_extension.fixed_extensions.all()
        obj.extensions.set(extensions)
        if plot_pk:
            plot.clone(campaign=obj)
        else:
            plot = Plot.objects.create(
                name=obj.name,
                language=self.request.LANGUAGE_CODE,
                player_abstract=obj.abstract or "",
                gm_description="",
                epoch_extension=obj.epoch_extension,
                world_extension=obj.world_extension,
                created_by=self.request.user,
                campaign=obj,
            )
            plot.extensions.set(obj.extensions.all())
            PlotElement.objects.create(
                plot=plot,
                name=_("How to edit this plot"),
                gm_notes=_(
                    "Toggle the Edit plot switch, then use Add Element in the properties panel."
                ),
            )
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_initial(self):
        initial = super().get_initial()
        plot_pk = self.request.GET.get("plot_pk")
        if not plot_pk:
            return initial
        plot = get_object_or_404(
            Plot.objects.filter(cloned_from__isnull=True, campaign__isnull=True),
            pk=plot_pk,
        )
        initial.setdefault("name", plot.name)
        if plot.player_abstract:
            initial.setdefault("abstract", plot.player_abstract)
        elif plot.gm_description:
            initial.setdefault("abstract", plot.gm_description)
        return initial


class CampaignDetailView(DetailView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_join"] = self.kwargs.get("hash", "") == self.object.campaign_hash
        context["may_edit"] = self.object.may_edit(self.request.user)
        return context


class CloneCampaignView(View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, slug=kwargs["slug"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()

        clone = campaign.clone()
        messages.success(
            request,
            _(
                "Campaign cloned. You are now viewing the duplicate. Everything but player characters is copied."
            ),
        )
        return HttpResponseRedirect(clone.get_absolute_url())


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
        if self.kwargs["fragment_template"] == "dramaturgy":
            context["available_plots"] = Plot.objects.filter(
                world_extension=self.object.world_extension,
                epoch_extension=self.object.epoch_extension,
                cloned_from__isnull=True,
                campaign__isnull=True,
            ).order_by("name")
        return context

    def get_template_names(self):
        return ["campaigns/fragments/" + self.kwargs["fragment_template"] + ".html"]


class XhrCampaignPlotPreviewView(View):
    def get(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, id=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()
        plot = get_object_or_404(Plot, id=kwargs["plot_pk"])
        if plot.campaign_id and plot.campaign_id != campaign.id:
            raise PermissionDenied()
        return render(
            request,
            "campaigns/modals/plot_preview.html",
            {"campaign": campaign, "plot": plot},
        )


class XhrAssignCampaignPlotView(View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, id=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()
        plot = get_object_or_404(Plot, id=kwargs["plot_pk"])
        if plot.cloned_from_id or plot.campaign_id:
            raise PermissionDenied()
        existing_plot = Plot.objects.filter(campaign=campaign).first()
        if existing_plot:
            existing_plot.delete()
        plot.clone(campaign=campaign)
        return JsonResponse({"status": "ok"})


class XhrRemoveCampaignPlotView(View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, id=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()
        plot = Plot.objects.filter(campaign=campaign).first()
        if plot:
            Handout.objects.filter(plotelement__plot=plot).delete()
            Location.objects.filter(plotelement__plot=plot).delete()
            Character.objects.filter(plotelement__plot=plot).delete()
            plot.delete()
        return JsonResponse({"status": "ok"})


class XhrRemoveCampaignPlotModalView(View):
    def get(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, id=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()
        plot = Plot.objects.filter(campaign=campaign).first()
        return render(
            request,
            "campaigns/modals/remove_plot.html",
            {"campaign": campaign, "plot": plot},
        )


class XhrCloneCampaignModalView(View):
    def get(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, slug=kwargs["slug"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()
        return render(
            request,
            "campaigns/modals/clone_campaign.html",
            {"campaign": campaign},
        )


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
            foe = Foe.objects.get(id=kwargs["foe_pk"])
            campaign.campaignfoe_set.create(foe=foe)
        return JsonResponse({"status": "ok"})


class XhrRemoveFoeView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs["pk"])
        if campaign.may_edit(request.user):
            campaign.campaignfoe_set.filter(id=kwargs["foe_pk"]).delete()
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
        campaign = self.object.pc_or_npc_campaign
        if campaign is None and self.object.plot_id:
            campaign = self.object.plot.campaign
        context["campaign"] = campaign
        context["may_edit"] = (
            campaign.may_edit(self.request.user) if campaign else False
        )
        return context


class XhrFoeSidebarView(BaseSidebarView):
    model = CampaignFoe


class XhrPlotHandoutSidebarView(DetailView):
    model = Handout
    template_name = "campaigns/sidebar/handout.html"

    def get_queryset(self):
        return Handout.objects.filter(
            plotelement__plot__campaign_id=self.kwargs["campaign_pk"]
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = get_object_or_404(Campaign, id=self.kwargs["campaign_pk"])
        context["campaign"] = campaign
        context["may_edit"] = campaign.may_edit(self.request.user)
        return context


class XhrPlotLocationSidebarView(DetailView):
    model = Location
    template_name = "campaigns/sidebar/location.html"

    def get_queryset(self):
        return Location.objects.filter(
            plotelement__plot__campaign_id=self.kwargs["campaign_pk"]
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = get_object_or_404(Campaign, id=self.kwargs["campaign_pk"])
        context["campaign"] = campaign
        context["may_edit"] = campaign.may_edit(self.request.user)
        return context


class XhrPlotFoeSidebarView(DetailView):
    model = Foe
    template_name = "campaigns/sidebar/plot_foe.html"

    def get_queryset(self):
        return Foe.objects.filter(
            plotelement__plot__campaign_id=self.kwargs["campaign_pk"]
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = get_object_or_404(Campaign, id=self.kwargs["campaign_pk"])
        context["campaign"] = campaign
        context["may_edit"] = campaign.may_edit(self.request.user)
        return context


class XhrSearchFoeSidebarView(DetailView):
    template_name = "campaigns/sidebar/search_foe.html"
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["may_edit"] = self.object.may_edit(self.request.user)
        foes = Foe.objects.all()

        if self.request.world is not None:
            foes = foes.filter(extensions=self.request.world.extension)

        context["foes"] = foes.order_by("name_de")
        return context


class XhrSelectNPCView(DetailView):
    model = Campaign
    template_name = "campaigns/fragments/select_npc.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["characters"] = Character.objects.filter(
            created_by=self.request.user
        ).exclude(id__in=self.object.npc_set.all())
        context["campaign"] = self.object
        return context


class CloneNPCView(View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, pk=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()

        character = get_object_or_404(Character, pk=kwargs["character_pk"])
        character.clone(new_npc_campaign=campaign)
        return render(
            request,
            "campaigns/fragments/select_npc.html",
            {
                "characters": Character.objects.filter(
                    created_by=self.request.user
                ).exclude(id__in=campaign.npc_set.all()),
                "campaign": campaign,
            },
        )


class AssignNPCView(View):
    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, pk=kwargs["pk"])
        if not campaign.may_edit(request.user):
            raise PermissionDenied()

        character = get_object_or_404(Character, pk=kwargs["character_pk"])
        character.npc_campaign = campaign
        character.save()
        messages.success(request, _("NPC assigned to this campaign."))
        return render(
            request,
            "campaigns/fragments/select_npc.html",
            {
                "characters": Character.objects.filter(
                    created_by=self.request.user
                ).exclude(id__in=campaign.npc_set.all()),
                "campaign": campaign,
            },
        )


class XhrCampaignGameLogView(ListView):
    paginate_by = 20

    def get_queryset(self):
        return Roll.objects.filter(campaign_id=self.kwargs["campaign_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = Campaign.objects.get(id=self.kwargs["campaign_pk"])
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
