from django.views.generic import TemplateView

from gmtools.utils import get_homebrew_models


class IndexView(TemplateView):
    template_name = "homebrew/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["homebrew_querysets"] = [
            model.objects.filter(is_homebrew=True, keep_as_homebrew=False)
            for model in get_homebrew_models()
        ]
        return context
