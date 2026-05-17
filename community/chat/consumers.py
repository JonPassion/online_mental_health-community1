import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message, GroupMembership
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Check if user has access to this room
        has_access = await self.check_room_access(self.scope["user"], self.room_name)
        if not has_access:
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        
        # Verify the username matches the authenticated user
        if username != self.scope["user"].username:
            await self.send(text_data=json.dumps({'error': 'Username mismatch'}))
            return

        await self.save_message(self.scope["user"], self.room_name, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username']
        }))

    @sync_to_async
    def check_room_access(self, user, room_name):
        """Check if user has access to a chat room"""
        try:
            room = ChatRoom.objects.get(name=room_name)
            
            # Room creator always has access
            if room.user == user:
                return True
            
            # Check if it's a direct message room involving this user
            if room_name.startswith('DM_'):
                try:
                    user_ids = room_name.split('_')[1:]  # Skip 'DM_' prefix
                    return str(user.id) in user_ids
                except:
                    return False
            
            # Check if user is a member of a group room
            if room.is_group:
                return GroupMembership.objects.filter(room=room, user=user).exists()
            
            # Deny access by default for non-DM rooms
            return False
        except ChatRoom.DoesNotExist:
            return False

    @sync_to_async
    def save_message(self, user, room, message):
        room_obj = ChatRoom.objects.get(name=room)
        Message.objects.create(user=user, room=room_obj, content=message)
