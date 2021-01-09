# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import math
from decimal import Decimal

from django.db import models
from django.db.models import Sum, Max
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from armory.models import Item, RiotGear, Weapon
from horror.models import QuirkModifier
from rules.models import Skill, Template, TemplateCategory, TemplateModifier


class Character(models.Model):
    name = models.CharField(_('name'), max_length=80)
    description = models.TextField(_('description'), blank=True, null=True)
    image = models.ImageField(
        _('image'), upload_to='character_images', blank=True, null=True
    )
    backdrop_image = models.ImageField(
        _('backdrop image'), upload_to='character_backdrop_images', blank=True, null=True
    )

    created_by = models.ForeignKey(
        'auth.User',
        verbose_name=_('created by'),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_('Characters without user will be cleaned daily.'),
    )

    extensions = models.ManyToManyField(
        'rules.Extension', limit_choices_to={'is_mandatory': False}
    )

    lineage = models.ForeignKey(
        'rules.Lineage', verbose_name=_('lineage'), on_delete=models.CASCADE
    )

    reputation = models.IntegerField(_('reputation'), default=0)

    health = models.IntegerField(_('health'), default=6)
    boost = models.IntegerField(_('boost'), default=0)
    arcana = models.IntegerField(_('arcana'), default=3)
    stress = models.IntegerField(_('stress'), default=0)

    shadows = models.ManyToManyField('rules.Shadow', verbose_name=_('shadows'), blank=True)
    quirks = models.ManyToManyField('horror.Quirk', verbose_name=_('quirks'), blank=True)

    def __getattr__(self, item):
        if item.endswith('_roll'):
            name = item.replace("_roll", '')
            if name == 'intelligence':
                return (120 - self.intelligence) / 5
            else:
                value = getattr(self, name)
                return 5 - value if value <= 5 else 0
        return super().__getattr__(item)

    def __str__(self):
        return self.name

    def may_edit(self, user):
        if self.created_by == user:
            return True
        if not self.created_by:
            return True
        return False

    def get_absolute_url(self):
        return reverse('characters:detail', kwargs={'pk': self.id})

    def get_attribute_modifier(self, attribute_name):
        m = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.charactertemplate_set.all(),
            attribute=attribute_name).aggregate(Sum('attribute_modifier'))

        q = QuirkModifier.objects.filter(
            quirk__in=self.quirks.all(),
            attribute=attribute_name).aggregate(Sum('attribute_modifier'))
        return (m['attribute_modifier__sum'] or 0) + (q['attribute_modifier__sum'] or 0)

    def add_template(self, template):
        if not self.charactertemplate_set.filter(template=template).exists():
            self.charactertemplate_set.create(template=template)
            for tm in template.templatemodifier_set.all():
                if tm.knowledge is not None:
                    self.characterknowledge_set.get_or_create(knowledge=tm.knowledge)
                if tm.shadow is not None:
                    self.shadows.add(tm.shadow)

    def remove_template(self, template):
        self.charactertemplate_set.filter(template=template).delete()
        for tm in template.templatemodifier_set.all():
            if tm.knowledge is not None:
                self.characterknowledge_set.filter(knowledge=tm.knowledge).delete()
            if tm.shadow is not None:
                self.shadows.remove(tm.shadow)

    def get_epoch(self):
        return self.extensions.filter(is_mandatory=False, is_epoch=True).earliest('id')

    @property
    def extension_enabled(self):
        res = {}
        for e in self.extensions.all():
            res[e.identifier] = True
        return res

    @property
    def weaponless_attacks(self):
        return self.quickness

    @property
    def weaponless_minimum_roll(self):
        roll = 7 - self.characterskill_set.melee_combat_skill().value
        return roll if roll >= 2 else 2

    @property
    def weaponless_wounds(self):
        if self.strength > 3:
            return 2
        return 1

    @property
    def wounds_taken(self):
        return self.max_health - self.health

    @property
    def available_stress(self):
        return self.max_stress - self.stress

    @property
    def spell_points_spent(self):
        return 0

    @property
    def spell_points_available(self):
        return self.spell_points - self.spell_points_spent

    @property
    def reputation_spent(self):
        ts = self.charactertemplate_set.aggregate(Sum('template__cost'))
        tc = ts['template__cost__sum'] if ts is not None else 0
        return tc or 0

    @property
    def reputation_available(self):
        return self.reputation - self.reputation_spent

    def set_initial_reputation(self, initial_reputation=None):
        self.reputation = (
            self.reputation_spent if initial_reputation is None else initial_reputation
        )
        self.save()

    @property
    def actions(self):
        return 1 + math.ceil((self.quickness + self.deftness) / 2)

    @property
    def combat_walking_range(self):
        return self.quickness

    @property
    def combat_running_range(self):
        return self.combat_walking_range * 2

    @property
    def combat_crawling_range(self):
        return math.ceil(self.combat_walking_range / 2)

    @property
    def remaining_template_points(self):
        template_points = (
            self.lineage.lineagetemplatepoints_set.aggregate(Sum('points'))[
                'points__sum'
            ]
            or 0
        )
        spent_points = (
            self.charactertemplate_set.aggregate(Sum('template__cost'))[
                'template__cost__sum'
            ]
            or 0
        )
        return template_points - spent_points

    @property
    def spell_points(self):
        return self.lineage.base_spell_points + self.get_attribute_modifier('base_spell_points')

    @property
    def intelligence(self):
        return self.lineage.base_intelligence + self.get_attribute_modifier('base_intelligence')

    @property
    def max_health(self):
        return self.lineage.base_max_health + self.get_attribute_modifier('base_max_health')

    @property
    def max_stress(self):
        return self.lineage.base_max_stress + self.get_attribute_modifier('base_max_stress')

    @property
    def max_arcana(self):
        return self.lineage.base_max_arcana + self.get_attribute_modifier('base_max_arcana')

    @property
    def bonus_dice(self):
        return self.lineage.base_bonus_dice + self.get_attribute_modifier('base_bonus_dice')

    @property
    def destiny_dice(self):
        return self.lineage.base_destiny_dice + self.get_attribute_modifier('base_destiny_dice')

    @property
    def rerolls(self):
        return self.lineage.base_rerolls + self.get_attribute_modifier('base_rerolls')

    @property
    def deftness(self):
        return self.lineage.base_deftness + self.get_attribute_modifier('base_deftness')

    @property
    def strength(self):
        return self.lineage.base_strength + self.get_attribute_modifier('base_strength')

    @property
    def attractiveness(self):
        return self.lineage.base_attractiveness + self.get_attribute_modifier(
            'base_attractiveness'
        )

    @property
    def endurance(self):
        return self.lineage.base_endurance + self.get_attribute_modifier('base_endurance')

    @property
    def resistance(self):
        return self.lineage.base_resistance + self.get_attribute_modifier('base_resistance')

    @property
    def quickness(self):
        return self.lineage.base_quickness + self.get_attribute_modifier('base_quickness')

    @property
    def openness(self):
        return self.lineage.base_openness + self.get_attribute_modifier('base_openness')

    @property
    def conscientiousness(self):
        return self.lineage.base_conscientiousness + self.get_attribute_modifier(
            'base_conscientiousness'
        )

    @property
    def extraversion(self):
        return self.lineage.base_extraversion + self.get_attribute_modifier('base_extraversion')

    @property
    def agreeableness(self):
        return self.lineage.base_agreeableness + self.get_attribute_modifier(
            'base_agreeableness'
        )

    @property
    def neuroticism(self):
        return self.lineage.base_neuroticism + self.get_attribute_modifier('base_neuroticism')

    @property
    def ballistic_protection(self):
        bp = self.characterriotgear_set.aggregate(
           Sum('riot_gear__protection_ballistic')
        )['riot_gear__protection_ballistic__sum'] or 0
        return self.lineage.base_protection + bp

    @property
    def explosive_protection(self):
        return self.lineage.base_protection + self.characterriotgear_set.aggregate(
            Sum('riot_gear__protection_explosive')
        )['riot_gear__protection_explosive__sum'] or 0

    @property
    def evasion(self):
        return self.lineage.base_evasion

    @property
    def max_concealment(self):
        ic = self.characteritem_set.aggregate(
            Max('item__concealment')
        )['item__concealment__max'] or 0
        rc = self.characterriotgear_set.aggregate(
            Max('riot_gear__concealment')
        )['riot_gear__concealment__max'] or 0
        wc = 0
        for w in self.characterweapon_set.all():
            if w.modified_concealment > wc:
                wc = w.modified_concealment
        return max(ic, rc, wc)


