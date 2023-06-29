from django.template import Library
from django.urls import reverse

register = Library()


@register.simple_tag(takes_context=True)
def active_if_url_name_matches(context, url_name, **kwargs):
    resolver_match = context['request'].resolver_match

    try:
        app_name, name = url_name.split(":")
    except ValueError:
        if resolver_match.url_name == url_name:
            if kwargs is not None and resolver_match.kwargs != kwargs:
                return ''
            return 'active'
    else:
        if app_name in resolver_match.app_name and resolver_match.url_name == name:
            if kwargs is not None and resolver_match.kwargs != kwargs:
                return ''
            return 'active'
    return ''


@register.simple_tag
def create_character_url(world):
    if not world or not world.extension:
        return reverse("characters:create_character")

    if not world.extension.fixed_epoch:
        return reverse(
            "characters:create_character_epoch",
            kwargs={"world_pk": world.extension.id}
        )

    if not world.extension.fixed_extensions.exists():
        return reverse(
            "characters:create_character_extensions",
            kwargs={"world_pk": world.extension.id, "epoch_pk": world.extension.fixed_epoch.id})

    return reverse(
        "characters:create_character_data",
        kwargs={"world_pk": world.extension.id, "epoch_pk": world.extension.fixed_epoch.id})


@register.simple_tag(takes_context=True)
def world_identifier(context):
    if not context['request'].world_configuration:
        return 'phasesix'
    return context['request'].world_configuration.world.extension.identifier
