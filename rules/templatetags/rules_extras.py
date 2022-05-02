from django.template import Library
from django.utils.safestring import mark_safe
import markdown2

from characters.models import Character

register = Library()


@register.inclusion_tag('rules/_template_widget.html', takes_context=True)
def template_widget(context, template):
    context.update({
        'template': template
    })
    return context


@register.inclusion_tag('magic/_basespell_widget.html', takes_context=True)
def basespell_widget(context, basespell, character=None):
    context.update({
        'basespell': basespell,
        'character': character,
    })
    return context


@register.filter
def urpg_markup(value):
    if value is None:
        return ''
    return mark_safe(markdown2.markdown(value, safe_mode=True, extras=['tables']))


@register.simple_tag
def latest_user_image(user):
    try:
        return Character.objects.filter(created_by=user, image__isnull=False).exclude(image='').latest('id').image
    except Character.DoesNotExist:
        return None
