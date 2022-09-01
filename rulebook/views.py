from django.views.generic import DetailView

from rulebook.models import Chapter


class ChapterDetailView(DetailView):
    template_name = 'rulebook/chapter_detail.html'
    model = Chapter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapters'] = Chapter.objects.all()
        return context
