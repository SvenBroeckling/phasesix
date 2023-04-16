from django.template import Library

from worlds.models import World, WikiPage

register = Library()


@register.simple_tag
def get_active_worlds():
    return World.objects.filter(is_active=True)


@register.simple_tag
def get_top_level_pages_for_world(world):
    return WikiPage.objects.filter(world=world, parent__isnull=True)


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
