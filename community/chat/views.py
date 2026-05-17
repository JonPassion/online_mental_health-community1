from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatRoom, Message, GroupMembership
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import models
from users.models import UserPresence, UserActivity, Notification


def has_room_access(user, room):
    """Check if user has access to a chat room"""
    # Room creator always has access
    if room.user == user:
        return True
    
    # Check if it's a direct message room involving this user
    if room.name.startswith('DM_'):
        try:
            user_ids = room.name.split('_')[1:]  # Skip 'DM_' prefix
            return str(user.id) in user_ids
        except:
            return False
    
    # Check if user is a member of a group room
    if room.is_group:
        return GroupMembership.objects.filter(room=room, user=user).exists()
    
    # Deny access by default for non-DM rooms
    return False
# Create your views here.

@login_required
def room_list(request):
    rooms = [room for room in ChatRoom.objects.all() if has_room_access(request.user, room)]
    return render(request, 'chat/room_list.html', {'rooms': rooms})


@login_required
def room(request, room_name):
    # Check if room exists and user has access
    try:
        room = ChatRoom.objects.get(name=room_name)
        if not has_room_access(request.user, room):
            return redirect('chat_index')
    except ChatRoom.DoesNotExist:
        return redirect('chat_index')
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Guest'
    })



@login_required
def chat_index(request):
    rooms = [room for room in ChatRoom.objects.all() if has_room_access(request.user, room)]
    return render(request, "chat/chat_index.html", {"rooms": rooms})

