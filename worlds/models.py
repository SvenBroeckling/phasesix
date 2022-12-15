import reversion
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from worlds.unique_slugify import unique_slugify


@reversion.register
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
    slug = models.SlugField(_('slug'), max_length=220, unique=True, null=True)

    description = models.TextField(_('description'), blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=True)
    extension = models.ForeignKey(
        'rules.Extension',
        verbose_name=_('extension'),
        help_text=_('The corresponding world extension, which is added to the characters.'),
        limit_choices_to={'type': 'w'},
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    image = models.ImageField(_('image'), upload_to='world_images', max_length=256, blank=True, null=True)
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

    def get_absolute_url(self):
        return reverse('worlds:detail', args=[self.slug])

    def get_image(self):
        if self.image:
            return {
                'image': self.image,
                'copyright': self.image_copyright,
                'copyright_url': self.image_copyright_url,
            }
        else:
            return None


class WikiPageQuerySet(models.QuerySet):
    def get_top_level(self):
        return self.filter(parent=None)


@reversion.register
class WikiPage(models.Model, metaclass=TransMeta):
    objects = WikiPageQuerySet.as_manager()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('created by'))

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    name = models.CharField(_('name'), max_length=120)
    slug = models.SlugField(_('slug'), max_length=220, unique=True)
    world = models.ForeignKey(
        'worlds.World',
        verbose_name=_('world'),
        help_text=_('The world this page belongs to.'),
        on_delete=models.CASCADE)

    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent'),
        help_text=_('The parent wiki page.'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    text = models.TextField(
        _('text'),
        help_text=_('The wiki page text. This may contain Wiki links.'),
        blank=True,
        null=True)

    image = models.ImageField(_('image'), upload_to='wiki_page_images', max_length=256, blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    is_active = models.BooleanField(_('is active'), default=True)
    ordering = models.IntegerField(_('ordering'), default=100)

    class Meta:
        ordering = ('ordering',)
        translate = ('name', 'text')
        verbose_name = _('wiki page')
        verbose_name_plural = _('wiki pages')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('world:wiki_page', kwargs={'world_slug': self.world.slug, 'slug': self.slug})

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.name_de))
        super().save(**kwargs)

    def may_edit(self, user):
        return user.is_superuser or user == self.created_by

    def get_image(self):
        if self.image:
            return {
                'image': self.image,
                'copyright': self.image_copyright,
                'copyright_url': self.image_copyright_url,
            }
        if self.parent and self.parent.image:
            return self.parent.get_image()

        return self.world.get_image()


@reversion.register
class WikiPageImage(models.Model):
    wiki_page = models.ForeignKey(
        'worlds.WikiPage',
        verbose_name=_('wiki page'),
        help_text=_('The wiki page the image belongs to.'),
        on_delete=models.CASCADE)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('created by'))

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)

    image = models.ImageField(_('image'), max_length=256, upload_to='wiki_page_images')
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    caption = models.CharField(_('caption'), max_length=120)
    slug = models.SlugField(_('slug'), max_length=220, unique=True, null=True)

    class Meta:
        verbose_name = _('wiki page image')
        verbose_name_plural = _('wiki page images')

    def __str__(self):
        return self.caption

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.caption))
        super().save(**kwargs)

    def get_wiki_tag(self):
        return '{{%s|w-25,float-end}}' % self.slug

    def may_edit(self, user):
        return user.is_superuser or user == self.wiki_page.created_by

    def get_image(self):
        return {
            'image': self.image,
            'caption': self.caption,
        }
