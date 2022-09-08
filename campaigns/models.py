from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import hashlib


class Campaign(models.Model):
    CHARACTER_VISIBILITY_CHOICES = (
        ('G', _('GM Only')),
        ('A', _('All')),
    )
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
            'rules.Extension', limit_choices_to={'type': 'e', 'is_mandatory': False}, on_delete=models.CASCADE,
        related_name="campaign_epoch_set",
        verbose_name=_('Epoch')
    )
    extensions = models.ManyToManyField(
        'rules.Extension', limit_choices_to={'is_mandatory': False, 'type': 'x'}, blank=True
    )
    forbidden_templates = models.ManyToManyField('rules.Template', blank=True)

    discord_webhook_url = models.URLField(
        _('discord webhook url'),
        max_length=256,
        help_text=_("Create a discord webhook and paste it's url here to display dice results."),
        blank=True,
        null=True)

    currency_map = models.ForeignKey('armory.CurrencyMap', blank=True, null=True, on_delete=models.SET_NULL)

    character_visibility = models.CharField(
        _('character visibility'),
        max_length=1,
        default='G',
        choices=CHARACTER_VISIBILITY_CHOICES)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('campaigns:detail', kwargs={'pk': self.id})

    def may_edit(self, user):
        if self.created_by == user:
            return True
        return False

    @property
    def extension_string(self):
        return ", ".join([e.name for e in self.extensions.all()])

    @property
    def campaign_hash(self):
        return hashlib.md5(
            "{}{}{}".format(self.id, self.name, self.created_by.id).encode('utf-8')
        ).hexdigest()

    @property
    def invite_link(self):
        return settings.BASE_URL + reverse('campaigns:detail',
                                           kwargs={'pk': self.id, 'hash': self.campaign_hash})

    @property
    def ws_room_name(self) -> str:
        """Websocket room name"""
        return f'campaign-{self.id}'


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


class Roll(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    character = models.ForeignKey(
        'characters.Character',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    header = models.CharField(_('header'), max_length=120, blank=True, null=True)
    description = models.CharField(_('description'), max_length=120, blank=True, null=True)
    roll_string = models.CharField(_('roll string'), max_length=20, blank=True, null=True)
    results_csv = models.CharField(_('results_csv'), max_length=120)
