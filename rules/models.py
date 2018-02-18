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
    short_name = models.CharField(_('short name'), max_length=20)

    class Meta:
        translate = ('name', 'short_name')

    def __unicode__(self):
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

    def __unicode__(self):
        return self.name
