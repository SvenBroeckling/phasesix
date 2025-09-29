from worlds.models import World


class WorldFromDomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _get_world(request):
        try:
            return World.objects.get(
                dns_domain_name=request.headers["x-forwarded-host"]
            )
        except (World.DoesNotExist, KeyError):
            try:
                return World.objects.get(dns_domain_name=request.headers["host"])
            except (World.DoesNotExist, KeyError):
                return None

    def __call__(self, request):
        request.world = self._get_world(request)
        return self.get_response(request)
