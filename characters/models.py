# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from armory.models import Item, RiotGear, Weapon
from rules.models import Skill, Template, TemplateCategory, TemplateModifier


class Character(models.Model):
    name = models.CharField(_('name'), max_length=80)
    image = models.ImageField(
        _('image'), upload_to='character_images', blank=True, null=True
    )
    creation_mode = models.CharField(
        _('creation mode'), max_length=12, default='random'
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

    base_intelligence = models.IntegerField(_('intelligence'), default=100)
    base_max_health = models.IntegerField(_('max health'), default=6)

    health = models.IntegerField(_('health'), default=6)
    boost = models.IntegerField(_('boost'), default=0)

    # magic extension
    base_max_arcana = models.IntegerField(_('max arcana'), default=0)
    arcana = models.IntegerField(_('arcana'), default=3)
    base_spell_points = models.IntegerField(_('spell points'), default=0)

    # dice
    base_bonus_dice = models.IntegerField(_('base bonus dice'), default=0)
    base_destiny_dice = models.IntegerField(_('base destiny dice'), default=0)
    base_rerolls = models.IntegerField(_('base rerolls'), default=0)

    # physis
    base_deftness = models.IntegerField(_('base deftness'), default=1)
    base_strength = models.IntegerField(_('base strength'), default=1)
    base_attractiveness = models.IntegerField(_('base attractiveness'), default=1)
    base_endurance = models.IntegerField(_('base endurance'), default=1)
    base_resistance = models.IntegerField(_('base resistance'), default=1)
    base_quickness = models.IntegerField(_('base quickness'), default=1)

    # persona
    base_openness = models.IntegerField(_('base openness'), default=1)
    base_conscientiousness = models.IntegerField(_('base conscientiousness'), default=1)
    base_extraversion = models.IntegerField(_('base extraversion'), default=1)
    base_agreeableness = models.IntegerField(_('base agreeableness'), default=1)
    base_neuroticism = models.IntegerField(_('base neuroticism'), default=1)

    shadows = models.ManyToManyField('rules.Shadow', verbose_name=_('shadows'))

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
        q = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.charactertemplate_set.all()
        )
        q = q.filter(attribute=attribute_name).aggregate(Sum('attribute_modifier'))
        return q['attribute_modifier__sum'] or 0

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

    @property
    def extension_enabled(self):
        res = {}
        for e in self.extensions.all():
            res[e.identifier] = True
        return res

    @property
    def spell_points_spent(self):
        return 0

    @property
    def spell_points_available(self):
        return self.spell_points - self.spell_points_spent

    @property
    def reputation_spent(self):
        ts = self.charactertemplate_set.aggregate(Sum('template__cost'))
        return ts['template__cost__sum'] if ts is not None else 0

    @property
    def reputation_available(self):
        return self.reputation - self.reputation_spent

    def set_initial_reputation(self, initial_reputation=None):
        """Sets the reputation to the initial reputation, or to the spent reputation
        if no initial reputation is given (for draft and random characters) to start
        a new character with 0 reputation available"""
        self.reputation = (
            self.reputation_spent if initial_reputation is None else initial_reputation
        )
        self.save()

    @property
    def actions(self):
        return 1 + ((self.quickness + self.deftness) / 2)

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
        return self.base_spell_points + self.get_attribute_modifier('base_spell_points')

    @property
    def intelligence(self):
        return self.base_intelligence + self.get_attribute_modifier('base_intelligence')

    @property
    def max_health(self):
        return self.base_max_health + self.get_attribute_modifier('base_max_health')

    @property
    def max_arcana(self):
        return self.base_max_arcana + self.get_attribute_modifier('base_max_arcana')

    @property
    def bonus_dice(self):
        return self.base_bonus_dice + self.get_attribute_modifier('base_bonus_dice')

    @property
    def destiny_dice(self):
        return self.base_destiny_dice + self.get_attribute_modifier('base_destiny_dice')

    @property
    def rerolls(self):
        return self.base_rerolls + self.get_attribute_modifier('base_rerolls')

    @property
    def deftness(self):
        return self.base_deftness + self.get_attribute_modifier('base_deftness')

    @property
    def strength(self):
        return self.base_strength + self.get_attribute_modifier('base_strength')

    @property
    def attractiveness(self):
        return self.base_attractiveness + self.get_attribute_modifier(
            'base_attractiveness'
        )

    @property
    def endurance(self):
        return self.base_endurance + self.get_attribute_modifier('base_endurance')

    @property
    def resistance(self):
        return self.base_resistance + self.get_attribute_modifier('base_resistance')

    @property
    def quickness(self):
        return self.base_quickness + self.get_attribute_modifier('base_quickness')

    @property
    def openness(self):
        return self.base_openness + self.get_attribute_modifier('base_openness')

    @property
    def conscientiousness(self):
        return self.base_conscientiousness + self.get_attribute_modifier(
            'base_conscientiousness'
        )

    @property
    def extraversion(self):
        return self.base_extraversion + self.get_attribute_modifier('base_extraversion')

    @property
    def agreeableness(self):
        return self.base_agreeableness + self.get_attribute_modifier(
            'base_agreeableness'
        )

    @property
    def neuroticism(self):
        return self.base_neuroticism + self.get_attribute_modifier('base_neuroticism')

    def get_full_heart_range(self):
        return range(self.health)

    def get_empty_heart_range(self):
        return range(self.max_health - self.health)

    def get_boost_range(self):
        return range(self.boost)

    def get_arcana_range(self):
        return range(self.arcana)

    def get_ballistic_protection_range(self):
        return range(
            self.characterriotgear_set.aggregate(
                Sum('riot_gear__protection_ballistic')
            )['riot_gear__protection_ballistic__sum']
            or 0
        )

    def get_explosive_protection_range(self):
        return range(
            self.characterriotgear_set.aggregate(
                Sum('riot_gear__protection_explosive')
            )['riot_gear__protection_explosive__sum']
            or 0
        )

    def fill_basics(self):
        for skill in Skill.objects.all():
            self.characterskill_set.create(skill=skill, base_value=1)
            self.save()

    def fill_random(self):
        self.fill_basics()
        for tc in TemplateCategory.objects.all():
            if tc.template_set.all().for_extensions(self.extensions).exists():
                for i in range(random.randint(1, 3)):
                    self.add_template(
                        tc.template_set.all()
                        .for_extensions(self.extensions)
                        .order_by('?')[0]
                    )
        for i in range(random.randint(2, 4)):
            self.characterweapon_set.create(
                weapon=Weapon.objects.for_extensions(self.extensions).order_by('?')[0]
            )
        self.characterriotgear_set.create(
            riot_gear=RiotGear.objects.for_extensions(self.extensions).order_by('?')[0]
        )
        for i in range(random.randint(2, 4)):
            self.characteritem_set.create(
                item=Item.objects.for_extensions(self.extensions).order_by('?')[0]
            )


