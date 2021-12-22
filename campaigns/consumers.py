import json

from asgiref.sync import async_to_sync
from django.template.loader import render_to_string

from characters.dice import roll
from channels.generic.websocket import WebsocketConsumer


def roll_and_send(channel_layer, group_name, roll_string, header, description, character_name):
    result_list = roll(roll_string)
    result_html = render_to_string('campaigns/_dice_socket_results.html', {'results': result_list})

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'dice_roll',
            'message': {
                'roll': roll_string,
                'result_list': result_list,
                'result_html': result_html,
                'header': header,
                'description': description,
                'character': character_name,
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
        roll_and_send(
            self.channel_layer,
            self.room_name,
            data['roll'],
            data['header'],
            data['description'],
            data['character'])

    # group receive
    def dice_roll(self, event):
        self.send(text_data=json.dumps(event))
