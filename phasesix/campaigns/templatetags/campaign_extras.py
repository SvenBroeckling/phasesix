from django.conf import settings
from django.template import Library
from django.template.loader import render_to_string
from django.urls import reverse

from campaigns.models import Campaign

register = Library()


@register.simple_tag(takes_context=True)
def user_campaigns(context, user):
    campaigns = Campaign.objects.for_world(context["request"].world)
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
    return reverse("campaigns:create")


@register.inclusion_tag("campaigns/statistics/roll_list.html")
def roll_list(campaign, mode):
    return {"object_list": campaign.roll_set.order_by(f"-{mode}")[:5]}
