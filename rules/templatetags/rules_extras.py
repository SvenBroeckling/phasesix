from django.template import Library
from django.utils.safestring import mark_safe
from markdown import markdown

register = Library()


@register.inclusion_tag('rules/_template_widget.html')
def template_widget(template):
    return {
        'template': template
    }


@register.filter
def urpg_markup(value):
    return mark_safe(markdown(value, extensions=['markdown.extensions.tables']))