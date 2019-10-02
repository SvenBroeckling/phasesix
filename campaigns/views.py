from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView

from campaigns.models import Campaign


class CampaignListView(ListView):
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Campaign.objects.all()
            return Campaign.objects.filter(created_by=user)


class CampaignCreateView(CreateView):
    model = Campaign
    fields = ('name', 'epoch', 'abstract',)

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
        context['may_edit'] = self.object.created_by == self.request.user or self.request.user.is_staff
        return context
