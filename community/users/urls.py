from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import urls_multiuser

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset URLs
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url='/users/password-reset/done/',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/users/password-reset/complete/',
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html',
         ),
         name='password_reset_complete'),
    
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