class CharacterSkillQuerySet(models.QuerySet):
    def mind_skills(self):
        return self.filter(skill__kind='m')

    def practical_skills(self):
        return self.filter(skill__kind='p')

    def combat_skills(self):
        return self.filter(skill__show_on_combat_tab=True)

    def melee_combat_skill(self):
        return self.get(skill__name_en='Hand to Hand Combat')

    def ranged_combat_skill(self):
        return self.get(skill__name_en='Shooting')

    def hand_to_hand_combat_skill(self):
        return self.get(skill__name_en='Hand to Hand Combat')


class CharacterSkill(models.Model):
    objects = CharacterSkillQuerySet.as_manager()

    character = models.ForeignKey(Character, models.CASCADE)
    skill = models.ForeignKey('rules.Skill', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('skill__name_de',)

    def __str__(self):
        return "{} {}".format(self.skill.name, self.value)

    @property
    def value(self):
        s = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.character.charactertemplate_set.all(),
            skill=self.skill).aggregate(Sum('skill_modifier'))
        q = QuirkModifier.objects.filter(
            quirk__in=self.character.quirks.all(),
            skill=self.skill).aggregate(Sum('skill_modifier'))
        return self.base_value + (s['skill_modifier__sum'] or 0) + (q['skill_modifier__sum'] or 0)


