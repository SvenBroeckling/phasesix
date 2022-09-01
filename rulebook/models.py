from django.db import models
from django.utils.translation import ugettext_lazy as gt
from django.conf import settings
from transmeta import TransMeta

from homebrew.models import HomebrewModel


class ModelWithCreationInfo(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=gt('created by'))
    created_at = models.DateTimeField(gt('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(gt('modified at'), auto_now=True)

    class Meta:
        abstract = True


class Book(ModelWithCreationInfo, HomebrewModel, metaclass=TransMeta):
    name = models.CharField(gt('name'), max_length=40)
    ordering = models.IntegerField(gt('ordering'), default=0)

    image = models.ImageField(gt('image'), upload_to='book_images', blank=True, null=True)
    image_copyright = models.CharField(gt('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(gt('image copyright url'), max_length=150, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = 'ordering',
        translate = 'name',
        verbose_name = gt('book')
        verbose_name_plural = gt('books')


class Chapter(ModelWithCreationInfo, HomebrewModel, metaclass=TransMeta):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    name = models.CharField(gt('name'), max_length=40)
    number = models.IntegerField(gt('number'), default=1)
    fa_icon_class = models.CharField(gt('fa icon class'), max_length=32)
    text = models.TextField(gt('text'))

    image = models.ImageField(gt('image'), upload_to='chapter_images', blank=True, null=True)
    image_copyright = models.CharField(gt('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(gt('image copyright url'), max_length=150, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = 'number',
        translate = 'name', 'text'
        verbose_name = gt('chapter')
        verbose_name_plural = gt('chapters')
