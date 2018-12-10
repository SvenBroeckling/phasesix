from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

FORUM_LANGUAGE_CHOICES = (
    ('de', _('German')),
    ('en', _('English')),
)


class ForumSettings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class BoardSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    board = models.ForeignKey('Board', on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)


class ThreadSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)


class Board(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    name = models.CharField(_('name'), max_length=60)
    language = models.CharField(_('language'), max_length=2, choices=FORUM_LANGUAGE_CHOICES)
    is_staff_only = models.BooleanField(_('is staff only'), default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('forum:board_detail', kwargs={'pk': self.id})

    def latest_thread(self):
        return self.thread_set.latest('created_at')


class Thread(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=60)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('forum:thread_detail', kwargs={'pk': self.id})

    def latest_post(self):
        return self.post_set.latest('created_at')

    def notify_subscribers(self, post):
        subscribers = [s.user.email for s in self.threadsubscription_set.all()]
        subscribers += [s.user.email for s in self.board.boardsubscription_set.all()]
        subscribers = set([s for s in subscribers if s])
        for s in subscribers:
            send_mail(
                _('PhaseSix Forum: %(user)s answered to the thread %(thread)s') % {
                    'user': post.created_by,
                    'thread': self,
                },
                render_to_string('forum/subscription_notify_mail.html', {'post': post}),
                settings.DEFAULT_FROM_EMAIL,
                [s],
                fail_silently=True)


class Post(models.Model):
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    text = models.TextField(_('text'))
