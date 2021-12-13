import json

from asgiref.sync import async_to_sync

from characters.dice import roll
from channels.generic.websocket import WebsocketConsumer


class DiceConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'dice_{self.room_name}'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # websocket receive
    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        results = roll(data['roll'])

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'dice_roll',
                'message': {
                    'roll': data['roll'],
                    'results': results,
                    'header': data['header'],
                    'description': data['description'],
                    'character': data['character'],
                }
            }
        )

    # group receive
    def dice_roll(self, event):
        self.send(text_data=json.dumps(event))
