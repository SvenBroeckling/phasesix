# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from transmeta import TransMeta


class Extension(models.Model, metaclass=TransMeta):
    """
    A URPG source book extension
    """
    is_mandatory = models.BooleanField(_('is mandatory'), default=False)
    name = models.CharField(_('name'), max_length=120)

    class Meta:
        translate = ('name',)
        verbose_name = _('extension')
        verbose_name_plural = _('extensions')

    def __str__(self):
        return self.name


class Skill(models.Model, metaclass=TransMeta):
    """
    A URPG skill
    """

    name = models.CharField(_('name'), max_length=120)
    extension = models.ForeignKey(Extension, models.CASCADE)
    add_to_all_characters = models.BooleanField(_('add to all characters'), default=True)

    class Meta:
        translate = ('name',)
        verbose_name = _('skill')
        verbose_name_plural = _('skills')

    def __str__(self):
        return self.name


class Knowledge(models.Model, metaclass=TransMeta):
    """
    A URPG skill
    """

    name = models.CharField(_('name'), max_length=120)
    extension = models.ForeignKey(Extension, models.CASCADE)
    add_to_all_characters = models.BooleanField(_('add to all characters'), default=True)

    class Meta:
        translate = ('name',)
        verbose_name = _('knowledge')
        verbose_name_plural = _('knowledge')

    def __str__(self):
        return self.name


class Quirk(models.Model, metaclass=TransMeta):
    """
    A URPG quirk
    """

    name = models.CharField(_('name'), max_length=120)
    extension = models.ForeignKey(Extension, models.CASCADE)

    class Meta:
        translate = ('name',)
        verbose_name = _('quirk')
        verbose_name_plural = _('quirks')

    def __str__(self):
        return self.name


class Gift(models.Model, metaclass=TransMeta):
    """
    A URPG gift
    """

    name = models.CharField(_('name'), max_length=120)
    extension = models.ForeignKey(Extension, models.CASCADE)

    class Meta:
        translate = ('name',)
        verbose_name = _('gift')
        verbose_name_plural = _('gifts')

    def __str__(self):
        return self.name
