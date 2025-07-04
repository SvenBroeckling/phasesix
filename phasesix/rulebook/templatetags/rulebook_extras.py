from django.contrib.staticfiles import finders
from django.template import Library, Template, Context
from django.template.loader import render_to_string

from rulebook.appendixes import get_appendix_class
from rulebook.font_utils import get_accumulated_fonts_css
from rulebook.models import WorldBook
from worlds.models import World

register = Library()


@register.simple_tag
def create_toc_entries(bookmark_tree, indent=0):
    for i, (label, (page, _, _), children, status) in enumerate(bookmark_tree, 1):
        is_appendix = label.startswith("Appendix") or label.startswith("Anhang")
        yield {
            "id": f"toc-{i}",
            "label": label.lstrip("0123456789."),
            "page": page + 1,
            "status": status,
            "indent": indent,
        }
        if children and not is_appendix:
            yield from create_toc_entries(children, indent + 3)


@register.filter
def chapter_label_to_id(label):
    return label.replace(".", "-").replace(" ", "-").lower()


@register.simple_tag
def appendix(world_book, kind):
    template_name = f"rulebook/pdf/appendix/{kind}.html"
    appendix_class = get_appendix_class(kind)

    if appendix_class:
        appendix_instance = appendix_class(world_book)
        if not appendix_instance.included_in_world_book:
            return ""
        return render_to_string(
            template_name,
            {
                "world_book": world_book,
                "object_list": appendix_instance.get_queryset(),
                "appendix_image": appendix_instance.get_linked_chapter().image,
                "title": appendix_instance.title,
                "kind": kind,
            },
        )

    return ""


@register.simple_tag
def rulebook_pdf_link(world, book, language):
    if not world:
        world = World.objects.get(is_default=True)

    world_book = WorldBook.objects.get(world=world, book=book)
    return getattr(world_book, f"pdf_{language}").url


@register.filter
def render_book_as_template(book_text, world):
    if not world:
        world = World.objects.get(is_default=True)

    template = Template(book_text)
    return template.render(Context({"world_book": world.worldbook_set.first()}))


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


@register.simple_tag
def font_kits():
    return get_accumulated_fonts_css()
