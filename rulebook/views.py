from django.views.generic import ListView

from rulebook.models import Chapter


class IndexView(ListView):
    model = Chapter

