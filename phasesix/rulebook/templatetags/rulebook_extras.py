from django.template import Library, Template, Context

from rulebook.models import WorldBook
from worlds.models import World

register = Library()


@register.simple_tag
def rulebook_pdf_link(world, book, language):
    if not world:
        world = World.objects.get(is_default=True)

    world_book = WorldBook.objects.get(world=world, book=book)
    return getattr(world_book, f"pdf_{language}").url


@register.filter
def replace_book_variables(book_text, world):
    if not world:
        world = World.objects.get(is_default=True)

    template = Template(book_text)
    return template.render(Context({"world": world}))
