from django.db import models
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta


class World(models.Model, metaclass=TransMeta):
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
