from worlds.models import WorldSiteConfiguration
from django.conf import settings


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

    @staticmethod
    def _set_cookie_domains(value):
        if settings.DEBUG:
            settings.SESSION_COOKIE_DOMAIN = None
            settings.CSRF_COOKIE_DOMAIN = None
        else:
            settings.SESSION_COOKIE_DOMAIN = value
            settings.CSRF_COOKIE_DOMAIN = value

    def __call__(self, request):
        request.world_configuration = self._get_world_configuration(request)
        if request.world_configuration is not None:
            self._set_cookie_domains(request.world_configuration.session_cookie_domain)
        return self.get_response(request)
