from django.views.generic import TemplateView

from forum.models import Board


class IndexView(TemplateView):
    template_name = 'forum/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['public_boards'] = Board.objects.filter(is_staff_only=False)
        context['staff_boards'] = Board.objects.filter(is_staff_only=True)
        return context

