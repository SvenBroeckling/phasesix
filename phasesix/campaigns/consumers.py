import json

import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.conf import settings
from django.template.loader import render_to_string

from campaigns.models import Campaign, Roll
from campaigns.templatetags.campaign_extras import int_with_sign


def roll_and_send(
    character_id,
    roll_string,
    header,
    description,
    campaign_id=None,
    save_to=None,
    minimum_roll=None,
):
    from characters.dice import roll
    from characters.models import Character

    channel_layer = get_channel_layer()

    if not character_id and not campaign_id:
        return []

    if character_id:
        character = Character.objects.get(id=character_id)
        campaign = character.pc_or_npc_campaign
        ws_room_name = character.ws_room_name
        character_name = character.name
        minimum_roll = minimum_roll or character.minimum_roll
    else:
        character = None
        campaign = Campaign.objects.get(id=campaign_id)
        ws_room_name = campaign.ws_room_name
        character_name = campaign.name
        minimum_roll = minimum_roll or 5

    result = roll(roll_string)

    roll = Roll.objects.create(
        campaign=campaign,
        character=character,
        header=header,
        description=description,
        roll_string=roll_string,
        results_csv=",".join(str(i) for i in result["list"]),
        modifier=result["modifier"],
        minimum_roll=minimum_roll,
    )

    result_html = render_to_string(
        "campaigns/_dice_socket_results.html",
        {
            "roll": roll,
        },
    )

    if save_to is not None and character is not None:
        if save_to == "initiative":
            character.latest_initiative = roll.get_sum()
            character.save()

    async_to_sync(channel_layer.group_send)(
        ws_room_name,
        {
            "type": "dice_roll",
            "message": {
                "roll": roll.roll_string,
                "result_list": roll.get_dice_list(),
                "result_html": result_html,
                "header": roll.header,
                "description": roll.description,
                "character": character_name,
            },
        },
    )

    url = campaign.discord_webhook_url if campaign is not None else None
    if url is not None:
        dice_result = ", ".join(str(r) for r in roll.get_dice_list())
        if roll.modifier:
            dice_result += int_with_sign(roll.modifier)
        dice_result += f" = {roll.get_sum()}"

        json_data = {
            "content": f"**{header}** {dice_result}",
            "username": character_name,
        }
        if roll.description:
            json_data["embeds"] = [{"description": roll.description}]

        if character:
            json_data["avatar_url"] = f"{settings.BASE_URL}{character.get_image_url()}"
        elif campaign:
            json_data["avatar_url"] = f"{settings.BASE_URL}{campaign.get_image_url()}"

        requests.post(url, json=json_data)

    return roll.get_dice_list()


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
