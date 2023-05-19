from django.db import models
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from rules.models import ExtensionSelectQuerySet, Extension


class EntityCategoryQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(item__extensions__id__in=extension_rm.all()) |
            Q(item__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class EntityCategory(models.Model, metaclass=TransMeta):
    objects = EntityCategoryQuerySet.as_manager()

    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    ordering = models.IntegerField(_('ordering'), default=10)

    class Meta:
        ordering = '-ordering',
        translate = ('name', 'description')
        verbose_name = _('entity category')
        verbose_name_plural = _('entity categories')

    def __str__(self):
        return self.name


class Entity(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    category = models.ForeignKey(EntityCategory, on_delete=models.CASCADE)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    extensions = models.ManyToManyField('rules.Extension')
    wiki_page = models.ForeignKey('worlds.WikiPage', null=True, blank=True, on_delete=models.SET_NULL)

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

    name = models.CharField(_('name'), max_length=256)
    short_name = models.CharField(
        _('short name'),
        help_text=_('An optional short name for selections.'),
        blank=True,
        null=True,
        max_length=90)
    description = models.TextField(_('description'), blank=True, null=True)

    image = models.ImageField(_('image'), max_length=256, upload_to='entity_images/', null=True, blank=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        translate = ('name', 'short_name', 'description')
        verbose_name = _('entity')
        verbose_name_plural = _('entities')

    def __str__(self):
        return self.name

