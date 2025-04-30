from django.contrib.staticfiles import finders
from django.template import Library, Template, Context

from rulebook.models import WorldBook
from worlds.models import World

register = Library()


@register.simple_tag
def create_toc_entries(bookmark_tree, indent=0):
    for i, (label, (page, _, _), children, status) in enumerate(bookmark_tree, 1):
        yield {
            "id": f"toc-{i}",
            "label": label.lstrip("0123456789."),
            "page": page + 1,
            "status": status,
            "indent": indent,
        }
        if children:
            yield from create_toc_entries(children, indent + 3)


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


@register.simple_tag
def local_static(path):
    """
    A template tag to return the local path to a static file,
    with behavior similar to Django's built-in {% static %} tag.
    """
    file_path = finders.find(path)
    if file_path:
        return file_path
    else:
        raise ValueError(f"Static file '{path}' could not be found.")
