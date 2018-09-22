from django.template import Library

register = Library()


@register.inclusion_tag('rules/_template_widget.html')
def template_widget(template):
    return {
        'template': template
    }
