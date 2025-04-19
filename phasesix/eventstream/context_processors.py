from django.conf import settings


def event_source_url(request):
    return {"event_source_url": settings.EVENT_SOURCE_URL}
