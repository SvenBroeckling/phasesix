from django.db import models
from django.utils.translation import gettext_lazy as gt


class HomebrewModel(models.Model):
    is_homebrew = models.BooleanField(gt('is homebrew'), default=False)
    keep_as_homebrew = models.BooleanField(
        gt('keep as homebrew'),
        help_text=gt('This was not accepted as general spell and is kept as homebrew.'),
        default=False)
    homebrew_campaign = models.ForeignKey(
        'campaigns.Campaign',
        related_name="homebrew_%(app_label)s_%(class)s_set",
        blank=True,
        null=True,
        verbose_name=gt('homebrew campaign'),
        on_delete=models.SET_NULL)
    homebrew_character = models.ForeignKey(
        'characters.Character',
        related_name="homebrew_%(app_label)s_%(class)s_set",
        blank=True,
        null=True,
        verbose_name=gt('homebrew character'),
        on_delete=models.SET_NULL)

    class Meta:
        abstract = True
