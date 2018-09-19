from django.db import models

from simplemde.fields import SimpleMDEField
from django.utils.translation import ugettext as _
from transmeta import TransMeta


class Chapter(models.Model, metaclass=TransMeta):
    """
    A rulebook chapter
    """

    number = models.IntegerField(_('number'))
    name = models.CharField(_('name'), max_length=120)
    fa_icon_class = models.CharField(_('FA Icon Class'), max_length=30, default='fa fa-book')
    text = SimpleMDEField(_('text'), blank=True, null=True)
    extension = models.ForeignKey('rules.Extension', models.CASCADE)

    class Meta:
        translate = ('name', 'text')
        verbose_name = _('chapter')
        verbose_name_plural = _('chapters')
        ordering = ('number',)

    def __str__(self):
        return self.name

