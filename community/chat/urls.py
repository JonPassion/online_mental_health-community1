from django.urls import path
from . import views
from . import mini

app_name = "chat"

urlpatterns = [
    # General chat pages
    path('', views.chat_index, name='index'),
    path('room_list/', views.room_list, name='room_list'),
    path('dashboard/', views.chat_dashboard, name='dashboard'),

    # API endpoints
    path('api/users/', views.get_users, name='get_users'),
    path('api/rooms/', views.get_chat_rooms, name='get_chat_rooms'),
    path('api/inbox/', views.get_user_inbox, name='get_user_inbox'),
    path('api/conversation/<int:user_id>/', views.get_conversation_messages, name='get_conversation_messages'),
    path('api/groups/', views.get_all_groups, name='get_all_groups'),
    path('create-direct-room/', views.create_direct_room, name='create_direct_room'),
    path('create-group/', views.create_group, name='create_group'),
    path('join-group/', views.join_group, name='join_group'),
    path('leave-group/', views.leave_group, name='leave_group'),
    path('group-members/<int:room_id>/', views.get_group_members, name='get_group_members'),

    # Specific chat room by name (string)
    path('room/<str:room_name>/', views.room, name='room'),

    path('', views.chat_index, name='index'),
    path('chat/<int:room_id>/', views.chatting, name='chatting'),
    path('chat/send/', views.send_message, name='send_message'),
    path('chat/messages/<int:room_id>/', views.get_messages, name='get_messages'),

    # Dashboard mini apps
    path('mini_chats/', mini.mini_chats, name='mini_chats'),
    path('miniposts/', mini.miniposts, name='miniposts'),
]