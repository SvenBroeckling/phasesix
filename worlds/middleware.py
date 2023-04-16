from worlds.models import WorldSiteConfiguration
from django.conf import settings


class WorldFromDomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _set_cookie_domains(self, value):
        if settings.DEBUG:
            settings.SESSION_COOKIE_DOMAIN = None
            settings.CSRF_COOKIE_DOMAIN = None
        else:
            settings.SESSION_COOKIE_DOMAIN = value
            settings.CSRF_COOKIE_DOMAIN = value

    def __call__(self, request):
        try:
            request.world_configuration = WorldSiteConfiguration.objects.get(dns_domain_name=request.META['HTTP_HOST'])
            self._set_cookie_domains(request.world_configuration.session_cookie_domain)
        except WorldSiteConfiguration.DoesNotExist:
            try:
                request.world_configuration = WorldSiteConfiguration.objects.get(
                    dns_domain_name=request.META['HTTP_X_FORWARDED_HOST'])
                self._set_cookie_domains(request.world_configuration.session_cookie_domain)
            except (WorldSiteConfiguration.DoesNotExist, KeyError):
                request.world_configuration = None

        response = self.get_response(request)
        return response
