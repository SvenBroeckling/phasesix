# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin
from django.db.models import Q, Sum
from django.utils.translation import ugettext_lazy as _
from transmeta import TransMeta

CHARACTER_ASPECT_CHOICES = (
    ('base_max_health', _('max health')),

    ('base_max_arcana', _('max arcana')),
    ('base_spell_points', _('spell points')),

    ('base_actions', _('actions')),
    ('base_minimum_roll', _('minimum roll')),

    ('base_protection', _('protection')),
    ('base_evasion', _('evasion')),

    ('base_bonus_dice', _('bonus dice')),
    ('base_destiny_dice', _('destiny dice')),
    ('base_rerolls', _('rerolls')),

    ('base_max_stress', _('max stress')),
)


class ExtensionSelectQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(extensions__id__in=extension_rm.all()) |
            Q(extensions__id__in=Extension.objects.filter(is_mandatory=True))
        )


class ExtensionQuerySet(models.QuerySet):
    def first_class_extensions(self):
        return self.filter(Q(type='e') | Q(is_mandatory=True)).filter(is_active=True)


class Extension(models.Model, metaclass=TransMeta):
    """
    A URPG source book extension
    """
    EXTENSION_TYPE_CHOICES = (
        ('x', _('Extension')),
        ('e', _('Epoch')),
        ('w', _('World')),
    )
    objects = ExtensionQuerySet.as_manager()

    is_mandatory = models.BooleanField(_('is mandatory'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    type = models.CharField(_('type'), max_length=1, choices=EXTENSION_TYPE_CHOICES, default='x')

    name = models.CharField(_('name'), max_length=120)
    identifier = models.CharField(_('identifier'), max_length=20)
    description = models.TextField(_('description'), blank=True, null=True)

    year_range = models.CharField(_('year range'), blank=True, null=True, max_length=50)
    fa_icon_class = models.CharField(_('FA Icon Class'), max_length=30, default='fas fa-book')

    image = models.ImageField(_('image'), upload_to='extension_images', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    currency_map = models.ForeignKey('armory.CurrencyMap', blank=True, null=True, on_delete=models.SET_NULL)
    fixed_epoch = models.ForeignKey(
        'self',
        limit_choices_to={'type': 'e'},
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'description', 'year_range')
        verbose_name = _('extension')
        verbose_name_plural = _('extensions')

    @property
    def is_epoch(self):
        return self.type == 'e'

    @property
    def is_world(self):
        return self.type == 'w'

    def __str__(self):
        return self.name


class Lineage(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=80)
    description = models.TextField(_('description'), blank=True, null=True)

    extensions = models.ManyToManyField('rules.Extension')
    template = models.ForeignKey('rules.Template', blank=True, null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    base_max_health = models.IntegerField(_('max health'), default=6)

    base_max_arcana = models.IntegerField(_('max arcana'), default=0)
    base_spell_points = models.IntegerField(_('spell points'), default=0)

    base_actions = models.IntegerField(_('base actions'), default=2)
    base_minimum_roll = models.IntegerField(_('base minimum roll'), default=5)

    base_bonus_dice = models.IntegerField(_('base bonus dice'), default=0)
    base_destiny_dice = models.IntegerField(_('base destiny dice'), default=0)
    base_rerolls = models.IntegerField(_('base rerolls'), default=0)

    # Base Values
    base_evasion = models.IntegerField(_('base evasion'), default=0)
    base_protection = models.IntegerField(_('base armor'), default=0)

    # horror
    base_max_stress = models.IntegerField(_('max stress'), default=6)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('lineage')
        verbose_name_plural = _('lineages')

    def __str__(self):
        return self.name

    @property
    def template_point_sum(self):
        tp = self.lineagetemplatepoints_set.aggregate(Sum('points'))
        return tp['points__sum'] if tp else 0


class LineageTemplatePoints(models.Model):
    lineage = models.ForeignKey(Lineage, verbose_name=_('lineage'), on_delete=models.CASCADE)
    template_category = models.ForeignKey(
        'rules.TemplateCategory', verbose_name=_('template category'), on_delete=models.CASCADE)
    points = models.IntegerField(_('points'))

    class Meta:
        ordering = ('template_category__sort_order',)


class Attribute(models.Model, metaclass=TransMeta):
    KIND_CHOICES = (
        ('per', _('persona')),
        ('phy', _('physis')),
    )
    name = models.CharField(_('name'), max_length=120)
    identifier = models.CharField(_('identifier'), max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    kind = models.CharField(_('kind'), max_length=3, choices=KIND_CHOICES)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('attribute')
        verbose_name_plural = _('attributes')

    def __str__(self):
        return self.name


class Skill(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()
    KIND_CHOICES = (
        ('p', _('practical')),
        ('m', _('mind')),
    )
    name = models.CharField(_('name'), max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    kind = models.CharField(_('kind'), max_length=1, choices=KIND_CHOICES)
    extensions = models.ManyToManyField('rules.Extension')

    reference_attribute_1 = models.ForeignKey(
        'rules.Attribute',
        verbose_name=_('reference attribute 1'),
        related_name='reference_attribute_1_set',
        on_delete=models.CASCADE)
    reference_attribute_2 = models.ForeignKey(
        'rules.Attribute',
        verbose_name=_('reference attribute 2'),
        related_name='reference_attribute_2_set',
        on_delete=models.CASCADE)

    class Meta:
        translate = ('name', 'description')
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
    description = models.TextField(_('description'), blank=True, null=True)
    skill = models.ForeignKey(
        Skill,
        verbose_name=_('Skill'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('knowledge')
        verbose_name_plural = _('knowledge')

    def __str__(self):
        return self.name


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
    show_rules_in_combat = models.BooleanField(
        _('Show rules in combat'),
        default=False,
        help_text=_('Show the rule as combat action on the combat tab.'))
    show_in_attack_dice_rolls = models.BooleanField(
        _('Show in attack dice rolls'),
        default=False,
        help_text=_('Show the name in attack dice rolls.'))
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

    @admin.display(boolean=True)
    def has_quote(self):
        if self.quote:
            return True
        return False

    @admin.display(boolean=True)
    def has_rules(self):
        if self.rules:
            return True
        return False


class TemplateModifier(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(Template, verbose_name=_('template'), on_delete=models.CASCADE)
    aspect = models.CharField(
        verbose_name=_('aspect'),
        max_length=40,
        choices=CHARACTER_ASPECT_CHOICES,
        null=True,
        blank=True)
    aspect_modifier = models.IntegerField(
        verbose_name=_('aspect modifier'),
        blank=True,
        null=True)
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        verbose_name=_('attribute'),
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

    def __str__(self):
        return self.template.name


class TemplateRequirement(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(Template, verbose_name=_('template'), on_delete=models.CASCADE)
    required_template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name='required_template_requirement_set',
        blank=True,
        null=True)


class StatusEffect(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField('rules.Extension')
    is_active = models.BooleanField(_('is active'), default=True)
    fa_icon_class = models.CharField(_('FA Icon Class'), max_length=30, default='fas fa-book')
    name = models.CharField(_('name'), max_length=120)
    rules = models.TextField(_('rules'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'rules')
        verbose_name = _('status effect')
        verbose_name_plural = _('status effects')

    def __str__(self):
        return self.name

