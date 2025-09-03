from django.apps import AppConfig

from django.utils.translation import gettext_lazy as _


class ModalsSidebarsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modals_sidebars"
    verbose_name = _("Modals und Sidebars")
