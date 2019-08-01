from django.template import Library

register = Library()


@register.simple_tag
def inline_edit_modal():
    pass


@register.simple_tag(takes_context=True)
def inline_edit(context, app, model, field):
    pass