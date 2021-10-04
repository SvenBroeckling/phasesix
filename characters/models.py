# -*- coding: utf-8 -*-
import math

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

    image = models.ImageField(_('image'), upload_to='character_images', blank=True, null=True)
    image_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    image_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    backdrop_image = models.ImageField(_('backdrop image'), upload_to='character_backdrop_images', blank=True,
                                       null=True)
    backdrop_copyright = models.CharField(_('image copyright'), max_length=40, blank=True, null=True)
    backdrop_copyright_url = models.CharField(_('image copyright url'), max_length=150, blank=True, null=True)

    created_by = models.ForeignKey(
        'auth.User',
        verbose_name=_('created by'),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_('Characters without user will be cleaned daily.')
    )

    extensions = models.ManyToManyField(
        'rules.Extension', limit_choices_to={'is_mandatory': False}
    )

    lineage = models.ForeignKey(
        'rules.Lineage', verbose_name=_('lineage'), on_delete=models.CASCADE
    )

    campaign = models.ForeignKey(
        'campaigns.Campaign', verbose_name=_('Campaign'), blank=True, null=True, on_delete=models.SET_NULL
    )

    reputation = models.IntegerField(_('reputation'), default=0)

    health = models.IntegerField(_('health'), default=6)
    boost = models.IntegerField(_('boost'), default=0)
    arcana = models.IntegerField(_('arcana'), default=3)
    stress = models.IntegerField(_('stress'), default=0)

    bonus_dice_used = models.IntegerField(_('Bonus dice used'), default=0)
    destiny_dice_used = models.IntegerField(_('Destiny dice used'), default=0)
    rerolls_used = models.IntegerField(_('Rerolls used'), default=0)

    quirks = models.ManyToManyField('horror.Quirk', verbose_name=_('quirks'), blank=True)

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

    def knowledge_dict(self):
        kd = {}
        for t in self.charactertemplate_set.all():
            for m in t.template.templatemodifier_set.all():
                if m.knowledge is not None:
                    if m.knowledge in kd.keys():
                        kd[m.knowledge] += m.knowledge_modifier if m.knowledge_modifier is not None else 0
                    else:
                        kd[m.knowledge] = m.knowledge_modifier
        return kd

    @property
    def templates_with_shadow_rules(self):
        return self.charactertemplate_set.filter(template__show_rules_in_shadows=True)

    @property
    def templates_with_combat_rules(self):
        return self.charactertemplate_set.filter(template__show_rules_in_shadows=True)

    def shadow_list(self):
        sl = []
        for t in self.charactertemplate_set.all():
            for m in t.template.templatemodifier_set.all():
                if m.shadow:
                    sl.append(m.shadow)
        return sl

    def add_template(self, template):
        if not self.charactertemplate_set.filter(template=template).exists():
            self.charactertemplate_set.create(template=template)

    def remove_template(self, template):
        self.charactertemplate_set.filter(template=template).delete()

    def get_epoch(self):
        return self.extensions.filter(is_mandatory=False, is_epoch=True).earliest('id')

    @property
    def extension_enabled(self):
        res = {}
        for e in self.extensions.all():
            res[e.identifier] = True
        return res

    @property
    def weaponless_attack_dice(self):
        bonus = 1 if self.quickness > 2 else 0
        return self.characterskill_set.melee_combat_skill().value + bonus

    @property
    def weaponless_bonus_wounds(self):
        if self.strength > 2:
            return 1
        return 0

    @property
    def wounds_taken(self):
        return self.max_health - self.health

    @property
    def arcana_used(self):
        return self.max_arcana - self.arcana

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
        return self.lineage.base_actions + self.get_attribute_modifier('base_actions')

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
    def bonus_dice_free(self):
        return self.bonus_dice - self.bonus_dice_used

    @property
    def destiny_dice_free(self):
        return self.destiny_dice - self.destiny_dice_used

    @property
    def rerolls_free(self):
        return self.rerolls - self.rerolls_used

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
    def education(self):
        return self.lineage.base_education + self.get_attribute_modifier('base_education')

    @property
    def conscientiousness(self):
        return self.lineage.base_conscientiousness + self.get_attribute_modifier(
            'base_conscientiousness'
        )

    @property
    def willpower(self):
        return self.lineage.base_willpower + self.get_attribute_modifier('base_willpower')

    @property
    def apprehension(self):
        return self.lineage.base_apprehension + self.get_attribute_modifier(
            'base_apprehension'
        )

    @property
    def charm(self):
        return self.lineage.base_charm + self.get_attribute_modifier('base_charm')

    @property
    def logic(self):
        return self.lineage.base_logic + self.get_attribute_modifier('base_logic')

    @property
    def ballistic_protection(self):
        bp = self.characterriotgear_set.aggregate(
            Sum('riot_gear__protection_ballistic')
        )['riot_gear__protection_ballistic__sum'] or 0
        return self.lineage.base_protection + self.get_attribute_modifier('base_protection') + bp

    @property
    def evasion(self):
        be = self.characterriotgear_set.aggregate(
            Sum('riot_gear__evasion')
        )['riot_gear__evasion__sum'] or 0
        return self.lineage.base_evasion + self.get_attribute_modifier('base_evasion') + be

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

    class Meta:
        ordering = ('skill__name_de',)

    def __str__(self):
        return "{} {}".format(self.skill.name, self.value)

    def attribute_value(self, attribute_name):
        return getattr(self.character, attribute_name)

    @property
    def value(self):
        s = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.character.charactertemplate_set.all(),
            skill=self.skill).aggregate(Sum('skill_modifier'))
        q = QuirkModifier.objects.filter(
            quirk__in=self.character.quirks.all(),
            skill=self.skill).aggregate(Sum('skill_modifier'))
        dom = self.attribute_value(self.skill.dominant_attribute)
        sup = self.attribute_value(self.skill.supplemental_attribute)
        attr_mod = math.ceil((dom + sup) / 2)
        return attr_mod + (s['skill_modifier__sum'] or 0) + (q['skill_modifier__sum'] or 0)


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
    capacity_used = models.IntegerField(_('capacity used'), default=0)

    class Meta:
        ordering = ('weapon__id',)

    def may_edit(self, user):
        return self.character.may_edit(user)

    def attack_modes(self):
        skill = self.character.characterskill_set.ranged_combat_skill()
        if self.weapon.is_hand_to_hand_weapon:
            skill = self.character.characterskill_set.hand_to_hand_combat_skill()

        bonus_dice = 0
        for wm in self.modifications.all():
            for wma in wm.weaponmodificationattributechange_set.all():
                if wma.attribute == 'bonus_dice':
                    bonus_dice += wma.attribute_modifier

        modes = []
        for wm in self.weapon.weaponattackmode_set.all():
            modes.append((wm.attack_mode.name, skill.value + wm.dice_bonus + bonus_dice, wm.id))

        return modes

    @property
    def modified_penetration(self):
        pen = self.weapon.penetration
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='penetration'):
                mods += wmm.attribute_modifier
        return pen + mods

    @property
    def modified_concealment(self):
        con = self.weapon.concealment
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='concealment'):
                mods += wmm.attribute_modifier
        return con + mods

    @property
    def modified_wounds(self):
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='wounds'):
                mods += wmm.attribute_modifier
        return self.weapon.wounds + mods

    @property
    def modified_range_meter(self):
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='range_meter'):
                mods += wmm.attribute_modifier
        return self.weapon.range_meter + mods

    @property
    def modified_capacity(self):
        base_capacity = self.weapon.capacity if self.weapon.capacity else 0
        mods = 0
        for wm in self.modifications.all():
            for wmm in wm.weaponmodificationattributechange_set.filter(attribute='capacity'):
                mods += wmm.attribute_modifier
        return base_capacity + mods

    @property
    def has_capacity(self):
        return self.modified_capacity > 0

    @property
    def capacity_available(self):
        return self.modified_capacity - self.capacity_used


