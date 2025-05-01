import json

import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.conf import settings
from django.template.loader import render_to_string

from campaigns.models import Campaign, Roll
from campaigns.templatetags.campaign_extras import int_with_sign
from characters.dice import roll


def _send_roll_link_to_channel(ctx, roll_string, header):
    header_urlencoded = header.replace(" ", "%20")
    async_to_sync(get_channel_layer().group_send)(
        ctx["ws_room_name"],
        {
            "type": "tale_spire_roll_link",
            "message": {
                "url": f"talespire://dice/{header_urlencoded}/{roll_string}",
                "character": ctx["character_name"],
            },
        },
    )


def _send_to_channel(ctx, roll_obj):
    async_to_sync(get_channel_layer().group_send)(
        ctx["ws_room_name"],
        {
            "type": "dice_roll",
            "message": {
                "roll": roll_obj.roll_string,
                "result_list": roll_obj.get_dice_list(),
                "result_html": render_to_string(
                    "campaigns/_dice_socket_results.html", {"roll": roll_obj}
                ),
                "header": roll_obj.header,
                "description": roll_obj.description,
                "character": ctx["character_name"],
            },
        },
    )


def _send_to_discord(roll_obj, character_name, character=None, campaign=None):
    if not campaign or not campaign.discord_integration:
        return

    url = campaign.discord_webhook_url if campaign else None
    if not url:
        return

    dice_result = ", ".join(str(r) for r in roll_obj.get_dice_list())
    if roll_obj.modifier:
        dice_result += int_with_sign(roll_obj.modifier)
    dice_result += f" = {roll_obj.get_sum()}"

    json_data = {
        "content": f"**{roll_obj.header}** {dice_result}",
        "username": character_name,
    }
    if roll_obj.description:
        json_data["embeds"] = [{"description": roll_obj.description}]

    if character:
        json_data["avatar_url"] = f"{settings.BASE_URL}{character.get_image_url()}"
    elif campaign:
        json_data["avatar_url"] = f"{settings.BASE_URL}{campaign.get_image_url()}"

    requests.post(url, json=json_data)


def _get_roll_context(character_id, campaign_id, minimum_roll):
    from characters.models import Character

    if character_id:
        character = Character.objects.get(id=character_id)
        return {
            "character": character,
            "campaign": character.pc_or_npc_campaign,
            "ws_room_name": character.ws_room_name,
            "character_name": character.name,
            "minimum_roll": minimum_roll or character.minimum_roll,
        }

    campaign = Campaign.objects.get(id=campaign_id)
    return {
        "character": None,
        "campaign": campaign,
        "ws_room_name": campaign.ws_room_name,
        "character_name": campaign.name,
        "minimum_roll": minimum_roll or 5,
    }


def roll_and_send(
    character_id,
    roll_string,
    header,
    description,
    campaign_id=None,
    save_to=None,
    minimum_roll=None,
) -> list[int] | None:

    if not character_id and not campaign_id:
        return []

    ctx = _get_roll_context(character_id, campaign_id, minimum_roll)

    if not ctx["campaign"] or ctx["campaign"].roll_on_site:
        result = roll(roll_string)
        roll_obj = Roll.objects.create(
            campaign=ctx["campaign"],
            character=ctx["character"],
            header=header,
            description=description,
            roll_string=roll_string,
            results_csv=",".join(str(i) for i in result["list"]),
            modifier=result["modifier"],
            minimum_roll=ctx["minimum_roll"],
        )

        if save_to == "initiative" and ctx["character"]:
            ctx["character"].latest_initiative = roll_obj.get_sum()
            ctx["character"].save()

        _send_to_channel(ctx, roll_obj)
        _send_to_discord(
            roll_obj, ctx["character_name"], ctx["character"], ctx["campaign"]
        )
        return roll_obj.get_dice_list()

    if ctx["campaign"] and ctx["campaign"].tale_spire_integration:
        _send_roll_link_to_channel(ctx, roll_string, header)

    return None


class DiceConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        async_to_sync(self.channel_layer.group_add)(self.room_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )

    # websocket receive
    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        roll_and_send(
            data.get("character", None),
            data["roll"],
            data["header"],
            data["description"],
            data.get("campaign", None),
            data.get("save_to", None),
        )

    # group receive
    def dice_roll(self, event):
        self.send(text_data=json.dumps(event))

    def tale_spire_roll_link(self, event):
        self.send(text_data=json.dumps(event))
