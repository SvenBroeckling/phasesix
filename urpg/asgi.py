import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import campaigns.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urpg.settings')

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            campaigns.routing.websocket_urlpatterns
        )
    ),
})
