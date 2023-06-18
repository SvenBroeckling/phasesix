from django.db.models import Q
from django.views.generic import TemplateView

from worlds.models import WikiPage


class SidebarSearchView(TemplateView):
    template_name = 'portal/sidebar/search.html'


class XhrSearchResultsView(TemplateView):
    template_name = 'portal/sidebar/search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        search_descriptions = self.request.GET.get('search_descriptions', 'off')
        if query:
            if search_descriptions == 'on':
                context['wiki_pages'] = WikiPage.objects.filter(
                    Q(name_en__icontains=query) | Q(name_de__icontains=query) |
                    Q(text_en__icontains=query) | Q(text_de__icontains=query))
            else:
                context['wiki_pages'] = WikiPage.objects.filter(
                    Q(name_de__icontains=query) | Q(name_en__icontains=query))
        return context
