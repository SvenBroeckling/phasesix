from worlds.models import WorldSiteConfiguration
from django.conf import settings


class WorldFromDomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.world_configuration = WorldSiteConfiguration.objects.get(dns_domain_name=request.META['HTTP_HOST'])
        except WorldSiteConfiguration.DoesNotExist:
            try:
                request.world_configuration = WorldSiteConfiguration.objects.get(
                    dns_domain_name=request.META['HTTP_X_FORWARDED_HOST'])
            except WorldSiteConfiguration.DoesNotExist:
                request.world_configuration = None

        response = self.get_response(request)
        return response
