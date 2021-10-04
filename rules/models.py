# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from transmeta import TransMeta

CHARACTER_ATTRIBUTE_CHOICES = (
    ('base_max_health', _('max health')),

    ('base_max_arcana', _('max arcana')),
    ('base_spell_points', _('spell points')),

    ('base_actions', _('actions')),
    ('base_protection', _('protection')),
    ('base_evasion', _('evasion')),

    ('base_bonus_dice', _('bonus dice')),
    ('base_destiny_dice', _('destiny dice')),
    ('base_rerolls', _('rerolls')),

    ('base_deftness', _('deftness')),
    ('base_strength', _('strength')),
    ('base_attractiveness', _('attractiveness')),
    ('base_endurance', _('endurance')),
    ('base_resistance', _('resistance')),
    ('base_quickness', _('quickness')),

    ('base_education', _('education')),
    ('base_logic', _('logic')),
    ('base_conscientiousness', _('conscientiousness')),
    ('base_willpower', _('willpower')),
    ('base_apprehension', _('apprehension')),
    ('base_charm', _('charm')),

    ('base_max_stress', _('max stress')),
)


BASE_ATTRIBUTE_CHOICES = (
    ('deftness', _('deftness')),
    ('strength', _('strength')),
    ('attractiveness', _('attractiveness')),
    ('endurance', _('endurance')),
    ('resistance', _('resistance')),
    ('quickness', _('quickness')),
    ('logic', _('logic')),
    ('education', _('education')),
    ('conscientiousness', _('conscientiousness')),
    ('willpower', _('willpower')),
    ('apprehension', _('apprehension')),
    ('charm', _('charm')),
)


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
    fa_icon_class = models.CharField(_('FA Icon Class'), max_length=30, default='fas fa-book')
    name = models.CharField(_('name'), max_length=120)
    identifier = models.CharField(_('identifier'), max_length=20)
    description = models.TextField(_('description'), blank=True, null=True)
    year_range = models.CharField(_('year range'), blank=True, null=True, max_length=50)

    image = models.ImageField(_('image'), upload_to='extension_images', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    is_active = models.BooleanField(_('is active'), default=True)
    is_epoch = models.BooleanField(_('is epoch'), default=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'description', 'year_range')
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

    base_max_health = models.IntegerField(_('max health'), default=6)

    base_max_arcana = models.IntegerField(_('max arcana'), default=0)
    base_spell_points = models.IntegerField(_('spell points'), default=0)

    base_actions = models.IntegerField(_('base actions'), default=2)

    base_bonus_dice = models.IntegerField(_('base bonus dice'), default=0)
    base_destiny_dice = models.IntegerField(_('base destiny dice'), default=0)
    base_rerolls = models.IntegerField(_('base rerolls'), default=0)

    # Base Values
    base_evasion = models.IntegerField(_('base evasion'), default=0)
    base_protection = models.IntegerField(_('base armor'), default=0)

    # physis
    base_deftness = models.IntegerField(_('base deftness'), default=1)
    base_strength = models.IntegerField(_('base strength'), default=1)
    base_attractiveness = models.IntegerField(_('base attractiveness'), default=1)
    base_endurance = models.IntegerField(_('base endurance'), default=1)
    base_resistance = models.IntegerField(_('base resistance'), default=1)
    base_quickness = models.IntegerField(_('base quickness'), default=1)

    # persona
    base_education = models.IntegerField(_('base education'), default=1)
    base_logic = models.IntegerField(_('base logic'), default=1)
    base_conscientiousness = models.IntegerField(_('base conscientiousness'), default=1)
    base_willpower = models.IntegerField(_('base willpower'), default=1)
    base_apprehension = models.IntegerField(_('base apprehension'), default=1)
    base_charm = models.IntegerField(_('base charme'), default=1)

    # horror
    base_max_stress = models.IntegerField(_('max stress'), default=6)

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

    dominant_attribute = models.CharField(
        _('dominant attribute'),
        choices=BASE_ATTRIBUTE_CHOICES,
        max_length=20,
        blank=True,
        null=True)
    supplemental_attribute = models.CharField(
        _('supplemental attribute'),
        choices=BASE_ATTRIBUTE_CHOICES,
        max_length=20,
        blank=True,
        null=True)

    @property
    def dominant_attribute_name(self):
        try:
            return next(filter(lambda x: x[0] == self.dominant_attribute, BASE_ATTRIBUTE_CHOICES))[1]
        except StopIteration:
            return ''

    @property
    def supplemental_attribute_name(self):
        try:
            return next(filter(lambda x: x[0] == self.supplemental_attribute, BASE_ATTRIBUTE_CHOICES))[1]
        except StopIteration:
            return ''

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
    skill = models.ForeignKey(
        Skill,
        verbose_name=_('Skill'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

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
    show_rules_in_shadows = models.BooleanField(
        _('Show rules in shadows'),
        default=False,
        help_text=_('Show the rule as shadow on the main character sheet.'))
    show_rules_in_combat = models.BooleanField(
        _('Show rules in combat'),
        default=False,
        help_text=_('Show the rule as combat action on the combat tab.'))
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


class StatusEffect(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField('rules.Extension')
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

