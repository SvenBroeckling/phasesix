import re

import bleach
import markdown
from django.template import Library
from django.utils.safestring import mark_safe
from sorl.thumbnail import get_thumbnail

from characters.models import Character
from rulebook.models import Chapter
from worlds.models import WikiPage, WikiPageImage

register = Library()


@register.inclusion_tag("rules/_modifier_widget.html")
def modifier_widget(qs, character=None, add_button=False):
    return {
        "qs": qs,
    }


@register.inclusion_tag("rules/_template_widget.html", takes_context=True)
def template_widget(context, template, character=None, add_button=False):
    context.update(
        {"template": template, "character": character, "add_button": add_button}
    )
    return context


@register.inclusion_tag("magic/_basespell_widget.html", takes_context=True)
def basespell_widget(context, basespell, character=None):
    context.update(
        {
            "basespell": basespell,
            "character": character,
        }
    )
    return context


@register.filter
def to_first_linebreak(value):
    try:
        return value.splitlines()[0]
    except IndexError:
        return ""


@register.filter
def phasesix_markup(value, safe_mode=True):
    if value is None:
        return ""

    # Insert two line breaks after a line that starts with a > and is followed by a line that doesn't start with a >
    # Markdown doesn't handle this case well, so we need to add the line breaks manually
    value = re.sub(r"(^>.*)(\n)([^>\n])", r"\1\n\n\3", value, flags=re.MULTILINE)

    html = markdown.markdown(value, extensions=["tables"])
    if safe_mode:
        html = bleach.clean(
            html,
            tags={
                "a",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "abbr",
                "acronym",
                "b",
                "br",
                "blockquote",
                "code",
                "em",
                "i",
                "img",
                "li",
                "ol",
                "strong",
                "ul",
                "p",
                "pre",
                "table",
                "thead",
                "tbody",
                "th",
                "td",
                "tr",
            },
            attributes={
                "a": ["href", "title"],
                "img": ["src", "alt"],
            },
        )
    return mark_safe(html)


@register.filter
def resolve_rulebook_chapter_links(value, mode="web"):
    if value is None or value == "":
        return ""

    def _repl_links(match_object):
        text = ""
        tag = match_object.group(0).strip("[]")
        if "|" in tag:
            try:
                tag, text = tag.split("|")
            except ValueError:
                tag = text = tag

        if mode == "web":
            try:
                obj = Chapter.objects.get(identifier=tag)
            except Chapter.DoesNotExist:
                return '<a href="#{}">{}</a>'.format(tag, text)
            return '<a href="{}">{}</a>'.format(obj.get_absolute_url(), text)
        return '<a href="#{}">{}</a>'.format(tag, text)

    tags_re = re.compile(r"\[\[([^\[])+\]\]", flags=re.UNICODE)
    value = re.sub(tags_re, _repl_links, value)
    return mark_safe(value)


@register.filter
def replace_wiki_tags(value, world):
    if value is None or value == "":
        return ""

    def _repl_tags(match_object):
        text = ""
        tag = match_object.group(0).strip("[]")
        if "|" in tag:
            try:
                tag, text = tag.split("|")
            except ValueError:
                tag = text = tag

        try:
            obj = WikiPage.objects.get(world=world, slug=tag)
        except WikiPage.DoesNotExist:
            return text

        return '<a href="{}">{}</a>'.format(obj.get_absolute_url(), text)

    def _repl_image_tags(match_object):
        formatters = ""
        tag = match_object.group(0).strip("{}")
        if "|" in tag:
            tag, formatters = tag.split("|")
        css = " ".join(formatters.split(","))

        try:
            obj = WikiPageImage.objects.get(wiki_page__world=world, slug=tag)
        except WikiPageImage.DoesNotExist:
            return ""

        image = get_thumbnail(obj.image, "800", crop="center", quality=99, format="PNG")

        return f"""
        <a
            data-gallery={obj.wiki_page.slug}
            class="invisible-link toggle-lightbox"
            href="{obj.image.url}">
            <img class="img-fluid {css}" src="{image.url}" alt="{obj.caption}" />
        </a>
        """

    tags_re = re.compile(r"\[\[([^\[])+\]\]", flags=re.UNICODE)
    image_tags_re = re.compile(r"\{\{.*\}\}", flags=re.UNICODE)

    value = re.sub(tags_re, _repl_tags, value)
    value = re.sub(image_tags_re, _repl_image_tags, value)

    return mark_safe(value)


@register.simple_tag
def latest_user_image(user):
    try:
        return (
            Character.objects.filter(created_by=user, image__isnull=False)
            .exclude(image="")
            .latest("id")
            .image
        )
    except Character.DoesNotExist:
        return None


@register.filter
def templates_for_world_configuration(qs, world_configuration):
    if world_configuration:
        qs = qs.for_world(world_configuration.world)
    return qs
