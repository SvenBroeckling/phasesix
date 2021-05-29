from django.db.models import Q
from django.template import Library
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from armory.models import WeaponModificationType
from rules.models import Extension

register = Library()


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
    color_class = "p{}".format(color_class) if p >= 0 else "n{}".format(abs(color_class))

    if algebraic_sign and value > 0:
        display_value = "+{}".format(display_value)

    return mark_safe('<span class="color-%s">%s</span>' % (
        color_class,
        display_value))


@register.simple_tag
def display_modifications(character_weapon, attribute):
    res = ''
    for wm in character_weapon.modifications.all():
        for wmm in wm.weaponmodificationattributechange_set.all():
            if wmm.attribute == attribute and wmm.attribute_modifier != 0:
                if attribute == 'concealment':
                    css_class = 'text-success' if wmm.attribute_modifier < 0 else 'text-danger'
                else:
                    css_class = 'text-danger' if wmm.attribute_modifier < 0 else 'text-success'
                res += ' <span title="%s" class="%s">%+d</span>' % (wm.name, css_class, wmm.attribute_modifier)
    return mark_safe(res)


@register.simple_tag(takes_context=True)
def detail_fragment(context, model_name, fragment_name):
    context = context.flatten()
    context['fragment_name'] = fragment_name
    context['model_name'] = model_name
    return render_to_string('characters/fragments/' + fragment_name + '.html', context=context)


@register.simple_tag
def has_extensions(template, extensions):
    for e in template.extensions.all():
        if e in extensions or e.is_mandatory:
            return True
    return False


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
def template_category_string(character, template_category, css="text-light"):
    tc = character.charactertemplate_set.filter(template__category__id=template_category)
    return mark_safe(
        '<span class="{}">{}</span>'.format(css, ", ".join([str(t.template) for t in tc]))
    )


@register.filter
def to_range(value):
    if value:
        return range(int(value))
    return []


@register.filter
def for_extensions(queryset, extension_queryset):
    return queryset.filter(
        Q(extensions__id__in=extension_queryset.all()) |
        Q(extensions__id__in=Extension.objects.filter(is_mandatory=True))
    )


@register.filter
def status_effect_value(status_effect, character):
    from characters.models import CharacterStatusEffect
    try:
        obj = CharacterStatusEffect.objects.get(character=character, status_effect=status_effect)
        return obj.value
    except CharacterStatusEffect.DoesNotExist:
        return 0


@register.simple_tag
def character_knowledge_skil_value(character, knowledge):
    return character.characterskill_set.get(skill=knowledge.skill).value