class CharacterRiotGear(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    riot_gear = models.ForeignKey('armory.RiotGear', on_delete=models.CASCADE)
    condition = models.IntegerField(_('condition'), default=100)

    def may_edit(self, user):
        return self.character.may_edit(user)

    class Meta:
        ordering = ('riot_gear__id',)


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

    class Meta:
        ordering = ('item__id',)

    @property
    def use_skill(self):
        if self.item.type.name_en == 'Grenades':
            return self.character.characterskill_set.get(skill__name_en="Throwing")
        if self.item.type.name_en == 'First Aid':
            return self.character.characterskill_set.get(skill__name_en="First Aid")
        return None

    def may_edit(self, user):
        return self.character.may_edit(user)


class CharacterSpell(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    spell = models.ForeignKey('magic.BaseSpell', on_delete=models.CASCADE)
    custom_name = models.CharField(_('custom name'), max_length=30, null=True, blank=True)

    class Meta:
        ordering = ('spell__id',)

    def __str__(self):
        return self.spell.name

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def name(self):
        return self.custom_name if self.custom_name else self.spell.name

    @property
    def spell_type(self):
        return self.spell.type

    @property
    def variant(self):
        return self.spell.variant

    @property
    def power(self):
        return self.spell.power

    @property
    def range(self):
        return self.spell.range

    @property
    def actions(self):
        return self.spell.actions

    @property
    def is_ritual(self):
        return self.spell.is_ritual

    @property
    def arcana_cost(self):
        return self.spell.arcana_cost


class CharacterSpellTemplate(models.Model):
    character_spell = models.ForeignKey(CharacterSpell, on_delete=models.CASCADE)
    spell_template = models.ForeignKey('magic.SpellTemplate', on_delete=models.CASCADE)
