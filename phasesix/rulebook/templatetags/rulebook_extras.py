from django.contrib.staticfiles import finders
from django.utils.translation import gettext_lazy as _
from django.template import Library, Template, Context
from django.template.loader import render_to_string

from armory.models import Weapon, RiotGear, WeaponModification
from body_modifications.models import BodyModification
from horror.models import Quirk
from magic.models import BaseSpell, SpellTemplate
from rulebook.font_utils import get_accumulated_fonts_css
from rulebook.models import WorldBook
from worlds.models import World
from rules.models import Template as CharacterTemplate

register = Library()


@register.simple_tag
def create_toc_entries(bookmark_tree, indent=0):
    for i, (label, (page, _, _), children, status) in enumerate(bookmark_tree, 1):
        is_appendix = label.startswith("Appendix") or label.startswith("Anhang")
        yield {"id": f"toc-{i}", "label": label.lstrip("0123456789."), "page": page + 1,
               "status": status, "indent": indent, }
        if children and not is_appendix:
            yield from create_toc_entries(children, indent + 3)


@register.filter
def chapter_label_to_id(label):
    return label.replace(".", "-").replace(" ", "-").lower()


@register.simple_tag
def appendix(world_book, kind):
    template_name = f"rulebook/pdf/appendix/{kind}.html"
    object_list_map = {
        "templates": CharacterTemplate.objects.for_world(world_book.world).order_by(
            "category"),
        "weapons": Weapon.objects.for_world(world_book.world).order_by("type"),
        "weapon_modifications": WeaponModification.objects.for_world(
            world_book.world).order_by("type"),
        "riot_gear": RiotGear.objects.for_world(world_book.world).order_by("type"),
        "spells": BaseSpell.objects.order_by("origin"), "quirks": Quirk.objects.all(),
        "spell_templates": SpellTemplate.objects.order_by("category"),
        "body_modifications": BodyModification.objects.all(), }
    title_map = {"templates": _("Character Templates"), "weapons": _("Weapons"),
                 "weapon_modifications": _("Weapon Modifications"),
                 "riot_gear": _("Armor"), "spells": _("Spells"),
                 "spell_templates": _("Spell Templates"), "quirks": _("Quirks"),
                 "body_modifications": _("Body Modifications"), }
    return render_to_string(template_name, {"world_book": world_book,
                                            "object_list": object_list_map.get(kind),
                                            "title": title_map.get(kind), "kind": kind})


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


@register.simple_tag
def font_kits():
    return get_accumulated_fonts_css()
