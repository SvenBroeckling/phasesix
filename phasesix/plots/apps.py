from django.apps import AppConfig


class PlotsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "plots"

    def ready(self):
        from plots import signals  # noqa: F401
