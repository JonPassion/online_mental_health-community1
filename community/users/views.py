from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import UserRegisterForm
from .models import UserProfile

def auth_view(request):
    mode = request.GET.get("mode", "login")

    # --- Handle LOGIN ---
    if request.method == "POST" and mode == "login":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Check for 'next' parameter to redirect to original page
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)

            # Redirect based on role
            if user.is_staff or user.is_superuser:
                return redirect("dashboards:admin_dashboard")
            else:
                return redirect("dashboards:user_dashboard")
        else:
            messages.error(request, "Invalid username or password.")

    # --- Handle SIGNUP ---
    elif request.method == "POST" and mode == "signup":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect("/users/auth/?mode=login")

    return render(request, "users/auth.html", {"mode": mode})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("/users/auth/?mode=login")


@login_required
def profile_view(request, username=None):
    """View user profile"""
    if username:
        # View another user's profile
        user_profile = get_object_or_404(UserProfile, user__username=username)
        is_owner = False
    else:
        # View own profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        is_owner = True
    
    # Get user statistics
    from chat.models import ChatRoom, Message
    from posts.models import Post
    
    profile_user = user_profile.user
    
    # Message statistics
    messages_sent = Message.objects.filter(user=profile_user).count()
    rooms_created = ChatRoom.objects.filter(user=profile_user).count()
    
    # Post statistics
    posts_created = Post.objects.filter(author=profile_user).count()
    
    # Recent activity
    from .models import UserActivity
    recent_activities = UserActivity.objects.filter(
        user=profile_user
    ).order_by('-timestamp')[:10]
    
    # Online status
    from .models import UserPresence
    try:
        presence = UserPresence.objects.get(user=profile_user)
        is_online = presence.is_online
        last_seen = presence.last_seen
    except UserPresence.DoesNotExist:
        is_online = False
        last_seen = None
    
    # Unread notifications count
    from .models import Notification
    unread_notifications = Notification.objects.filter(
        recipient=profile_user,
        is_read=False
    ).count() if is_owner else 0
    
    context = {
        'profile': user_profile,
        'is_owner': is_owner,
        'user': profile_user,
        'messages_sent': messages_sent,
        'rooms_created': rooms_created,
        'posts_created': posts_created,
        'recent_activities': recent_activities,
        'is_online': is_online,
        'last_seen': last_seen,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    from .forms import UserForm, UserProfileForm
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save user form
            user_form.save()
            
            # Save profile form
            profile_form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'users/edit_profile.html', context)


@login_required
def profile_settings(request):
    """Profile settings page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'users/profile_settings.html', context)


@login_required
def change_password(request):
    """Change password for logged-in user"""
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep the user logged in
            messages.success(request, 'Your password was updated successfully.')
            return redirect('users:profile_settings')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'users/change_password.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def upload_profile_picture(request):
    """Upload profile picture via AJAX"""
    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        file = request.FILES['profile_picture']
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': 'File must be an image'}, status=400)
        
        # Validate file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File size must be less than 5MB'}, status=400)
        
        # Save the file
        profile.profile_picture = file
        profile.save()
        
        return JsonResponse({
            'success': True,
            'profile_picture_url': profile.get_profile_picture_url(),
            'message': 'Profile picture updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def upload_cover_picture(request):
    """Upload cover picture via AJAX"""
    try:
        if 'cover_picture' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        file = request.FILES['cover_picture']
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': 'File must be an image'}, status=400)
        
        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'File size must be less than 10MB'}, status=400)
        
        # Save the file
        profile.cover_picture = file
        profile.save()
        
        return JsonResponse({
            'success': True,
            'cover_picture_url': profile.get_cover_picture_url(),
            'message': 'Cover picture updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_profile_picture(request):
    """Remove profile picture"""
    try:
        profile = get_object_or_404(UserProfile, user=request.user)
        
        if profile.profile_picture:
            # Delete the file
            import os
            if os.path.exists(profile.profile_picture.path):
                os.remove(profile.profile_picture.path)
            
            # Clear the field
            profile.profile_picture = None
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile picture removed successfully!'
            })
        else:
            return JsonResponse({'error': 'No profile picture to remove'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_cover_picture(request):
    """Remove cover picture"""
    try:
        profile = get_object_or_404(UserProfile, user=request.user)
        
        if profile.cover_picture:
            # Delete the file
            import os
            if os.path.exists(profile.cover_picture.path):
                os.remove(profile.cover_picture.path)
            
            # Clear the field
            profile.cover_picture = None
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cover picture removed successfully!'
            })
        else:
            return JsonResponse({'error': 'No cover picture to remove'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
