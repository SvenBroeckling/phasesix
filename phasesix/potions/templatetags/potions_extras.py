from django.template import Library

register = Library()


@register.inclusion_tag("potions/_recipe_widget.html", takes_context=True)
def recipe_widget(context, recipe, character=None, add_button=False):
    context.update(
        {
            "recipe": recipe,
            "character": character,
            "add_button": add_button,
        }
    )
    return context
