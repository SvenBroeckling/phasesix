from django.template import Library
from django.template.loader import render_to_string
from django.urls import reverse

register = Library()


@register.simple_tag
def image_url(obj, geometry="100x100", crop="center"):
    if hasattr(obj, "get_image_url"):
        return obj.get_image_url(geometry, crop)


@register.simple_tag
def backdrop_image_url(obj, geometry="100x100", crop="center"):
    if hasattr(obj, "get_backdrop_image_url"):
        return obj.get_backdrop_image_url(geometry, crop)


@register.filter
def genitive_ending(value):
    if not isinstance(value, str):
        return value
    if value.endswith("s") or value.endswith("x"):
        return f"{value}’"
    return f"{value}s"


@register.simple_tag(takes_context=True)
def active_if_url_name_matches(context, url_name_list, **kwargs):
    resolver_match = context["request"].resolver_match

    for url_name in url_name_list.split(","):
        try:
            app_name, name = url_name.split(":")
        except ValueError:
            if resolver_match.url_name == url_name:
                if kwargs is not None and resolver_match.kwargs != kwargs:
                    return ""
                return "active"
        else:
            if app_name in resolver_match.app_name and resolver_match.url_name == name:
                if kwargs and resolver_match.kwargs != kwargs:
                    return ""
                return "active"
    return ""


@register.simple_tag(takes_context=True)
def create_character_url(context):
    try:
        world = context["request"].world_configuration.world
    except AttributeError:
        world = None

    if not world or not world.extension:
        return reverse("characters:create_character")

    if not world.extension.fixed_epoch:
        return reverse(
            "characters:create_character_epoch", kwargs={"world_pk": world.extension.id}
        )

    if not world.extension.fixed_extensions.exists():
        return reverse(
            "characters:create_character_extensions",
            kwargs={
                "world_pk": world.extension.id,
                "epoch_pk": world.extension.fixed_epoch.id,
            },
        )

    return reverse(
        "characters:create_character_data",
        kwargs={
            "world_pk": world.extension.id,
            "epoch_pk": world.extension.fixed_epoch.id,
        },
    )


@register.simple_tag(takes_context=True)
def bottom_navigation_button(context, template_include):
    context.update({"template_include": template_include})
    return render_to_string("portal/_bottom_navigation_button.html", context.flatten())
