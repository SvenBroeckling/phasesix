from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, TemplateView, FormView

from campaigns.forms import SettingsForm
from campaigns.models import Campaign
from characters.forms import CreateCharacterExtensionsForm
from characters.models import Character
from rules.models import Extension


class CampaignListView(ListView):
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Campaign.objects.all()
            return Campaign.objects.filter(created_by=user)


class CreateCampaignView(TemplateView):
    template_name = 'campaigns/create_campaign.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extensions'] = Extension.objects.exclude(
            is_mandatory=True).exclude(type__in=['e', 'x']).exclude(is_active=False)
        return context


class CreateCampaignEpochView(TemplateView):
    template_name = 'campaigns/create_campaign_epoch.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['world_pk'] = self.kwargs['world_pk']
        context['extensions'] = Extension.objects.exclude(
            is_mandatory=True).exclude(type__in=['x', 'w']).exclude(is_active=False)
        return context


class CreateCampaignExtensionsView(FormView):
    template_name = 'campaigns/create_campaign_extensions.html'
    form_class = CreateCharacterExtensionsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['world_pk'] = self.kwargs['world_pk']
        context['epoch_pk'] = self.kwargs['epoch_pk']
        context['extensions'] = Extension.objects.exclude(
            is_mandatory=True).exclude(type__in=['e', 'w']).exclude(is_active=False)
        return context


class CreateCampaignDataView(CreateView):
    model = Campaign
    fields = ('name', 'abstract', 'character_visibility', 'currency_map')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.epoch = Extension.objects.get(pk=self.kwargs['epoch_pk'])
        obj.world = Extension.objects.get(pk=self.kwargs['world_pk'])
        obj.save()
        obj.extensions.set(Extension.objects.filter(pk__in=self.request.GET.getlist('extensions')))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class CampaignDetailView(DetailView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['may_join'] = self.kwargs.get('hash', '') == self.object.campaign_hash
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context


class XhrCampaignFragmentView(DetailView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fragment_template'] = self.kwargs['fragment_template']
        context['may_edit'] = self.object.may_edit(self.request.user)
        return context

    def get_template_names(self):
        return ['campaigns/fragments/' + self.kwargs['fragment_template'] + '.html']


class SaveSettingsView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs['pk'])
        if campaign.may_edit(request.user):
            form = SettingsForm(request.POST, instance=campaign, files=request.FILES)
            if form.is_valid():
                form.save()
        return HttpResponseRedirect(campaign.get_absolute_url())


class XhrSwitchCharacterNPCView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs['pk'])
        if campaign.may_edit(request.user):
            character = Character.objects.get(id=kwargs['character_pk'])
            character.switch_pc_npc_campaign()
        return JsonResponse({'status': 'ok'})


class XhrRemoveCharacterView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs['pk'])
        if campaign.may_edit(request.user):
            character = Character.objects.get(id=kwargs['character_pk'])
            character.campaign = None
            character.npc_campaign = None
            character.save()
        return JsonResponse({'status': 'ok'})


class BaseSidebarView(DetailView):

    def get_template_names(self):
        return ['campaigns/sidebar/' + self.kwargs['sidebar_template'] + '.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['may_edit'] = self.object.pc_or_npc_campaign.may_edit(self.request.user)
        except AttributeError:
            context['may_edit'] = self.object.may_edit(self.request.user)
        return context


class XhrSidebarView(BaseSidebarView):
    model = Campaign


class XhrSettingsSidebarView(BaseSidebarView):
    model = Campaign

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SettingsForm(instance=self.object)
        return context


class XhrCharacterSidebarView(BaseSidebarView):
    model = Character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['may_edit'] = self.object.pc_or_npc_campaign.may_edit(self.request.user)
        return context
