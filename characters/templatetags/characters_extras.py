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
def color_value_span(value, max_value, invert=False):
    value = int(value)
    max_value = int(max_value)

    if invert:
        value = max_value - value

    try:
        p = (value * 100) / max_value
    except ZeroDivisionError:  # max_value == 0
        p = 0

    p = 100 if p > 100 else p

    if p > 80:
        color = '#47C040'
    elif p > 60:
        color = '#C0BC40'
    elif p > 20:
        color = '#ECA935'
    else:
        color = '#EC4D35'
    return mark_safe('<span title="max. %s" style="font-weight: bold; color:%s;">%s</span>' % (max_value, color, value))

