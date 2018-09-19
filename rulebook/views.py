from django.views.generic import ListView, DetailView

from rulebook.models import Chapter


class IndexView(ListView):
    model = Chapter


class ChapterDetailView(DetailView):
    model = Chapter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_chapters'] = Chapter.objects.order_by('number')
        return context
