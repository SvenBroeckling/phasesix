from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import ListView, CreateView, DetailView

from campaigns.forms import SettingsForm
from campaigns.models import Campaign
from characters.models import Character


class CampaignListView(ListView):
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Campaign.objects.all()
            return Campaign.objects.filter(created_by=user)


class CampaignCreateView(CreateView):
    model = Campaign
    fields = ('name', 'epoch', 'abstract', 'character_visibility', 'currency_map')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
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


class SaveSettingsView(View):
    def post(self, request, *args, **kwargs):
        campaign = Campaign.objects.get(id=kwargs['pk'])
        if campaign.may_edit(request.user):
            form = SettingsForm(request.POST, instance=campaign, files=request.FILES)
            if form.is_valid():
                form.save()
        return HttpResponseRedirect(campaign.get_absolute_url())


class BaseSidebarView(DetailView):

    def get_template_names(self):
        return ['campaigns/sidebar/' + self.kwargs['sidebar_template'] + '.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['may_edit'] = self.object.may_edit(self.request.user)
        except AttributeError:
            context['may_edit'] = False
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
