# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _

from rules.models import Skill


class CharacterQuerySet(models.QuerySet):
    def create_random_character(self, user):
        character = self.create(
            name="A Random Guy",
            created_by=user)
        for skill in Skill.objects.filter(add_to_all_characters=True):
            character.characterskill_set.create(skill=skill, base_value=1)
        return character


class Character(models.Model):
    objects = CharacterQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=80)
    created_by = models.ForeignKey('auth.User', verbose_name=_('created by'), on_delete=models.CASCADE)
    base_intelligence = models.IntegerField(_('intelligence'), default=100)

    # dice
    base_bonus_dice = models.IntegerField(_('base bonus dice'), default=0)
    base_destiny_dice = models.IntegerField(_('base destiny dice'), default=0)
    base_rerolls = models.IntegerField(_('base rerolls'), default=0)

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

    def get_absolute_url(self):
        return reverse('characters:detail', kwargs={'pk': self.id})

    @property
    def intelligence(self):
        return self.base_intelligence

    @property
    def bonus_dice(self):
        return self.base_bonus_dice

    @property
    def destiny_dice(self):
        return self.base_destiny_dice

    @property
    def rerolls(self):
        return self.base_rerolls

    @property
    def deftness(self):
        return self.base_deftness

    @property
    def strength(self):
        return self.base_strength

    @property
    def attractiveness(self):
        return self.base_attractiveness

    @property
    def endurance(self):
        return self.base_endurance

    @property
    def resistance(self):
        return self.base_resistance

    @property
    def quickness(self):
        return self.base_quickness

    @property
    def openness(self):
        return self.base_openness

    @property
    def conscientiousness(self):
        return self.base_conscientiousness

    @property
    def extraversion(self):
        return self.base_extraversion

    @property
    def agreeableness(self):
        return self.base_agreeableness

    @property
    def neuroticism(self):
        return self.base_neuroticism


class CharacterSkill(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    skill = models.ForeignKey('rules.Skill', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('skill__name_de',)

    def __str__(self):
        return "{} {}".format(self.skill.name, self.value)

    @property
    def value(self):
        return self.base_value


class CharacterKnowledge(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    knowledge = models.ForeignKey('rules.Knowledge', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('knowledge__name_en',)

    def __str__(self):
        return "{} {}".format(self.knowledge.name, self.value)

    @property
    def value(self):
        return self.base_value
