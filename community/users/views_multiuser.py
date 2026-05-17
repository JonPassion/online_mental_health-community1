from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Max
from datetime import timedelta
from .models import UserPresence, UserActivity, Notification
from chat.models import ChatRoom, Message
from posts.models import Post
from django.contrib.auth.models import User


@login_required
def update_presence(request):
    """Update user's online status and current activity"""
    room_id = request.POST.get('room_id')
    activity_type = request.POST.get('activity_type', 'active')
    
    room = None
    if room_id:
        room = get_object_or_404(ChatRoom, id=room_id)
    
    # Update presence
    presence = UserPresence.update_activity(request.user, room)
    
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        activity_type=activity_type,
        description=f"User is {activity_type} in {room.name if room else 'system'}",
        related_object_id=room_id,
        related_object_type='room'
    )
    
    return JsonResponse({
        'status': 'success',
        'presence': {
            'is_online': presence.is_online,
            'last_seen': presence.last_seen.isoformat(),
            'current_room': room.name if room else None
        }
    })


@login_required
def get_online_users(request):
    """Get list of online users with their current activities"""
    online_users = UserPresence.objects.filter(
        is_online=True,
        last_activity__gte=timezone.now() - timedelta(minutes=5)
    ).select_related('user', 'current_room')
    
    users_data = []
    for presence in online_users:
        users_data.append({
            'id': presence.user.id,
            'username': presence.user.username,
            'email': presence.user.email,
            'current_room': presence.current_room.name if presence.current_room else None,
            'last_activity': presence.last_activity.isoformat()
        })
    
    return JsonResponse({'online_users': users_data})


@login_required
def get_user_activities(request):
    """Get recent activities across the system"""
    activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:50]
    
    activities_data = []
    for activity in activities:
        activities_data.append({
            'user': activity.user.username,
            'activity_type': activity.activity_type,
            'description': activity.description,
            'timestamp': activity.timestamp.isoformat()
        })
    
    return JsonResponse({'activities': activities_data})


@login_required
def get_notifications(request):
    """Get user's unread notifications"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).select_related('sender').order_by('-created_at')
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'sender': notif.sender.username if notif.sender else 'System',
            'created_at': notif.created_at.isoformat()
        })
    
    return JsonResponse({'notifications': notifications_data})


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'status': 'success'})


@login_required
def create_notification(request):
    """Create a new notification (for system use)"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        notification_type = request.POST.get('notification_type')
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        recipient = get_object_or_404(User, id=recipient_id)
        
        notification = Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type=notification_type,
            title=title,
            message=message
        )
        
        return JsonResponse({
            'status': 'success',
            'notification_id': notification.id
        })
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def get_chat_stats(request):
    """Get real-time chat statistics"""
    stats = {
        'total_users': User.objects.count(),
        'online_users': UserPresence.objects.filter(is_online=True).count(),
        'active_rooms': ChatRoom.objects.annotate(
            recent_messages=Count('message', filter=Q(message__timestamp__gte=timezone.now() - timedelta(hours=1)))
        ).filter(recent_messages__gt=0).count(),
        'total_messages': Message.objects.count(),
        'recent_posts': Post.objects.filter(created_at__gte=timezone.now() - timedelta(hours=24)).count()
    }
    
    return JsonResponse(stats)


@login_required
def cleanup_offline_users(request):
    """Mark users as offline if they haven't been active"""
    cutoff_time = timezone.now() - timedelta(minutes=5)
    offline_presences = UserPresence.objects.filter(
        is_online=True,
        last_activity__lt=cutoff_time
    )
    
    count = 0
    for presence in offline_presences:
        presence.is_online = False
        presence.current_room = None
        presence.save()
        count += 1
    
    return JsonResponse({
        'status': 'success',
        'marked_offline': count
    })
