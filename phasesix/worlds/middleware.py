from worlds.models import WorldSiteConfiguration


class WorldFromDomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _get_world_configuration(request):
        try:
            return WorldSiteConfiguration.objects.get(dns_domain_name=request.META['HTTP_X_FORWARDED_HOST'])
        except (WorldSiteConfiguration.DoesNotExist, KeyError):
            try:
                return WorldSiteConfiguration.objects.get(dns_domain_name=request.META['HTTP_HOST'])
            except (WorldSiteConfiguration.DoesNotExist, KeyError):
                return None

    def __call__(self, request):
        request.world_configuration = self._get_world_configuration(request)
        return self.get_response(request)
