from django.urls import path
from . import views_profile as views
from . import views as main_views

app_name = "users"

urlpatterns = [
    # Authentication URLs
    path('auth/', main_views.auth_view, name='auth'),
    path('logout/', main_views.logout_view, name='logout'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    
    # Profile Picture Upload URLs
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('upload-cover-picture/', views.upload_cover_picture, name='upload_cover_picture'),
    path('remove-profile-picture/', views.remove_profile_picture, name='remove_profile_picture'),
    path('remove-cover-picture/', views.remove_cover_picture, name='remove_cover_picture'),
]
