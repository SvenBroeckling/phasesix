from django.template import Library, Template, Context

from armory.models import Item, RiotGear, Weapon
from body_modifications.models import BodyModification
from horror.models import Quirk
from magic.models import BaseSpell
from potions.models import Recipe
from rules.models import Template as PhaseSixTemplate, Foe
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


@register.inclusion_tag("armory/_riot_gear_protection_display.html", takes_context=True)
def riot_gear_protection_display(context, riot_gear):
    context.update({"riot_gear": riot_gear})
    return context


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
    mapping = {
        Weapon: "{% load armory_extras %}{% weapon_widget obj character=character add_button=add_button %}",
        RiotGear: "{% load armory_extras %}{% riot_gear_widget obj character=character %}",
        Item: "{% load armory_extras %}{% item_widget obj character=character %}",
        BaseSpell: "{% load rules_extras %}{% basespell_widget obj character=character %}",
        PhaseSixTemplate: "{% load rules_extras %}{% template_widget obj character=character add_button=add_button %}",
        Foe: "{% load rules_extras %}{% foe_widget obj character=character add_button=add_button %}",
        Quirk: "{% load horror_extras %}{% quirk_widget obj character=character add_button=add_button %}",
        Language: "{% load world_extras %}{% language_widget obj character=character add_button=add_button %}",
        BodyModification: "{% load body_modification_extras %}{% body_modification_widget obj character=character add_button=add_button %}",
        Recipe: "{% load potions_extras %}{% recipe_widget obj character=character add_button=add_button %}",
    }

    return Template(mapping.get(type(obj), "")).render(
        Context(
            {
                "obj": obj,
                "character": character,
                "add_button": add_button,
                "world": context.get("world", None),
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
        "world": context["request"].world,
        "character_object": character_object,
        "add_button": add_button,
        "user": context["user"],
    }


@register.filter
def replace_keyword_value(description, value):
    return description.replace("{X}", str(value))
