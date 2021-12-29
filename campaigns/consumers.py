import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string

from channels.generic.websocket import WebsocketConsumer


def roll_and_send(character_id, roll_string, header, description):
    from characters.dice import roll
    from characters.models import Character
    channel_layer = get_channel_layer()
    character = Character.objects.get(id=character_id)

    result_list = roll(roll_string)
    result_html = render_to_string(
        'campaigns/_dice_socket_results.html',
        {
            'results': result_list,
            'character': character,
        }
    )

    if character.campaign is not None:
        character.campaign.roll_set.create(
            character=character,
            header=header,
            description=description,
            roll_string=roll_string,
            results_csv=",".join(str(i) for i in result_list))

    async_to_sync(channel_layer.group_send)(
        character.ws_room_name,
        {
            'type': 'dice_roll',
            'message': {
                'roll': roll_string,
                'result_list': result_list,
                'result_html': result_html,
                'header': header,
                'description': description,
                'character': character.name,
            }
        }
    )
    return result_list


class DiceConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name,
            self.channel_name
        )

    # websocket receive
    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        roll_and_send(data['character'], data['roll'], data['header'], data['description'])

    # group receive
    def dice_roll(self, event):
        self.send(text_data=json.dumps(event))
