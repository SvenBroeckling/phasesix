from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from transmeta import TransMeta

from rules.models import ExtensionSelectQuerySet, Extension


class ItemTypeQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(item__extensions__id__in=extension_rm.all()) |
            Q(item__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class ItemType(models.Model, metaclass=TransMeta):
    objects = ItemTypeQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('item type')
        verbose_name_plural = _('item types')

    def __str__(self):
        return self.name


class Item(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)
    type = models.ForeignKey(ItemType, verbose_name=_('type'), on_delete=models.CASCADE)
    weight = models.DecimalField(_('weight'), decimal_places=2, max_digits=6)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=6)
    concealment = models.IntegerField(_('concealment'), default=0)
    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    is_homebrew = models.BooleanField(_('is homebrew'), default=False)
    keep_as_homebrew = models.BooleanField(
        _('keep as homebrew'),
        help_text=_('This was not accepted as general item and is kept as homebrew.'),
        default=False)
    homebrew_campaign = models.ForeignKey(
        'campaigns.Campaign',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    usable_in_combat = models.BooleanField(_('usable in combat'), default=False)
    attribute = models.ForeignKey(
        'rules.Attribute',
        verbose_name=_('attribute for usage'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    skill = models.ForeignKey(
        'rules.Skill',
        verbose_name=_('skill for usage'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    knowledge = models.ForeignKey(
        'rules.Knowledge',
        verbose_name=_('knowledge for usage'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    dice_roll_string = models.CharField(
        _('dice role string'),
        blank=True,
        null=True,
        max_length=10,
        help_text=_('Shows a roll button at the item if not empty.'))

    image = models.ImageField(_('image'), max_length=256, upload_to='item_images/', null=True, blank=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('item')
        verbose_name_plural = _('items')

    def __str__(self):
        return self.name


class WeaponTypeQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(weapon__extensions__id__in=extension_rm.all()) |
            Q(weapon__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class WeaponType(models.Model, metaclass=TransMeta):
    objects = WeaponTypeQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('weapon type')
        verbose_name_plural = _('weapon types')

    def __str__(self):
        return self.name

    def get_first_image(self):
        return self.weapon_set.earliest('id').image


RANGE_CHOICES = (
    ('-', _('hand to hand 1m')),
    ('+', _('hand to hand 2m')),
    ('s', _('short')),
    ('m', _('mid')),
    ('l', _('long')),
    ('e', _('extreme')),
)


class AttackMode(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=100)
    dice_bonus = models.IntegerField(_('dice bonus'), default=1)
    capacity_consumed = models.IntegerField(_('capacity consumed'), default=1)

    class Meta:
        translate = ('name',)
        verbose_name = _('attack mode')
        verbose_name_plural = _('attack modes')

    def __str__(self):
        return self.name


class WeaponQuerySet(ExtensionSelectQuerySet):
    def with_price(self):
        return self.exclude(price=0).order_by('price')


class Weapon(models.Model, metaclass=TransMeta):
    objects = WeaponQuerySet.as_manager()

    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    is_hand_to_hand_weapon = models.BooleanField(
        _('is hand to hand weapon'), default=False)
    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)

    type = models.ForeignKey(WeaponType, verbose_name=_('type'), on_delete=models.CASCADE)

    bonus_dice = models.IntegerField(_('bonus dice'), default=0)
    capacity = models.IntegerField(_('capacity'), null=True, blank=True)
    wounds = models.IntegerField(_('bonus wounds'), default=0)
    piercing = models.IntegerField(_('piercing'), default=0)
    concealment = models.IntegerField(_('concealment'), default=0)
    reload_actions = models.IntegerField(_('reload actions'), default=1)

    weight = models.DecimalField(_('weight'), decimal_places=2, max_digits=6)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=8)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    is_homebrew = models.BooleanField(_('is homebrew'), default=False)
    keep_as_homebrew = models.BooleanField(
        _('keep as homebrew'),
        help_text=_('This was not accepted as general weapon and is kept as homebrew.'),
        default=False)
    homebrew_campaign = models.ForeignKey(
        'campaigns.Campaign',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    range_meter = models.IntegerField(_('range (meter)'), default=0)

    image = models.ImageField(_('image'), max_length=256, upload_to='weapon_images/', null=True, blank=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('weapon')
        verbose_name_plural = _('weapons')

    def __str__(self):
        return self.name


class WeaponAttackMode(models.Model):
    weapon = models.ForeignKey(
        Weapon,
        on_delete=models.CASCADE,
        verbose_name=_('Weapon'))
    attack_mode = models.ForeignKey(
        AttackMode,
        on_delete=models.CASCADE,
        verbose_name=_('Attack Mode'))
    dice_bonus_override = models.IntegerField(
        _('dice bonus override'),
        blank=True,
        null=True)
    capacity_consumed_override = models.IntegerField(
        _('capacity consumed override'),
        blank=True,
        null=True)

    class Meta:
        verbose_name = _('weapon attack mode')
        verbose_name_plural = _('weapon attack modes')

    def __str__(self):
        return f'{self.weapon} - {self.attack_mode}: {self.dice_bonus_override}'

    @property
    def dice_bonus(self):
        if self.dice_bonus_override:
            return self.dice_bonus_override
        return self.attack_mode.dice_bonus

    @property
    def capacity_consumed(self):
        if self.capacity_consumed_override:
            return self.capacity_consumed_override
        return self.attack_mode.capacity_consumed


class WeaponModificationTypeQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(weaponmodification__extensions__id__in=extension_rm.all()) |
            Q(weaponmodification__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class WeaponModificationType(models.Model, metaclass=TransMeta):
    objects = WeaponModificationTypeQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=20)
    description = models.TextField(_('description'), blank=True, null=True)
    unique_equip = models.BooleanField(
        _('unique equip'),
        default=False,
        help_text=_('A weapon may only have one modification of this type (i.E. sights)')
    )

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('weapon modification type')
        verbose_name_plural = _('weapon modification type')

    def __str__(self):
        return self.name


class WeaponModification(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField('rules.Extension')
    available_for_weapon_types = models.ManyToManyField(WeaponType)
    name = models.CharField(_('name'), max_length=40)
    description = models.TextField(_('description'), blank=True, null=True)
    rules = models.TextField(
        _('rules'),
        help_text=_('Rules for this weapon modification. May be blank if only attribute changes apply.'),
        blank=True,
        null=True)
    type = models.ForeignKey(WeaponModificationType, on_delete=models.CASCADE)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=6)

    class Meta:
        translate = ('name', 'description', 'rules')
        verbose_name = _('weapon modification')
        verbose_name_plural = _('weapon modification')

    def __str__(self):
        return self.name

    def extension_string(self):
        return ", ".join([e.identifier for e in self.extensions.all()])


class WeaponModificationAttributeChange(models.Model):
    ATTRIBUTE_CHOICES = (
        ('capacity', _('Capacity')),
        ('wounds', _('Bonus wounds')),
        ('bonus_dice', _('Bonus dice')),
        ('piercing', _('Piercing')),
        ('concealment', _('Concealment')),
        ('reload_actions', _('Reload actions')),
        ('range_meter', _('Range (meter)')),
    )
    weapon_modification = models.ForeignKey(WeaponModification, on_delete=models.CASCADE)
    attribute = models.CharField(_('attribute'), max_length=40, choices=ATTRIBUTE_CHOICES)
    attribute_modifier = models.IntegerField(_('attribute modifier'), default=0)
    status_effect = models.ForeignKey(
        'rules.StatusEffect',
        verbose_name=_('status effect'),
        limit_choices_to={'is_active': True},
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    status_effect_value = models.IntegerField(_('status effect value'), default=0)

    def get_attribute_display(self):
        try:
            return _(Weapon._meta.get_field(self.attribute).verbose_name)
        except FieldDoesNotExist:
            return 'UNKNOWN'

    def get_modifier_display(self):
        return "%+d" % self.attribute_modifier


class RiotGear(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField('rules.Extension')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)
    weight = models.DecimalField(_('weight'), decimal_places=2, max_digits=6)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=6)
    protection_ballistic = models.IntegerField(_('protection ballistic'), default=0)
    evasion = models.IntegerField(_('evasion'), default=0)
    concealment = models.IntegerField(_('concealment'), default=0)

    is_homebrew = models.BooleanField(_('is homebrew'), default=False)
    keep_as_homebrew = models.BooleanField(
        _('keep as homebrew'),
        help_text=_('This was not accepted as general riot gear and is kept as homebrew.'),
        default=False)
    homebrew_campaign = models.ForeignKey(
        'campaigns.Campaign',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('riot gear')
        verbose_name_plural = _('riot gear')

    def __str__(self):
        return self.name


class CurrencyMap(models.Model):
    name = models.CharField(_('name'), max_length=20)

    def __str__(self):
        return self.name


class CurrencyMapUnit(models.Model):
    FA_ICON_CLASS_CHOICES = (
        ('fas fa-coins', _('Coins')),
        ('fas fa-euro-sign', _('Euro')),
        ('fas fa-dollar-sign', _('Dollar')),
        ('fas fa-rupee-sign', _('Rupee')),
        ('fas fa-pound-sign', _('Pound')),
        ('fas fa-lira-sign', _('Lira')),
        ('fas fa-shekel-sign', _('Shekel')),
        ('fas fa-yen-sign', _('Yen')),
        ('fas fa-won-sign', _('Won')))
    COLOR_CLASS_CHOICES = (
        ('text-white', _('White')),
        ('text-success', _('Success')),
        ('text-primary', _('Primary')),
        ('text-secondary', _('Secondary')),
        ('text-warning', _('Warning')),
        ('text-danger', _('Danger')))
    currency_map = models.ForeignKey(CurrencyMap, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=20)
    color_class = models.CharField(max_length=30, default='text-warning', choices=COLOR_CLASS_CHOICES)
    fa_icon_class = models.CharField(
        _('FA Icon Class'),
        choices=FA_ICON_CLASS_CHOICES,
        max_length=30,
        default='fas fa-coins')

    class Meta:
        get_latest_by = 'id',
