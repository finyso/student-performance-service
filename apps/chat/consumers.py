import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.accounts.models import ChatRoom, ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Проверка аутентификации
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        # Проверка доступа к комнате
        if not await self.check_user_access():
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connected to room {self.room_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected from room {self.room_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        sender = self.scope['user']
        room_id = int(self.room_id)
        
        if not message:
            return
        
        # Сохраняем сообщение
        saved_message = await self.save_message(room_id, sender, message)
        
        # Отправляем в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
                'sender_fullname': sender.get_full_name() or sender.username,
                'timestamp': saved_message.created_at.strftime('%H:%M'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_fullname': event['sender_fullname'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def check_user_access(self):
        try:
            room = ChatRoom.objects.get(id=int(self.room_id))
            return self.scope['user'] in room.participants.all()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, room_id, sender, message):
        room = ChatRoom.objects.get(id=room_id)
        chat_message = ChatMessage.objects.create(
            room=room,
            sender=sender,
            content=message
        )
        room.last_message_at = chat_message.created_at
        room.save(update_fields=['last_message_at'])
        return chat_message