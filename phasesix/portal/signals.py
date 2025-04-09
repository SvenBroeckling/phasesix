from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from portal.models import Profile


@receiver(post_save, sender=User)
def create_profile_on_save(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
