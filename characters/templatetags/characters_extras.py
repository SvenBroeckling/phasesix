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
    color_classes = [80, 60, 40, 20, 0, -20, -40, -60]

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

    return mark_safe('<span title="max. %s" class="color-%s">%s</span>' % (max_value, color_class, value))
