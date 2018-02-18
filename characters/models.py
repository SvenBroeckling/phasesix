# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _


class Character(models.Model):
    name = models.CharField(_('name'), max_length=80)

    intelligence = models.IntegerField(_('intelligence'), default=0)
    valour = models.IntegerField(_('valour'), default=0)
    willpower = models.IntegerField(_('willpower'), default=0)

    # physis
    deftness = models.IntegerField(_('deftness'), default=1)
    strength = models.IntegerField(_('strength'), default=1)
    attractiveness = models.IntegerField(_('attractiveness'), default=1)
    endurance = models.IntegerField(_('endurance'), default=1)
    resistance = models.IntegerField(_('resistance'), default=1)
    quickness = models.IntegerField(_('quickness'), default=1)

    # persona
    openness = models.IntegerField(_('openness'), default=1)
    conscientiousness = models.IntegerField(_('conscientiousness'), default=1)
    extraversion = models.IntegerField(_('extraversion'), default=1)
    agreeableness = models.IntegerField(_('agreeableness'), default=1)
    neuroticism = models.IntegerField(_('neuroticism'), default=1)

    gifts = models.ManyToManyField('rules.Gift', verbose_name=_('gifts'))
    quirks = models.ManyToManyField('rules.Quirk', verbose_name=_('quirks'))

    def __str__(self):
        return self.name


class CharacterSkill(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    skill = models.ForeignKey('rules.Skill', models.CASCADE)
    value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('skill__name_en',)

    def __str__(self):
        return "{} {}".format(self.skill.name, self.value)


class CharacterKnowledge(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    knowledge = models.ForeignKey('rules.Knowledge', models.CASCADE)
    value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('knowledge__name_en',)

    def __str__(self):
        return "{} {}".format(self.knowledge.name, self.value)
