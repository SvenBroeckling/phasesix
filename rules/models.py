# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from transmeta import TransMeta


class ExtensionSelectQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(extensions__id__in=extension_rm.all()) |
            Q(extensions__id__in=Extension.objects.filter(is_mandatory=True))
        )


class Extension(models.Model, metaclass=TransMeta):
    """
    A URPG source book extension
    """
    is_mandatory = models.BooleanField(_('is mandatory'), default=False)
    fa_icon_class = models.CharField(_('FA Icon Class'), max_length=30, default='fa fa-book')
    name = models.CharField(_('name'), max_length=120)
    identifier = models.CharField(_('identifier'), max_length=20)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    is_epoch = models.BooleanField(_('is epoch'), default=True)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('extension')
        verbose_name_plural = _('extensions')

    def __str__(self):
        return self.name


class Lineage(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=80)
    description = models.TextField(_('description'), blank=True, null=True)
    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('lineage')
        verbose_name_plural = _('lineages')

    def __str__(self):
        return self.name


class LineageTemplatePoints(models.Model):
    lineage = models.ForeignKey(Lineage, verbose_name=_('lineage'), on_delete=models.CASCADE)
    template_category = models.ForeignKey(
        'rules.TemplateCategory', verbose_name=_('template category'), on_delete=models.CASCADE)
    points = models.IntegerField(_('points'))

    class Meta:
        ordering = ('template_category__sort_order',)


class Skill(models.Model, metaclass=TransMeta):
    """
    A URPG skill
    """
    objects = ExtensionSelectQuerySet.as_manager()

    KIND_CHOICES = (
        ('p', _('practical')),
        ('m', _('mind')),
    )
    name = models.CharField(_('name'), max_length=120)
    kind = models.CharField(_('kind'), max_length=1, choices=KIND_CHOICES)
    extensions = models.ManyToManyField('rules.Extension')
    show_on_combat_tab = models.BooleanField(_('show on combat tab'), default=False)

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

    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=120)
    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
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
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    extensions = models.ManyToManyField('rules.Extension')

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('shadow')
        verbose_name_plural = _('shadows')

    def __str__(self):
        return self.name


CHARACTER_ATTRIBUTE_CHOICES = (
    ('base_intelligence', _('intelligence')),
    ('base_max_health', _('max health')),

    ('base_max_arcana', _('max arcana')),
    ('base_spell_points', _('spell points')),

    ('base_bonus_dice', _('bonus dice')),
    ('base_destiny_dice', _('destiny dice')),
    ('base_rerolls', _('rerolls')),

    ('base_deftness', _('deftness')),
    ('base_strength', _('strength')),
    ('base_attractiveness', _('attractiveness')),
    ('base_endurance', _('endurance')),
    ('base_resistance', _('resistance')),
    ('base_quickness', _('quickness')),

    ('base_openness', _('openness')),
    ('base_conscientiousness', _('conscientiousness')),
    ('base_extraversion', _('extraversion')),
    ('base_agreeableness', _('agreeableness')),
    ('base_neuroticism', _('neuroticism')),
)


class TemplateCategory(models.Model, metaclass=TransMeta):
    COLOR_CLASS_CHOICES = (
        ('', _('None')),
        ('primary', 'primary'),
        ('secondary', 'secondary'),
        ('success', 'success'),
        ('danger', 'danger'),
        ('warning', 'warning'),
        ('info', 'info'),
        ('light', 'light'),
        ('dark', 'dark'),
        ('muted', 'muted'),
        ('white', 'white'),
    )
    name = models.CharField(_('name'), max_length=120)
    fg_color_class = models.CharField(
        _('bootstrap color class'),
        max_length=10,
        blank=True,
        choices=COLOR_CLASS_CHOICES,
        default='')
    bg_color_class = models.CharField(
        _('bootstrap color class'),
        max_length=10,
        blank=True,
        choices=COLOR_CLASS_CHOICES,
        default='')
    description = models.TextField(_('description'), blank=True, null=True)
    sort_order = models.IntegerField(_('sort order'), default=1000)
    allow_for_reputation = models.BooleanField(_('Allow for reputation'), default=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('template category')
        verbose_name_plural = _('template categories')

    def __str__(self):
        return self.name

    def get_bg_color_class(self):
        if self.bg_color_class:
            return 'bg-{}'.format(self.bg_color_class)
        return ''

    def get_fg_color_class(self):
        if self.fg_color_class:
            return 'text-{}'.format(self.fg_color_class)
        return ''


class Template(models.Model, metaclass=TransMeta):
    """
    A character creation template
    """
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=120)
    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    category = models.ForeignKey(TemplateCategory, models.CASCADE, verbose_name=_('category'))

    rules = models.TextField(_('rules'), blank=True, null=True)
    quote = models.TextField(_('quote'), blank=True, null=True)
    quote_author = models.CharField(_('quote author'), max_length=50, null=True, blank=True)

    cost = models.IntegerField(verbose_name=_('cost'), default=1)

    class Meta:
        translate = ('name', 'rules')
        verbose_name = _('character template')
        verbose_name_plural = _('character templates')
        ordering = ('category__sort_order',)

    def __str__(self):
        return self.name


class TemplateModifier(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(Template, verbose_name=_('template'), on_delete=models.CASCADE)
    attribute = models.CharField(
        verbose_name=_('attribute'),
        max_length=40,
        choices=CHARACTER_ATTRIBUTE_CHOICES,
        null=True,
        blank=True)
    attribute_modifier = models.IntegerField(
        verbose_name=_('attribute modifier'),
        blank=True,
        null=True)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name=_('skill'),
        null=True,
        blank=True)
    skill_modifier = models.IntegerField(
        verbose_name=_('skill modifier'),
        blank=True,
        null=True)
    knowledge = models.ForeignKey(
        Knowledge,
        on_delete=models.CASCADE,
        verbose_name=_('knowledge'),
        null=True,
        blank=True)
    knowledge_modifier = models.IntegerField(
        verbose_name=_('knowledge modifier'),
        blank=True,
        null=True)
    shadow = models.ForeignKey(
        Shadow,
        on_delete=models.CASCADE,
        verbose_name=_('shadow'),
        null=True,
        blank=True)


class TemplateRequirement(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(Template, verbose_name=_('template'), on_delete=models.CASCADE)
    required_template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='required_template_requirement_set',
        blank=True,
        null=True)
