from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from portal.email import email_brand_context, send_templated_email

FORUM_LANGUAGE_CHOICES = (
    ("de", _("German")),
    ("en", _("English")),
)


class ForumSettings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class BoardSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    board = models.ForeignKey("Board", on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)


class ThreadSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey("Thread", on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)


class ForumImage(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(_("image"), upload_to="forum_images/")


class Board(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    name = models.CharField(_("name"), max_length=60)
    language = models.CharField(
        _("language"), max_length=2, choices=FORUM_LANGUAGE_CHOICES
    )
    is_staff_only = models.BooleanField(_("is staff only"), default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("forum:board_detail", kwargs={"pk": self.id})

    def latest_thread(self):
        return self.thread_set.latest("created_at")


class Thread(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=60)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("forum:thread_detail", kwargs={"pk": self.id})

    def post_count(self):
        return self.post_set.all().count() - 1

    def earliest_post(self):
        return self.post_set.earliest("created_at")

    def latest_post(self):
        return self.post_set.latest("created_at")

    def notify_subscribers(self, post, request=None):
        subscribers = [s.user.email for s in self.threadsubscription_set.all()]
        subscribers += [s.user.email for s in self.board.boardsubscription_set.all()]
        subscribers = {s for s in subscribers if s}
        context = {"post": post}
        if request is not None:
            context.update(email_brand_context(request))
            context["thread_url"] = request.build_absolute_uri(self.get_absolute_url())
        else:
            context.update(
                {
                    "email_brand_name": "Phase Six",
                    "email_theme": {
                        "background": "#0c1118",
                        "surface": "#141c26",
                        "primary": "#4f8fdb",
                        "text": "#edf5fc",
                        "muted": "#b7c5d5",
                    },
                    "thread_url": f"{settings.BASE_URL}{self.get_absolute_url()}",
                }
            )
        for s in subscribers:
            send_templated_email(
                _("%(brand)s Forum: %(user)s answered to the thread %(thread)s")
                % {
                    "brand": context["email_brand_name"],
                    "user": post.created_by,
                    "thread": self,
                },
                "forum/subscription_notify_mail.txt",
                "forum/subscription_notify_mail.html",
                context,
                [s],
                fail_silently=True,
            )


class Post(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    text = models.TextField(_("text"))

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return self.thread.name
