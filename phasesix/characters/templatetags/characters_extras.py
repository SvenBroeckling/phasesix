from django.core.exceptions import FieldError
from django.db.models import Q
from django.template import Library
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from armory.models import WeaponModificationType
from rules.models import Extension

register = Library()


@register.inclusion_tag("characters/_arcana_display.html")
def arcana_display(character):
    return {"character": character}


@register.inclusion_tag("characters/_dice_display.html")
def dice_display(character):
    return {"character": character}


@register.inclusion_tag("characters/_wound_display.html")
def wound_display(character):
    return {"character": character}


@register.inclusion_tag("characters/_protection_display.html")
def protection_display(character):
    return {"character": character}


@register.simple_tag
def color_value_span(value, max_value, invert=False, algebraic_sign=False):
    try:
        value = int(value)
        max_value = int(max_value)
    except (TypeError, ValueError):
        return mark_safe(value)
    color_classes = [80, 60, 40, 20, 0, -20, -40, -60]
    display_value = value

    if invert:
        value = max_value - value

    try:
        p = (value * 100) / max_value
    except ZeroDivisionError:  # max_value == 0
        p = 0

    p = 100 if p > 100 else p

    for color_class in color_classes:
        if p >= color_class:
            break
    else:
        color_class = 0
    color_class = (
        "p{}".format(color_class) if p >= 0 else "n{}".format(abs(color_class))
    )

    if algebraic_sign and value > 0:
        display_value = "+{}".format(display_value)

    return mark_safe(
        '<span class="color-{}">{}</span>'.format(color_class, display_value)
    )


@register.simple_tag
def display_modifications(character_weapon, identifier):
    if isinstance(character_weapon, FillProxyModel):
        return ""
    res = ""
    try:
        keyword = character_weapon.modified_keywords[identifier]
        res += "<span title='%s' class='text-success'>%s</span>" % (
            keyword["name"],
            keyword["value"],
        )
    except KeyError:
        return mark_safe(res)
    return mark_safe(res)


@register.simple_tag(takes_context=True)
def detail_fragment(context, fragment_template):
    context = context.flatten()
    context["fragment_template"] = fragment_template
    return render_to_string(
        "characters/fragments/" + fragment_template + ".html", context=context
    )


@register.simple_tag
def has_extensions(template, extensions):
    for e in template.extensions.all():
        if e in extensions or e.is_mandatory:
            return True
    return False


@register.filter
def for_extensions(queryset, extension_queryset):
    try:
        return queryset.filter(
            Q(extensions__id__in=extension_queryset.all())
            | Q(extensions__id__in=Extension.objects.filter(is_mandatory=True))
        )
    except FieldError:  # queryset without extensions
        return queryset


@register.simple_tag
def weaponmodification_type_valid_for_weapon(wmt, weapon):
    for wm in wmt.weaponmodification_set.all():
        if weapon.type in wm.available_for_weapon_types.all():
            return True
    return False


@register.simple_tag
def has_valid_weaponmodifications(weapon, character):
    for wmt in WeaponModificationType.objects.for_extensions(character.extensions):
        for wm in wmt.weaponmodification_set.all():
            if weapon.type in wm.available_for_weapon_types.all():
                return True
    return False


@register.simple_tag
def template_category_string(character, template_category, end="<br>"):
    tc = character.charactertemplate_set.filter(
        template__category__id=template_category
    ).order_by("template__cost")[:3]
    if tc.exists():
        return mark_safe(
            "<small><span>{}</span></small>{}".format(
                ", ".join([str(t.template) for t in tc]), end
            )
        )
    return ""


@register.filter
def to_range(value):
    if value:
        return range(int(value))
    return []


@register.filter
def status_effect_value(status_effect, character):
    from characters.models import CharacterStatusEffect

    try:
        obj = CharacterStatusEffect.objects.get(
            character=character, status_effect=status_effect
        )
        return obj.value
    except CharacterStatusEffect.DoesNotExist:
        return 0


@register.simple_tag
def character_knowledge_skill_value(character, knowledge):
    from characters.models import CharacterSkill

    try:
        return character.characterskill_set.get(skill=knowledge.skill).value
    except CharacterSkill.DoesNotExist:
        return 0


@register.simple_tag
def character_knowledge_value(character, knowledge):
    cnd = character.knowledge_dict().get(knowledge, None)
    if cnd is None:
        return None
    return character.characterskill_set.get(skill=knowledge.skill).value + cnd


@register.simple_tag
def character_attribute_value(character, attribute):
    return character.characterattribute_set.get(attribute=attribute).value


@register.simple_tag
def character_skill_value(character, skill):
    return character.characterskill_set.get(skill=skill).value


@register.simple_tag
def spell_type_attribute_dice_value(character, spell_type):
    from characters.models import CharacterAttribute, CharacterSkill

    attribute = spell_type.reference_attribute
    try:
        da = character.characterattribute_set.get(attribute=attribute).value
    except CharacterAttribute.DoesNotExist:
        da = 0

    try:
        sc = character.characterskill_set.spell_casting_skill().value
    except CharacterSkill.DoesNotExist:
        sc = 0

    return da + sc


@register.filter
def currency_quantity(object, currency_map_unit):
    return object.currency_quantity(currency_map_unit)


@register.simple_tag
def character_notes(character, user):
    if character.may_edit(user):
        return character.characternote_set.all()
    return character.characternote_set.filter(is_private=False)


@register.filter
def has_knowledge(character, knowledge):
    return character.knowledge_dict().get(knowledge, None) is not None


@register.filter
def for_world_configuration(qs, world_configuration):
    return qs.for_world_configuration(world_configuration)


# Character Sheet PDF


class FillProxyModel:
    def __getitem__(self, item):
        return "⠀"  # Unicode U+2800 invisible space

    def __getattr__(self, item):
        return "⠀"  # Unicode U+2800 invisible space


@register.filter
def cap_and_fill_queryset_to(qs, max_length):
    result = list(qs)[:max_length]
    while len(result) < max_length:
        result.append(FillProxyModel())
    return result


@register.filter
def fill_queryset_to(qs, max_length):
    result = list(qs)
    while len(result) < max_length:
        result.append(FillProxyModel())
    return result
