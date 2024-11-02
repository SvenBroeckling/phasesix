from django.template import Library

register = Library()


@register.inclusion_tag("armory/_riot_gear_protection_display.html")
def riot_gear_protection_display(riot_gear):
    return {"riot_gear": riot_gear}


@register.inclusion_tag("armory/_item_widget.html", takes_context=True)
def item_widget(context, item, character=None):
    context.update(
        {
            "item": item,
            "character": character,
        }
    )
    return context


@register.inclusion_tag("armory/_weapon_widget.html", takes_context=True)
def weapon_widget(context, weapon, character=None, add_button=False):
    context.update({"weapon": weapon, "character": character, "add_button": add_button})
    return context


@register.inclusion_tag("armory/_riot_gear_widget.html", takes_context=True)
def riot_gear_widget(context, riot_gear, character=None):
    context.update(
        {
            "riot_gear": riot_gear,
            "character": character,
        }
    )
    return context


@register.filter
def replace_keyword_value(description, value):
    return description.replace("{X}", str(value))
