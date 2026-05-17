from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import UserProfile
from .forms import UserProfileForm, UserForm
import json
import os


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
    
    context = {
        'profile': user_profile,
        'is_owner': is_owner,
        'user': user_profile.user,
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
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


@login_required
def profile_settings(request):
    """Profile settings page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'users/profile_settings.html', context)
