from django.template import Library
from django.conf import settings

register = Library()

@register.simple_tag
def ws_room_url(room_name):
    if settings.DEBUG:
        return f'ws://localhost:8000/ws/campaign/{room_name}/'
    return f'wss://phasesix.org/ws/campaign/{room_name}/'
