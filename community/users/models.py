from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


class UserPresence(models.Model):
    """Track user online status and last activity"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    current_room = models.ForeignKey('chat.ChatRoom', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "User Presence"
        verbose_name_plural = "User Presences"
    
    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"
    
    @classmethod
    def update_activity(cls, user, room=None):
        """Update user's last activity and current room"""
        presence, created = cls.objects.get_or_create(user=user)
        presence.is_online = True
        presence.last_activity = timezone.now()
        if room:
            presence.current_room = room
        presence.save()
        return presence
    
    @classmethod
    def mark_offline(cls, user):
        """Mark user as offline"""
        presence, created = cls.objects.get_or_create(user=user)
        presence.is_online = False
        presence.current_room = None
        presence.save()


class UserActivity(models.Model):
    """Log user activities for tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)  # 'message_sent', 'post_created', 'login', etc.
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp.strftime('%H:%M')}"


class Notification(models.Model):
    """Real-time notifications for users"""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=50)  # 'new_message', 'new_post', 'mention', etc.
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"


class UserProfile(models.Model):
    """Extended user profile with additional information and profile picture"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, help_text="Tell us about yourself")
    location = models.CharField(max_length=100, blank=True, help_text="Your location")
    website = models.URLField(blank=True, help_text="Your website or social media")
    phone = models.CharField(max_length=20, blank=True, help_text="Your phone number")
    birth_date = models.DateField(null=True, blank=True, help_text="Your birth date")
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Upload a profile picture"
    )
    cover_picture = models.ImageField(
        upload_to='cover_pics/',
        blank=True,
        null=True,
        help_text="Upload a cover picture"
    )
    is_verified = models.BooleanField(default=False, help_text="Whether this user is verified")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    
    def get_profile_picture_url(self):
        """Get profile picture URL or default"""
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default_profile.png'
    
    def get_cover_picture_url(self):
        """Get cover picture URL or default"""
        if self.cover_picture:
            return self.cover_picture.url
        return '/static/images/default_cover.png'
    
    def save(self, *args, **kwargs):
        """Override save to handle image optimization"""
        super().save(*args, **kwargs)
        
        # Resize profile picture if exists
        if self.profile_picture:
            self.resize_image(self.profile_picture, max_size=(300, 300))
        
        # Resize cover picture if exists
        if self.cover_picture:
            self.resize_image(self.cover_picture, max_size=(1200, 400))
    
    def resize_image(self, image_field, max_size):
        """Resize image to fit within max_size"""
        try:
            from PIL import Image
            from io import BytesIO
            from django.core.files.base import ContentFile
            
            img = Image.open(image_field.path)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate new size maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save the resized image
            img.save(image_field.path, 'JPEG', quality=85, optimize=True)
            
        except Exception as e:
            print(f"Error resizing image: {e}")


# Signal to create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every new User"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
