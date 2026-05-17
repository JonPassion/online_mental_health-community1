from django.urls import path
from . import views_multiuser

urlpatterns = [
    # Multi-user management URLs
    path('api/update-presence/', views_multiuser.update_presence, name='update_presence'),
    path('api/online-users/', views_multiuser.get_online_users, name='get_online_users'),
    path('api/user-activities/', views_multiuser.get_user_activities, name='get_user_activities'),
    path('api/notifications/', views_multiuser.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notification_id>/read/', views_multiuser.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/create/', views_multiuser.create_notification, name='create_notification'),
    path('api/chat-stats/', views_multiuser.get_chat_stats, name='get_chat_stats'),
    path('api/cleanup-offline/', views_multiuser.cleanup_offline_users, name='cleanup_offline_users'),
]
