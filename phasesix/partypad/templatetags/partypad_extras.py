from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag
def partypad_ws_room_url(room_name):
    if settings.DEBUG:
        return f"ws://localhost:8000/ws/campaign/{room_name}/"
    return f"wss://phasesix.org/ws/campaign/{room_name}/"
