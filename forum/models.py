from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

FORUM_LANGUAGE_CHOICES = (
    ('de', _('German')),
    ('en', _('English')),
)


class Board(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    name = models.CharField(_('name'), max_length=60)
    language = models.CharField(_('language'), max_length=2, choices=FORUM_LANGUAGE_CHOICES)
    is_staff_only = models.BooleanField(_('is staff only'), default=False)

    def __str__(self):
        return self.name

    def latest_thread(self):
        return self.thread_set.latest('created_at')


class Thread(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=60)

    def __str__(self):
        return self.name

    def latest_post(self):
        return self.post_set.latest('created_at')


class Post(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    text = models.TextField(_('text'))