class CharacterSkillQuerySet(models.QuerySet):
    def mind_skills(self):
        return self.filter(skill__kind='m')

    def practical_skills(self):
        return self.filter(skill__kind='p')

    def combat_skills(self):
        return self.filter(skill__show_on_combat_tab=True)

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
        q = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.character.charactertemplate_set.all()
        )
        q = q.filter(skill=self.skill).aggregate(Sum('skill_modifier'))
        return self.base_value + (q['skill_modifier__sum'] or 0)


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
        return 7 - skill.value - mods - self.weapon.accuracy

    def penetration(self):
        pen = self.weapon.penetration
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='penetration'):
                mods += wmm.modifier
        return pen + mods

    def wounds_range(self):
        wounds = self.weapon.wounds
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='wounds'):
                mods += wmm.modifier
        return range(wounds + mods)



class CharacterRiotGear(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    riot_gear = models.ForeignKey('armory.RiotGear', on_delete=models.CASCADE)
    condition = models.IntegerField(_('condition'), default=100)


class CharacterItemQuerySet(models.QuerySet):
    def by_type(self):
        return self.order_by('item__type')


class CharacterItem(models.Model):
    objects = CharacterItemQuerySet.as_manager()

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    item = models.ForeignKey('armory.Item', on_delete=models.CASCADE)
    quantity = models.IntegerField(_('quantity'), default=1)
