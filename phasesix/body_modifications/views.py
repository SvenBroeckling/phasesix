from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from characters.character_objects import BodyModificationObject


class BodyModificationTypeListView(TemplateView):
    template_name = "characters/character_object_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Body Modifications")
        context["sub_title"] = _("Things you can integrate into your body")
        context["character_object"] = BodyModificationObject(
            self.request, character=None
        )
        return context
