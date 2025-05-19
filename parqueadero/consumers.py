import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ParqueaderoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Únete a un grupo de canales
        await self.channel_layer.group_add("parqueadero_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Sal del grupo de canales
        await self.channel_layer.group_discard("parqueadero_group", self.channel_name)

    # Recibe mensajes del WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Por ejemplo, reenvía el mensaje a todo el grupo
        await self.channel_layer.group_send(
            "parqueadero_group",
            {
                'type': 'parqueadero_message',
                'message': data['message']
            }
        )

    # Recibe mensajes del grupo
    async def parqueadero_message(self, event):
        message = event['message']

        # Enviar mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))



class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({'message': 'Conexión aceptada'}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        await self.send(text_data=json.dumps({'message': text_data}))
