from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class Campaign(models.Model):
    name = models.CharField(_('name'), max_length=80)
    image = models.ImageField(
        _('image'), upload_to='campaign_images', blank=True, null=True
    )
    backdrop_image = models.ImageField(
        _('backdrop image'), upload_to='campaign_backdrop_images', blank=True, null=True
    )
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
        'rules.Extension', limit_choices_to={'is_mandatory': False, 'is_epoch': False}
    )
    forbidden_templates = models.ManyToManyField('rules.Template')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('campaigns:detail', kwargs={'pk': self.id})


class Scene(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=80)
    text = models.TextField(_('text'), blank=True, null=True)

    npc = models.ManyToManyField('characters.Character')


class Handout(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=80)
    image = models.ImageField(
        _('image'), upload_to='campaign_handouts', blank=True, null=True
    )

