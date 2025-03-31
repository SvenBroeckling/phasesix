from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BodyModificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "body_modifications"
    verbose_name = _("Body Modifications")
    verbose_name_plural = _("Body Modifications")
