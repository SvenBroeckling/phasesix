from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import hashlib


class Campaign(models.Model):
    name = models.CharField(_('name'), max_length=80)
    image = models.ImageField(_('image'), upload_to='campaign_images', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    backdrop_image = models.ImageField(_('backdrop image'), upload_to='campaign_backdrop_images', blank=True, null=True)
    backdrop_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    backdrop_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)
    abstract = models.TextField(_('abstract'), blank=True, null=True)

    created_by = models.ForeignKey(
        'auth.User',
        verbose_name=_('created by'),
        on_delete=models.CASCADE
    )

    epoch = models.ForeignKey(
        'rules.Extension', limit_choices_to={'is_epoch': True}, on_delete=models.CASCADE,
        related_name="campaign_epoch_set",
        verbose_name=_('Epoch')
    )
    extensions = models.ManyToManyField(
        'rules.Extension', limit_choices_to={'is_mandatory': False, 'is_epoch': False}, blank=True
    )
    forbidden_templates = models.ManyToManyField('rules.Template')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('campaigns:detail', kwargs={'pk': self.id})

    def get_campaign_hash(self):
        return hashlib.md5(
            "{}{}{}".format(self.id, self.name, self.created_by.id).encode('utf-8')
        ).hexdigest()

    def get_invite_link(self):
        return settings.BASE_URL + reverse('campaigns:invitation',
                                           kwargs={'pk': self.id, 'hash': self.get_campaign_hash()})


class Scene(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=80)
    text = models.TextField(_('text'), blank=True, null=True)

    npc = models.ManyToManyField('characters.Character')


class Handout(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=80)
    image = models.ImageField(_('image'), upload_to='campaign_handouts', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

