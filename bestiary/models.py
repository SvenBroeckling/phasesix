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

    image = models.ImageField(_('image'), upload_to='foe_images', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)

    type = models.ForeignKey(FoeType, verbose_name=_('type'), on_delete=models.CASCADE)

    health = models.IntegerField(_('health'), default=6)
    actions = models.IntegerField(_('actions'), default=2)
    movement = models.IntegerField(_('movement'), default=1)
    minimum_roll = models.IntegerField(_('minimum roll'), default=5)

    resistances = models.ManyToManyField(
        FoeResistanceOrWeakness,
        blank=True,
        related_name='foe_resistance_set',
        verbose_name=_('resistances'))
    weaknesses = models.ManyToManyField(
        FoeResistanceOrWeakness,
        blank=True,
        related_name='foe_weakness_set',
        verbose_name=_('weaknesses'))

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('foe')
        verbose_name_plural = _('foes')

    def __str__(self):
        return self.name

    def resistance_string(self):
        return ",".join([r.name for r in self.resistances.all()]) or '-'

    def weakness_string(self):
        return ",".join([r.name for r in self.weaknesses.all()]) or '-'


class FoeAction(models.Model, metaclass=TransMeta):
    foe = models.ForeignKey(Foe, verbose_name=_('foe'), on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=256)
    skill = models.IntegerField(_('skill'), default=6)
    effect = models.TextField(_('effect'))

    class Meta:
        translate = ('name', 'effect')
        verbose_name = _('foe action')
        verbose_name_plural = _('foe actions')

