from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from characters.character_objects import SpellObject
from magic.models import BaseSpell


class SpellOriginView(TemplateView):
    template_name = "characters/character_object_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "spell_origin_list"
        context["title"] = _("Spell Origins")
        context["sub_title"] = _("Spell origins and their spells")
        context["character_object"] = SpellObject(self.request, character=None)
        return context


class BaseSpellDetailView(DetailView):
    model = BaseSpell

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navigation"] = "spell_origin_list"
        return context
