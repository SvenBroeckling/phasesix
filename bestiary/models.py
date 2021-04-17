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


class FoeResistanceOrWeakness(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=100)

    class Meta:
        translate = ('name',)
        verbose_name = _('foe resistance or weakness')
        verbose_name_plural = _('foe resistances or weaknesses')

    def __str__(self):
        return self.name


class Foe(models.Model, metaclass=TransMeta):
    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)

    type = models.ForeignKey(FoeType, verbose_name=_('type'), on_delete=models.CASCADE)

    health = models.IntegerField(_('health'), default=6)
    actions = models.IntegerField(_('actions'), default=2)
    movement = models.IntegerField(_('movement'), default=1)
    minimum_roll = models.IntegerField(_('minimum_roll'), default=5)

    resistances = models.ManyToManyField(
        FoeResistanceOrWeakness,
        related_name='foe_resistance_set',
        verbose_name=_('resistances'))
    weaknesses = models.ManyToManyField(
        FoeResistanceOrWeakness,
        related_name='foe_weakness_set',
        verbose_name=_('weaknesses'))

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('foe')
        verbose_name_plural = _('foes')

    def __str__(self):
        return self.name


class FoeAction(models.Model, metaclass=TransMeta):
    foe = models.ForeignKey(Foe, verbose_name=_('foe'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=256)
    effect = models.TextField(_('effect'))
