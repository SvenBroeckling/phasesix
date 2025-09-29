from django.views.generic import DetailView, ListView

from rulebook.models import Chapter, WorldBook


class DownloadView(ListView):
    template_name = "rulebook/download.html"
    model = WorldBook

    def get_queryset(self):
        if self.request.world:
            return WorldBook.objects.filter(world=self.request.world)
        return WorldBook.objects.all()


class ChapterDetailView(DetailView):
    template_name = "rulebook/chapter_detail.html"
    model = Chapter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chapters"] = Chapter.objects.all()
        return context
