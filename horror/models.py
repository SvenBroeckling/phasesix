from django.db import models
from transmeta import TransMeta

from django.utils.translation import ugettext_lazy as _

from rules.models import CHARACTER_ATTRIBUTE_CHOICES, Skill


class QuirkCategory(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('quirk category')
        verbose_name_plural = _('quirk categories')

    def __str__(self):
        return "{} ({})".format(self.name, self.id)


class Quirk(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    category = models.ForeignKey(QuirkCategory, verbose_name=_("category"), on_delete=models.CASCADE)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('quirk')
        verbose_name_plural = _('quirks')

    def __str__(self):
        return self.name


class QuirkModifier(models.Model, metaclass=TransMeta):
    quirk = models.ForeignKey(Quirk, verbose_name=_('quirk'), on_delete=models.CASCADE)
    attribute = models.CharField(
        verbose_name=_('attribute'),
        max_length=40,
        choices=CHARACTER_ATTRIBUTE_CHOICES,
        null=True,
        blank=True)
    attribute_modifier = models.IntegerField(
        verbose_name=_('attribute modifier'),
        blank=True,
        null=True)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name=_('skill'),
        null=True,
        blank=True)
    skill_modifier = models.IntegerField(
        verbose_name=_('skill modifier'),
        blank=True,
        null=True)
