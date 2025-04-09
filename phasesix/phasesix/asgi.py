import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phasesix.settings")
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import campaigns.routing


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(campaigns.routing.websocket_urlpatterns)
        ),
    }
)
