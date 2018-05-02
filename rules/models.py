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


class Shadow(models.Model, metaclass=TransMeta):
    """
    A URPG quirk
    """

    name = models.CharField(_('name'), max_length=120)
    extension = models.ForeignKey(Extension, models.CASCADE)

    class Meta:
        translate = ('name',)
        verbose_name = _('shadow')
        verbose_name_plural = _('shadows')

    def __str__(self):
        return self.name


CHARACTER_ATTRIBUTE_CHOICES = (
    ('intelligence', _('intelligence')),

    ('deftness', _('deftness')),
    ('strength', _('strength')),
    ('attractiveness', _('attractiveness')),
    ('endurance', _('endurance')),
    ('resistance', _('resistance')),
    ('quickness', _('quickness')),

    ('openness', _('openness')),
    ('conscientiousness', _('conscientiousness')),
    ('extraversion', _('extraversion')),
    ('agreeableness', _('agreeableness')),
    ('neuroticism', _('neuroticism')),
)


class Template(models.Model, metaclass=TransMeta):
    """
    A character creation template
    """
    name = models.CharField(_('name'), max_length=120)
    extension = models.ForeignKey(Extension, models.CASCADE)

    cost = models.IntegerField(verbose_name=_('cost'), default=1)

    class Meta:
        translate = ('name',)
        verbose_name = _('character template')
        verbose_name_plural = _('character templates')

    def __str__(self):
        return self.name


class TemplateModifier(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(Template, verbose_name=_('template'), on_delete=models.CASCADE)
    attribute = models.CharField(
        verbose_name=_('attribute'),
        max_length=40,
        help_text=_('Leave empty if the knowledge or skill modifier is used.'),
        choices=CHARACTER_ATTRIBUTE_CHOICES,
        null=True,
        blank=True)
    attribute_modifier = models.IntegerField(
        verbose_name=_('attribute modifier'),
        help_text=_('Leave empty if the knowledge or skill modifier is used.'),
        blank=True,
        null=True)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name=_('skill'),
        help_text=_('Leave empty if the attribute or knowledge modifier is used.'),
        null=True,
        blank=True)
    skill_modifier = models.IntegerField(
        verbose_name=_('skill modifier'),
        help_text=_('Leave empty if the attribute or knowledge modifier is used.'),
        blank=True,
        null=True)
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        verbose_name=_('knowledge'),
        help_text=_('Leave empty if the skill or attribute modifier is used.'),
        null=True,
        blank=True)
    knowledge_modifier = models.IntegerField(
        verbose_name=_('knowledge modifier'),
        help_text=_('Leave empty if the skill or attribute modifier is used.'),
        blank=True,
        null=True)


class TemplateRequirement(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(Template, verbose_name=_('template'), on_delete=models.CASCADE)
    required_template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='required_template_requirement_set',
        blank=True,
        null=True)
