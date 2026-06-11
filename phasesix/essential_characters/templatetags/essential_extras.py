from django import template
from django.utils.translation import gettext

from essential_characters.forms import ATTRIBUTE_LABELS
from essential_characters.rules import ATTRIBUTES

register = template.Library()


@register.simple_tag
def essential_attribute_rows(character):
    return [
        {
            "name": name,
            "label": ATTRIBUTE_LABELS[name],
            "value": getattr(character, name),
            "target": 30 + getattr(character, name) * 15,
        }
        for name in ATTRIBUTES
    ]


@register.simple_tag
def essential_rank_options(maximum=4):
    return range(maximum + 1)
