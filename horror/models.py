from django.db import models
from transmeta import TransMeta

from django.utils.translation import gettext_lazy as _

from characters.templatetags.characters_extras import color_value_span
from rules.models import CHARACTER_ASPECT_CHOICES, Skill, Attribute


class QuirkCategory(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=30)

    class Meta:
        ordering = ('id',)
        translate = ('name',)
        verbose_name = _('quirk category')
        verbose_name_plural = _('quirk categories')

    def __str__(self):
        return self.name


class Quirk(models.Model, metaclass=TransMeta):
    name = models.CharField(_('name'), max_length=60)
    category = models.ForeignKey(QuirkCategory, verbose_name=_("category"), on_delete=models.CASCADE)
    rules = models.TextField(_('rules'), blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        ordering = ('id',)
        translate = ('name', 'description', 'rules')
        verbose_name = _('quirk')
        verbose_name_plural = _('quirks')

    def __str__(self):
        return self.name

    def get_modifier_summary_html(self):
        html = ''
        for m in self.quirkmodifier_set.all():
            if m.aspect:
                html += '<i class="fas fa-sun"></i> {} {}<br>'.format(
                    m.get_aspect_display(),
                    color_value_span(m.aspect_modifier, 3, algebraic_sign=True))
            if m.attribute:
                html += '<i class="fas fa-asterisk"></i> {} {}<br>'.format(
                    m.attribute.name,
                    color_value_span(m.attribute_modifier, 3, algebraic_sign=True))
            if m.skill:
                html += '<i class="fas fa-hand-scissors"></i> {} {}<br>'.format(
                    m.skill,
                    color_value_span(m.skill_modifier, 3, algebraic_sign=True))
        return html


class QuirkModifier(models.Model, metaclass=TransMeta):
    quirk = models.ForeignKey(Quirk, verbose_name=_('quirk'), on_delete=models.CASCADE)
    aspect = models.CharField(
        verbose_name=_('aspect'),
        max_length=40,
        choices=CHARACTER_ASPECT_CHOICES,
        null=True,
        blank=True)
    aspect_modifier = models.IntegerField(
        verbose_name=_('aspect modifier'),
        blank=True,
        null=True)
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        verbose_name=_('attribute'),
        null=True,
        blank=True)
    attribute_modifier = models.IntegerField(
        verbose_name=_('attribute modifier'),
        blank=True,
        null=True)
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name=_('skill'),
        null=True,
        blank=True)
    skill_modifier = models.IntegerField(
        verbose_name=_('skill modifier'),
        blank=True,
        null=True)
