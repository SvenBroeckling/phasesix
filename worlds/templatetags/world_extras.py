from django.template import Library

register = Library()


@register.filter
def is_subpage_of(page, parent):
    return page.is_subpage_of(parent)


@register.simple_tag
def breadcrumbs(page):
    bc = [(page.world.name, page.world.get_absolute_url())]

    if page:
        pages = [(page.name, page.get_absolute_url())]

        parent = page.parent
        while parent:
            pages.append((parent.name, parent.get_absolute_url()))
            parent = parent.parent

        bc += pages[::-1]

    return bc


@register.inclusion_tag("worlds/_language_widget.html", takes_context=True)
def language_widget(context, language, character=None, add_button=False):
    context.update(
        {"language": language, "character": character, "add_button": add_button}
    )
    return context
