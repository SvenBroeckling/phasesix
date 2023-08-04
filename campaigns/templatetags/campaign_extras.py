from django.template import Library
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

from campaigns.models import Campaign

register = Library()


@register.simple_tag(takes_context=True)
def campaign_fragment(context, fragment_template):
    context = context.flatten()
    context["fragment_template"] = fragment_template
    return render_to_string(
        "campaigns/fragments/" + fragment_template + ".html", context=context
    )


@register.simple_tag(takes_context=True)
def user_campaigns(context, user):
    campaigns = Campaign.objects.for_world_configuration(
        context["request"].world_configuration
    )
    return campaigns.filter(created_by=user)


@register.simple_tag
def ws_room_url(room_name):
    if settings.DEBUG:
        return f"ws://localhost:8000/ws/campaign/{room_name}/"
    return f"wss://phasesix.org/ws/campaign/{room_name}/"


@register.filter
def int_with_sign(value):
    return "{:+}".format(int(value))


@register.simple_tag(takes_context=True)
def create_campaign_url(context):
    try:
        extension = context["request"].world_configuration.world.extension
    except AttributeError:
        extension = None

    if extension is not None:
        if extension.fixed_epoch:
            if extension.fixed_extensions.exists():
                return reverse(
                    "campaigns:create_data",
                    kwargs={
                        "world_pk": extension.id,
                        "epoch_pk": extension.fixed_epoch.id,
                    },
                )
            return reverse(
                "campaigns:create_extensions",
                kwargs={"world_pk": extension.id, "epoch_pk": extension.fixed_epoch.id},
            )
        return reverse("campaigns:create_epoch", kwargs={"world_pk": extension.id})
    return reverse("campaigns:create")
