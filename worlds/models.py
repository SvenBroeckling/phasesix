from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta


class World(models.Model, metaclass=TransMeta):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('created by'))

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    name = models.CharField(_('name'), max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    extension = models.ForeignKey(
        'rules.Extension',
        verbose_name=_('extension'),
        help_text=_('The corresponding world extension, which is added to the characters.'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    image = models.ImageField(_('image'), upload_to='extension_images', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'description')
        verbose_name = _('world')
        verbose_name_plural = _('worlds')

    def __str__(self):
        return self.name

    def may_edit(self, user):
        return user.is_superuser or user == self.created_by


class WikiCategory(models.Model, metaclass=TransMeta):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('created by'))

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    name = models.CharField(_('name'), max_length=120)
    world = models.ForeignKey(
        'worlds.World',
        verbose_name=_('world'),
        help_text=_('The world this category belongs to.'),
        on_delete=models.CASCADE)
    description = models.TextField(_('description'), blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'description')
        verbose_name = _('wiki category')
        verbose_name_plural = _('wiki categories')

    def __str__(self):
        return self.name


class WikiPage(models.Model, metaclass=TransMeta):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('created by'))

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    name = models.CharField(_('name'), max_length=120)
    description = models.TextField(_('description'), blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    category = models.ForeignKey(
        'worlds.WikiCategory',
        verbose_name=_('category'),
        help_text=_('The category of the wiki page.'),
        on_delete=models.CASCADE)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'description')
        verbose_name = _('wiki page')
        verbose_name_plural = _('wiki pages')

    def __str__(self):
        return self.name