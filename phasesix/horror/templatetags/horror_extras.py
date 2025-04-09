from django.template import Library

register = Library()


@register.inclusion_tag("horror/_quirk_widget.html", takes_context=True)
def quirk_widget(context, quirk, character=None, add_button=False):
    context.update({"quirk": quirk, "character": character, "add_button": add_button})
    return context
