from django.template import Library

register = Library()


@register.inclusion_tag('characters/_character_attribute_widget.html')
def character_attribute_widget(name, attribute):
    return {
        'name': name,
        'attribute': attribute,
    }
