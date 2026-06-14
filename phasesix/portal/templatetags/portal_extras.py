from django.template import Library
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html

from characters.utils import is_tirakan_world, phasesix_character_creation_url

register = Library()


@register.simple_tag
def focal_crop(obj, crop="center", field_name="image"):
    if hasattr(obj, "get_image_crop"):
        return obj.get_image_crop(crop, field_name)
    return crop


@register.simple_tag
def focal_position(obj, field_name="image"):
    if hasattr(obj, "get_image_focal_point"):
        return obj.get_image_focal_point(field_name)
    return "50% 50%"


@register.simple_tag(takes_context=True)
def focal_image_attrs(context, obj, field_name="image"):
    user = context.get("user")
    if not user or not user.is_staff or not getattr(obj, "pk", None):
        return ""
    image = getattr(obj, field_name, None)
    if not image:
        return ""
    x = getattr(obj, f"{field_name}_focal_x", None)
    y = getattr(obj, f"{field_name}_focal_y", None)
    if x is None or y is None:
        return ""
    return format_html(
        'data-focal-editor="true" data-focal-app="{}" data-focal-model="{}" '
        'data-focal-pk="{}" data-focal-field="{}" data-focal-src="{}" '
        'data-focal-x="{}" data-focal-y="{}"',
        obj._meta.app_label,
        obj._meta.model_name,
        obj.pk,
        field_name,
        image.url,
        x,
        y,
    )


@register.simple_tag
def image_url(obj, geometry="100x100", crop="center"):
    if hasattr(obj, "get_image_url"):
        if hasattr(obj, "get_image_crop") and getattr(obj, "image", None):
            crop = obj.get_image_crop(crop)
        return obj.get_image_url(geometry, crop)


@register.simple_tag
def backdrop_image_url(obj, geometry="100x100", crop="center"):
    if hasattr(obj, "get_backdrop_image_url"):
        if hasattr(obj, "get_image_crop") and getattr(obj, "backdrop_image", None):
            crop = obj.get_image_crop(crop, "backdrop_image")
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
        world = context["request"].world
    except AttributeError:
        world = None

    if is_tirakan_world(world):
        return reverse("characters:choose_character_ruleset")

    return phasesix_character_creation_url(world)


@register.simple_tag(takes_context=True)
def bottom_navigation_button(context, template_include):
    context.update({"template_include": template_include})
    return render_to_string("portal/_bottom_navigation_button.html", context.flatten())


@register.filter
def subtract(value, arg):
    return value - arg
