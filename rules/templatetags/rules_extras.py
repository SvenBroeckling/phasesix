import re

import markdown2
from django.template import Library
from django.utils.safestring import mark_safe

from characters.models import Character
from worlds.models import WikiPage

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
def urpg_markup(value, safe_mode=True):
    if value is None:
        return ''
    return mark_safe(markdown2.markdown(value, safe_mode=safe_mode, extras=['tables']))


@register.filter
def replace_tags(value, world):
    if value is None or value == '':
        return ''

    def _repl_tags(match_object):
        text = ''
        tag = match_object.group(0).strip('[]')
        if '|' in tag:
            tag, text = tag.split('|')

        try:
            obj = WikiPage.objects.get(world=world, slug=tag)
        except WikiPage.DoesNotExist:
            return text

        return '<a href="%s">%s</a>' % (obj.get_absolute_url(), text)

    tags_re = re.compile(r"\[\[([^\[])+\]\]", flags=re.UNICODE)
    value = re.sub(tags_re, _repl_tags, value)

    return mark_safe(value)


@register.simple_tag
def latest_user_image(user):
    try:
        return Character.objects.filter(created_by=user, image__isnull=False).exclude(image='').latest('id').image
    except Character.DoesNotExist:
        return None
