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


@register.simple_tag
def essential_condition_rows(character):
    return [
        {
            "label": gettext("Wounds"),
            "value": character.wounds,
            "options": range(character.wound_threshold + 1),
        },
        {
            "label": gettext("Burden"),
            "value": character.burden,
            "options": range(character.burden_threshold + 1),
        },
        {
            "label": gettext("Omen"),
            "value": character.omen,
            "options": range(character.omen_max + 1),
        },
        {
            "label": gettext("Arkana"),
            "value": character.arkana,
            "options": range(character.arkana_max + 1),
        },
        {
            "label": gettext("Favor"),
            "value": character.favor,
            "options": range(character.favor_max + 1),
        },
        {
            "label": gettext("Corruption"),
            "value": character.corruption,
            "options": range(max(6, character.corruption) + 1),
        },
    ]
