from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from transmeta import TransMeta


class SpellCost(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell cost')
        verbose_name_plural = _('spell costs')

    def __str__(self):
        return self.name


class SpellRange(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell range')
        verbose_name_plural = _('spell ranges')

    def __str__(self):
        return self.name


class SpellAreaOfEffect(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell area of effect')
        verbose_name_plural = _('spell areas of effect')

    def __str__(self):
        return self.name


class SpellComponents(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell component')
        verbose_name_plural = _('spell components')

    def __str__(self):
        return self.name


class SpellCastingTime(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell casting time')
        verbose_name_plural = _('spell casting times')

    def __str__(self):
        return self.name


class SpellType(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell type')
        verbose_name_plural = _('spell types')

    def __str__(self):
        return self.name


class SpellPower(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)
    wounds = models.IntegerField(_('wounds'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell power')
        verbose_name_plural = _('spell powers')

    def __str__(self):
        return self.name


class SpellFlavour(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)
    cost = models.IntegerField(_('cost'), default=0)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('spell flavour')
        verbose_name_plural = _('spell flavours')

    def __str__(self):
        return self.name


class Spell(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(_('name'), max_length=80)
    description = models.TextField(_('description'))

    cost = models.ForeignKey(SpellCost, on_delete=models.CASCADE)
    flavour = models.ForeignKey(SpellFlavour, on_delete=models.CASCADE)
    power = models.ForeignKey(SpellPower, on_delete=models.CASCADE)
    type = models.ForeignKey(SpellType, on_delete=models.CASCADE)
    casting_time = models.ForeignKey(SpellCastingTime, on_delete=models.CASCADE)
    components = models.ForeignKey(SpellComponents, on_delete=models.CASCADE)
    area_of_effect = models.ForeignKey(SpellAreaOfEffect, on_delete=models.CASCADE)
    range = models.ForeignKey(SpellRange, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
