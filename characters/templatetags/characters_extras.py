from django.db.models import Sum
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()


@register.inclusion_tag('characters/_character_attribute_widget.html')
def character_attribute_widget(name, attribute):
    return {
        'name': name,
        'attribute': attribute,
    }


@register.simple_tag
def color_value_span(value, max_value, invert=False, algebraic_sign=False):
    try:
        value = int(value)
        max_value = int(max_value)
    except (TypeError, ValueError):
        return mark_safe(value)
    color_classes = [80, 60, 40, 20, 0, -20, -40, -60]
    display_value = value

    if invert:
        value = max_value - value

    try:
        p = (value * 100) / max_value
    except ZeroDivisionError:  # max_value == 0
        p = 0

    p = 100 if p > 100 else p

    for color_class in color_classes:
        if p >= color_class:
            break
    else:
        color_class = 0
    color_class = "p{}".format(color_class) if p >= 0 else "n{}".format(abs(color_class))

    if algebraic_sign and value > 0:
        display_value = "+{}".format(display_value)

    return mark_safe('<span title="max. %s" class="color-%s">%s</span>' % (max_value, color_class, display_value))


@register.simple_tag
def display_modifications(character_weapon, attribute):
    return ''
    res = ''
    for wm in character_weapon.modifications.all():
        for wmm in wm.weaponmodificationattributechange_set.all():
            if wmm.attribute == attribute and wmm.modifier != 0:
                if attribute == 'concealment':
                    css_class = 'text-success' if wmm.modifier < 0 else 'text-danger'
                else:
                    css_class = 'text-danger' if wmm.modifier < 0 else 'text-success'
                res += ' <span title="%s" class="%s">%+d</span>' % (wm.name, css_class, wmm.modifier)
    return mark_safe(res)

@register.simple_tag
def character_remaining_template_points(character, template_category):
    available_points = character.lineage.lineagetemplatepoints_set.get(
        template_category=template_category).points
    spent_points = character.charactertemplate_set.filter(
        template__category=template_category).aggregate(Sum('template__cost'))['template__cost__sum'] or 0
    return available_points - spent_points

