from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import ChatRoom, Message
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create sample chat rooms and messages for testing'

    def handle(self, *args, **options):
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'is_active': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))

        # Create sample rooms
        rooms_data = [
            'Tech Enthusiasts 💻',
            'Health Club 💪', 
            'Developers Hub 👨‍💻',
            'Anna',
            'David',
            'Maya',
            'User #3278',
            'User #5409'
        ]

        for room_name in rooms_data:
            room, created = ChatRoom.objects.get_or_create(
                name=room_name,
                user=user,
                defaults={'name': room_name, 'user': user}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created room: {room.name}'))
                
                # Add some sample messages
                sample_messages = [
                    "Welcome to the chat!",
                    "How is everyone doing today?",
                    "Great to see you here!",
                    "This is a sample message.",
                ]
                
                for msg_text in sample_messages:
                    Message.objects.create(
                        room=room,
                        user=user,
                        content=msg_text,
                        timestamp=timezone.now()
                    )
                
                self.stdout.write(self.style.SUCCESS(f'Added sample messages to {room.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Room {room.name} already exists'))

        self.stdout.write(self.style.SUCCESS('Sample rooms and messages created successfully!'))
