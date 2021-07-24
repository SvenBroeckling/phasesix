from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from transmeta import TransMeta


class SpellVariant(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell variant')
        verbose_name_plural = _('spell variants')

    def __str__(self):
        return self.name


class SpellType(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell type')
        verbose_name_plural = _('spell types')

    def __str__(self):
        return self.name


class BaseSpell(models.Model, metaclass=TransMeta):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('created by'))

    variant = models.ForeignKey(
        SpellVariant,
        on_delete=models.CASCADE,
        verbose_name=_('variant'))
    type = models.ForeignKey(
        SpellType,
        on_delete=models.CASCADE,
        verbose_name=_('type'))

    name = models.CharField(_('name'), max_length=80)
    rules = models.TextField(_('rules'))
    quote = models.TextField(_('quote'), blank=True, null=True)
    quote_author = models.CharField(_('quote author'), max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        translate = ('name', 'rules')
        verbose_name = _('base spell')
        verbose_name_plural = _('base spell')
