from django.db import models
from django.utils.translation import ugettext_lazy as _

from transmeta import TransMeta


class FoeType(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        translate = ('name',)
        verbose_name = _('foe type')
        verbose_name_plural = _('foe types')

    def __str__(self):
        return self.name


class Foe(models.Model, metaclass=TransMeta):
    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)

    type = models.ForeignKey(FoeType, verbose_name=_('type'), on_delete=models.CASCADE)

    class Meta:
        translate = ('name',)
        verbose_name = _('foe')
        verbose_name_plural = _('foes')

    def __str__(self):
        return self.name
