from django.urls import path

from eventstream.views import events

app_name = "eventstream"

urlpatterns = [
    path("", events),
]