@login_required
def chatting(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user has access to this room
    if not has_room_access(request.user, room):
        return redirect('chat_index')
    
    rooms = [r for r in ChatRoom.objects.all() if has_room_access(request.user, r)]  # sidebar
    return render(request, "chat/chats_mini.html", {"room": room, "rooms": rooms})

@login_required
def send_message(request):
    if request.method == "POST":
        try:
            room_id = request.POST.get("room_id")
            content = request.POST.get("message")
            
            if not room_id or not content:
                return JsonResponse({"error": "room_id and message are required"}, status=400)
            
            room = get_object_or_404(ChatRoom, id=room_id)
            
            # Check if user has access to this room
            if not has_room_access(request.user, room):
                return JsonResponse({"error": "Access denied"}, status=403)
            
            # Create message
            message = Message.objects.create(
                room=room,
                user=request.user,
                content=content,
                timestamp=timezone.now()
            )
            
            # Update user presence and activity (with error handling)
            try:
                UserPresence.update_activity(request.user, room)
            except Exception as e:
                print(f"Error updating user presence: {e}")
            
            try:
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='message_sent',
                    description=f'Sent message in {room.name}',
                    related_object_id=message.id,
                    related_object_type='message'
                )
            except Exception as e:
                print(f"Error creating user activity: {e}")
            
            # Create notifications for other users in the room (with error handling)
            try:
                room_users = Message.objects.filter(room=room).values_list('user', flat=True).distinct()
                for user_id in room_users:
                    if user_id != request.user.id:
                        # Only notify users who have access to this room
                        other_user = User.objects.get(id=user_id)
                        if has_room_access(other_user, room):
                            Notification.objects.create(
                                recipient=other_user,
                                sender=request.user,
                                notification_type='new_message',
                                title=f'New message in {room.name}',
                                message=f'{request.user.username}: {content[:50]}...',
                                related_object_id=message.id,
                                related_object_type='message'
                            )
            except Exception as e:
                print(f"Error creating notifications: {e}")
            
            return JsonResponse({
                "id": message.id,
                "content": message.content,
                "user": message.user.username,
                "sent_by_me": True,
                "timestamp": message.timestamp.isoformat()
            })
        except Exception as e:
            print(f"Error in send_message: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def chat_dashboard(request):
    """Render the chat dashboard template with real users and rooms"""
    # Get all users except current user for contacts
    all_users = User.objects.exclude(id=request.user.id)
    
    # Get only accessible chat rooms
    rooms = [room for room in ChatRoom.objects.all() if has_room_access(request.user, room)]
    
    return render(request, 'chat_dash/chadashboard.html', {
        'all_users': all_users,
        'rooms': rooms,
        'user': request.user
    })

@login_required
def get_users(request):
    """API endpoint to get all users (except current user)"""
    users = User.objects.exclude(id=request.user.id).values('id', 'username', 'email')
    return JsonResponse(list(users), safe=False)

@login_required
def create_direct_room(request):
    """Create or get a direct message room between two users"""
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        other_user = get_object_or_404(User, id=user_id)
        
        # Look for existing room between these users
        room_name = f"DM_{request.user.id}_{other_user.id}"
        reverse_room_name = f"DM_{other_user.id}_{request.user.id}"
        
        room = ChatRoom.objects.filter(
            models.Q(name=room_name) | models.Q(name=reverse_room_name)
        ).first()
        
        if not room:
            # Create new direct message room
            room = ChatRoom.objects.create(
                name=room_name,
                user=request.user
            )
        
        return JsonResponse({"room_id": room.id})
    
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def get_chat_rooms(request):
    """API endpoint to get all accessible chat rooms"""
    rooms = [room for room in ChatRoom.objects.all() if has_room_access(request.user, room)]
    rooms_data = [{'id': room.id, 'name': room.name, 'is_group': room.is_group} for room in rooms]
    return JsonResponse(rooms_data, safe=False)


@login_required
def get_user_inbox(request):
    """Get all direct message conversations for current user"""
    # Find all DM rooms involving current user
    user_dm_rooms = []
    
    try:
        all_rooms = ChatRoom.objects.all()
        
        for room in all_rooms:
            # Verify user has access to this room
            if not has_room_access(request.user, room):
                continue
                
            if room.name.startswith('DM_'):
                try:
                    user_ids = room.name.split('_')[1:]  # Skip 'DM_' prefix
                    if str(request.user.id) in user_ids:
                        # Get the other user's ID
                        other_user_id = None
                        for uid in user_ids:
                            if uid != str(request.user.id):
                                other_user_id = int(uid)
                                break
                        
                        if other_user_id:
                            other_user = User.objects.get(id=other_user_id)
                            
                            # Get latest message in this conversation
                            latest_message = Message.objects.filter(room=room).order_by('-timestamp').first()
                            
                            # Count unread messages (simplified logic)
                            unread_count = 0
                            try:
                                if request.user.last_login:
                                    unread_count = Message.objects.filter(
                                        room=room,
                                        timestamp__gt=request.user.last_login
                                    ).exclude(user=request.user).count()
                            except:
                                unread_count = 0
                            
                            conversation_data = {
                                'room_id': room.id,
                                'other_user_id': other_user_id,
                                'other_username': other_user.username,
                                'other_email': other_user.email,
                                'latest_message': latest_message.content if latest_message else 'No messages yet',
                                'latest_timestamp': latest_message.timestamp.isoformat() if latest_message else None,
                                'unread_count': unread_count,
                                'total_messages': Message.objects.filter(room=room).count()
                            }
                            user_dm_rooms.append(conversation_data)
                except (ValueError, User.DoesNotExist, IndexError) as e:
                    print(f"Error processing room {room.name}: {e}")
                    continue
        
        # Sort by latest message timestamp
        user_dm_rooms.sort(key=lambda x: x['latest_timestamp'] or '', reverse=True)
        
        return JsonResponse({'conversations': user_dm_rooms})
    except Exception as e:
        print(f"Error in get_user_inbox: {e}")
        return JsonResponse({'conversations': [], 'error': str(e)})


@login_required
def get_conversation_messages(request, user_id):
    """Get all messages between current user and another user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Find the DM room between these users
    room_name1 = f"DM_{request.user.id}_{other_user.id}"
    room_name2 = f"DM_{other_user.id}_{request.user.id}"
    
    room = ChatRoom.objects.filter(
        models.Q(name=room_name1) | models.Q(name=room_name2)
    ).first()
    
    if not room:
        return JsonResponse({'messages': [], 'room_id': None})
    
    # Verify user has access to this room
    if not has_room_access(request.user, room):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Get all messages in this conversation
    messages = Message.objects.filter(room=room).order_by("timestamp")
    messages_data = [
        {
            "id": m.id,
            "user": m.user.username,
            "user_id": m.user.id,
            "content": m.content,
            "sent_by_me": m.user == request.user,
            "timestamp": m.timestamp.isoformat()
        } for m in messages
    ]
    
    return JsonResponse({
        'messages': messages_data,
        'room_id': room.id,
        'other_user': {
            'id': other_user.id,
            'username': other_user.username,
            'email': other_user.email
        }
    })

@login_required
def get_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user has access to this room
    if not has_room_access(request.user, room):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    messages = Message.objects.filter(room=room).order_by("timestamp")
    messages_data = [
        {
            "id": m.id,
            "user": m.user.username,
            "user_id": m.user.id,
            "content": m.content,
            "sent_by_me": m.user == request.user,
            "timestamp": m.timestamp.isoformat()
        } for m in messages
    ]
    return JsonResponse(messages_data, safe=False)


@login_required
def create_group(request):
    """Create a new group chat room"""
    if request.method == "POST":
        group_name = request.POST.get("group_name")
        
        if not group_name:
            return JsonResponse({"error": "Group name is required"}, status=400)
        
        # Check if group name already exists
        if ChatRoom.objects.filter(name=group_name).exists():
            return JsonResponse({"error": "Group name already exists"}, status=400)
        
        # Create the group room
        room = ChatRoom.objects.create(
            name=group_name,
            user=request.user,
            is_group=True
        )
        
        # Add creator as a member
        GroupMembership.objects.create(room=room, user=request.user)
        
        return JsonResponse({
            "success": True,
            "room_id": room.id,
            "room_name": room.name
        })
    
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def join_group(request):
    """Join an existing group chat room"""
    if request.method == "POST":
        room_id = request.POST.get("room_id")
        
        if not room_id:
            return JsonResponse({"error": "Room ID is required"}, status=400)
        
        room = get_object_or_404(ChatRoom, id=room_id)
        
        # Check if it's a group room
        if not room.is_group:
            return JsonResponse({"error": "This is not a group room"}, status=400)
        
        # Check if user is already a member
        if GroupMembership.objects.filter(room=room, user=request.user).exists():
            return JsonResponse({"error": "You are already a member of this group"}, status=400)
        
        # Add user to the group
        GroupMembership.objects.create(room=room, user=request.user)
        
        return JsonResponse({
            "success": True,
            "room_id": room.id,
            "room_name": room.name
        })
    
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def leave_group(request):
    """Leave a group chat room"""
    if request.method == "POST":
        room_id = request.POST.get("room_id")
        
        if not room_id:
            return JsonResponse({"error": "Room ID is required"}, status=400)
        
        room = get_object_or_404(ChatRoom, id=room_id)
        
        # Check if it's a group room
        if not room.is_group:
            return JsonResponse({"error": "This is not a group room"}, status=400)
        
        # Check if user is a member
        membership = GroupMembership.objects.filter(room=room, user=request.user).first()
        if not membership:
            return JsonResponse({"error": "You are not a member of this group"}, status=400)
        
        # Remove user from the group
        membership.delete()
        
        return JsonResponse({
            "success": True,
            "message": "You have left the group"
        })
    
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def get_group_members(request, room_id):
    """Get all members of a group"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user has access to this room
    if not has_room_access(request.user, room):
        return JsonResponse({"error": "Access denied"}, status=403)
    
    members = GroupMembership.objects.filter(room=room).select_related('user')
    members_data = [
        {
            "id": m.user.id,
            "username": m.user.username,
            "email": m.user.email,
            "joined_at": m.joined_at.isoformat()
        } for m in members
    ]
    
    return JsonResponse({"members": members_data})


@login_required
def get_all_groups(request):
    """Get all group rooms (for joining)"""
    groups = ChatRoom.objects.filter(is_group=True)
    groups_data = []
    
    for group in groups:
        # Check if user is already a member
        is_member = GroupMembership.objects.filter(room=group, user=request.user).exists()
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'is_member': is_member,
            'member_count': GroupMembership.objects.filter(room=group).count()
        })
    
    return JsonResponse({'groups': groups_data})