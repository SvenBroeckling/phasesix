from django.template import Library
from django.conf import settings
from django.template.loader import render_to_string

register = Library()


@register.simple_tag(takes_context=True)
def campaign_fragment(context, fragment_template):
    context = context.flatten()
    context['fragment_template'] = fragment_template
    return render_to_string('campaigns/fragments/' + fragment_template + '.html', context=context)


@register.simple_tag
def ws_room_url(room_name):
    if settings.DEBUG:
        return f'ws://localhost:8000/ws/campaign/{room_name}/'
    return f'wss://phasesix.org/ws/campaign/{room_name}/'
