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
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    usable_in_combat = models.BooleanField(_('usable in combat'), default=False)

    image = models.ImageField(
        _('image'), max_length=256, upload_to='item_images/', null=True, blank=True)

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

    # def get_absolute_url(self):
    #     return reverse('armory:weapontype_detail', kwargs={'pk': self.id})

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


class WeaponAttackMode(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=100)

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

    attacks_per_action = models.IntegerField(_('attacks per action'))
    capacity = models.IntegerField(_('capacity'), null=True, blank=True)
    wounds = models.IntegerField(_('wounds'), default=0)
    penetration = models.IntegerField(_('penetration'), default=0)
    recoil_control = models.IntegerField(_('recoil control'), default=0)
    concealment = models.IntegerField(_('concealment'), default=0)
    accuracy = models.IntegerField(_('accuracy'), default=0)
    reload_actions = models.IntegerField(_('reload actions'), default=1)

    weight = models.DecimalField(_('weight'), decimal_places=2, max_digits=6)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=8)

    attack_modes = models.ManyToManyField(WeaponAttackMode, verbose_name=_('attack modes'))

    range_lower = models.CharField(_('lower range'), default='s', max_length=1, choices=RANGE_CHOICES)
    range_upper = models.CharField(_('upper range'), null=True, blank=True, max_length=1, choices=RANGE_CHOICES)

    image = models.ImageField(_('image'), max_length=256, upload_to='weapon_images/', null=True, blank=True)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('weapon')
        verbose_name_plural = _('weapons')

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse('armory:weapon_detail', kwargs={'pk': self.id})

    def display_wounds(self):
        if self.wounds < 0:
            return '-' * abs(self.wounds)
        return '+' * self.wounds


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
    type = models.ForeignKey(WeaponModificationType, on_delete=models.CASCADE)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=6)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('weapon modification')
        verbose_name_plural = _('weapon modification')

    def __str__(self):
        return self.name


class WeaponModificationAttributeChange(models.Model):
    ATTRIBUTES = [
        'attacks_per_action', 'capacity', 'wounds', 'penetration',
        'accuracy', 'weight', 'recoil_control', 'concealment', 'reload_actions']
    ATTRIBUTE_CHOICES = zip([_(a.replace('_', '')) for a in ATTRIBUTES], ATTRIBUTES)
    weapon_modification = models.ForeignKey(WeaponModification, on_delete=models.CASCADE)
    attribute = models.CharField(_('attribute'), max_length=40, choices=ATTRIBUTE_CHOICES)
    modifier = models.IntegerField(_('modifier'), default=0)

    def get_attribute_display(self):
        return _(Weapon._meta.get_field(self.attribute).verbose_name)

    def get_modifier_display(self):
        return "%+d" % self.modifier


class RiotGear(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField('rules.Extension')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True, null=True)
    weight = models.DecimalField(_('weight'), decimal_places=2, max_digits=6)
    price = models.DecimalField(_('price'), decimal_places=2, max_digits=6)
    protection_ballistic = models.IntegerField(_('protection ballistic'), default=0)
    protection_explosive = models.IntegerField(_('protection explosive'), default=0)
    concealment = models.IntegerField(_('concealment'), default=0)

    class Meta:
        translate = ('name', 'description')
        verbose_name = _('riot gear')
        verbose_name_plural = _('riot gear')

    def __str__(self):
        return self.name
