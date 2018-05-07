# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _


class Character(models.Model):
    name = models.CharField(_('name'), max_length=80)

    created_by = models.ForeignKey('auth.User', verbose_name=_('created by'), on_delete=models.CASCADE)

    base_intelligence = models.IntegerField(_('intelligence'), default=0)

    # physis
    base_deftness = models.IntegerField(_('base deftness'), default=1)
    base_strength = models.IntegerField(_('base strength'), default=1)
    base_attractiveness = models.IntegerField(_('base attractiveness'), default=1)
    base_endurance = models.IntegerField(_('base endurance'), default=1)
    base_resistance = models.IntegerField(_('base resistance'), default=1)
    base_quickness = models.IntegerField(_('base quickness'), default=1)

    # persona
    base_openness = models.IntegerField(_('base openness'), default=1)
    base_conscientiousness = models.IntegerField(_('base conscientiousness'), default=1)
    base_extraversion = models.IntegerField(_('base extraversion'), default=1)
    base_agreeableness = models.IntegerField(_('base agreeableness'), default=1)
    base_neuroticism = models.IntegerField(_('base neuroticism'), default=1)

    shadows = models.ManyToManyField('rules.Shadow', verbose_name=_('shadows'))

    def __str__(self):
        return self.name


class CharacterSkill(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    skill = models.ForeignKey('rules.Skill', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('skill__name_en',)

    def __str__(self):
        return "{} {}".format(self.skill.name, self.value)


class CharacterKnowledge(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    knowledge = models.ForeignKey('rules.Knowledge', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('knowledge__name_en',)

    def __str__(self):
        return "{} {}".format(self.knowledge.name, self.value)