class CharacterKnowledge(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    knowledge = models.ForeignKey('rules.Knowledge', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('knowledge__name_en',)

    def __str__(self):
        return "{} {}".format(self.knowledge.name, self.value)

    @property
    def value(self):
        q = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.character.charactertemplate_set.all()
        )
        q = q.filter(knowledge=self.knowledge).aggregate(Sum('knowledge_modifier'))
        return self.base_value + (q['knowledge_modifier__sum'] or 0)


class CharacterStatusEffect(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    status_effect = models.ForeignKey('rules.StatusEffect', models.CASCADE)
    base_value = models.IntegerField(_('base value'), default=0)

    class Meta:
        ordering = ('status_effect__ordering',)

    def __str__(self):
        return "{} {}".format(self.status_effect.name, self.value)

    @property
    def value(self):
        return self.base_value


class CharacterTemplate(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    template = models.ForeignKey('rules.Template', models.CASCADE)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ('template__category__sort_order',)

    def __str__(self):
        return self.template.name


class CharacterWeapon(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    weapon = models.ForeignKey('armory.Weapon', on_delete=models.CASCADE)
    modifications = models.ManyToManyField('armory.WeaponModification')
    condition = models.IntegerField(default=100)

    class Meta:
        ordering = ('weapon__id',)

    def attack_roll(self):
        mods = Decimal(0)
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='accuracy'):
                mods += wmm.modifier

        skill = self.character.characterskill_set.ranged_combat_skill()
        if self.weapon.is_hand_to_hand_weapon:
            skill = self.character.characterskill_set.hand_to_hand_combat_skill()

        roll = 7 - skill.value - mods - self.weapon.accuracy
        return roll if roll >= 2 else 2

    @property
    def modified_penetration(self):
        pen = self.weapon.penetration
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='penetration'):
                mods += wmm.modifier
        return pen + mods

    @property
    def modified_concealment(self):
        con = self.weapon.concealment
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='concealment'):
                mods += wmm.modifier
        return con + mods

    @property
    def modified_wounds(self):
        wounds = self.weapon.wounds
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='wounds'):
                mods += wmm.modifier
        return wounds + mods


class CharacterRiotGear(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    riot_gear = models.ForeignKey('armory.RiotGear', on_delete=models.CASCADE)
    condition = models.IntegerField(_('condition'), default=100)


class CharacterItemQuerySet(models.QuerySet):
    def usable_in_combat(self):
        return self.filter(item__usable_in_combat=True)

    def by_type(self):
        return self.order_by('item__type')


class CharacterItem(models.Model):
    objects = CharacterItemQuerySet.as_manager()

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    quantity = models.IntegerField(_('Quantity'), default=1)
    item = models.ForeignKey('armory.Item', on_delete=models.CASCADE)

    def use_roll(self):
        if self.item.type.name_en == 'Grenades':
            return 7 - self.character.characterskill_set.get(skill__name_en="Throwing").value
        if self.item.type.name_en == 'First Aid':
            return 7 - self.character.characterskill_set.get(skill__name_en="First Aid").value
        return 0


class CharacterSpell(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    spell = models.ForeignKey('magic.Spell', on_delete=models.CASCADE)
