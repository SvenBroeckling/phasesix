from django.template import Library, Template, Context

from armory.models import Item, RiotGear, Weapon
from body_modifications.models import BodyModification
from horror.models import Quirk
from magic.models import BaseSpell
from rules.models import Template as PhaseSixTemplate
from worlds.models import Language

register = Library()


@register.simple_tag
def rarity_color_class(rarity):
    rarity_colors = {
        "c": "secondary",  # Common
        "u": "success",  # Uncommon
        "r": "primary",  # Rare
        "1": "warning",  # Unique
        "l": "danger",  # Legendary
    }

    return rarity_colors.get(rarity, "default")


@register.inclusion_tag("armory/_riot_gear_protection_display.html")
def riot_gear_protection_display(riot_gear):
    return {"riot_gear": riot_gear}


@register.inclusion_tag("armory/_item_widget.html", takes_context=True)
def item_widget(context, item, character=None):
    context.update(
        {
            "item": item,
            "character": character,
        }
    )
    return context


@register.inclusion_tag("armory/_weapon_widget.html", takes_context=True)
def weapon_widget(context, weapon, character=None, add_button=False):
    context.update({"weapon": weapon, "character": character, "add_button": add_button})
    return context


@register.inclusion_tag("armory/_riot_gear_widget.html", takes_context=True)
def riot_gear_widget(context, riot_gear, character=None):
    context.update(
        {
            "riot_gear": riot_gear,
            "character": character,
        }
    )
    return context


@register.simple_tag(takes_context=True)
def object_widget(context, obj, character=None, add_button=False):
    template_string = ""
    if isinstance(obj, Weapon):
        template_string = "{% load armory_extras %}{% weapon_widget obj character=character add_button=add_button %}"
    if isinstance(obj, RiotGear):
        template_string = (
            "{% load armory_extras %}{% riot_gear_widget obj character=character %}"
        )
    if isinstance(obj, Item):
        template_string = (
            "{% load armory_extras %}{% item_widget obj character=character %}"
        )
    if isinstance(obj, BaseSpell):
        template_string = (
            "{% load rules_extras %}{% basespell_widget obj character=character %}"
        )
    if isinstance(obj, PhaseSixTemplate):
        template_string = "{% load rules_extras %}{% template_widget obj character=character add_button=add_button %}"
    if isinstance(obj, Quirk):
        template_string = "{% load horror_extras %}{% quirk_widget obj character=character add_button=add_button %}"
    if isinstance(obj, Language):
        template_string = "{% load world_extras %}{% language_widget obj character=character add_button=add_button %}"
    if isinstance(obj, BodyModification):
        template_string = "{% load body_modification_extras %}{% body_modification_widget obj character=character add_button=add_button %}"

    return Template(template_string).render(
        Context(
            {
                "obj": obj,
                "character": character,
                "add_button": add_button,
                "world_configuration": context.get("world_configuration", None),
                "user": context["user"],
            }
        )
    )


@register.inclusion_tag("portal/_searchable_object_card_list.html", takes_context=True)
def searchable_object_card_list(
    context,
    character_object,
    add_button=False,
):

    return {
        "world_configuration": context["request"].world_configuration,
        "character_object": character_object,
        "add_button": add_button,
        "user": context["user"],
    }


@register.filter
def replace_keyword_value(description, value):
    return description.replace("{X}", str(value))
