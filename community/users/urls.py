from django.urls import path
from . import views
from . import urls_multiuser

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile URLs
    path('', views.profile_view, name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('<str:username>/', views.profile_view, name='user_profile'),
    
    # Profile Picture Upload URLs
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('upload-cover-picture/', views.upload_cover_picture, name='upload_cover_picture'),
    path('remove-profile-picture/', views.remove_profile_picture, name='remove_profile_picture'),
    path('remove-cover-picture/', views.remove_cover_picture, name='remove_cover_picture'),
]

# Include multi-user functionality
urlpatterns += urls_multiuser.urlpatterns
