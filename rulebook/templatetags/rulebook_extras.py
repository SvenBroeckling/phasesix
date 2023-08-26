from django.template import Library

from rulebook.models import WorldBook
from worlds.models import World

register = Library()


@register.simple_tag
def rulebook_pdf(world, book, language):
    if not world:
        world = World.objects.get(id=4)  # TODO: Fix id

    world_book = WorldBook.objects.get(
        world=world,
        book=book
    )
    return getattr(world_book, f"pdf_{language}").url
