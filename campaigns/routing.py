from django.urls import re_path

from .consumers import DiceConsumer

websocket_urlpatterns = [
    re_path(r'ws/campaign/(?P<room_name>\w+-\d+)/$', DiceConsumer.as_asgi()),
]