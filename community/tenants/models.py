from django.db import models
from django.contrib.auth.models import User
import uuid


class Tenant(models.Model):
    """
    Tenant model for multi-tenant architecture (simplified version)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    created_on = models.DateField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=10)
    subscription_plan = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}"
    
    def get_user_count(self):
        """Get the number of users in this tenant"""
        return self.users.count()
    
    def can_add_user(self):
        """Check if tenant can add more users based on plan"""
        if self.subscription_plan == 'free':
            return self.get_user_count() < self.max_users
        elif self.subscription_plan == 'basic':
            return self.get_user_count() < 50
        elif self.subscription_plan == 'premium':
            return self.get_user_count() < 200
        else:  # enterprise
            return True


class TenantDomain(models.Model):
    """
    Domain model for tenant domains (simplified version)
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['domain']
    
    def __str__(self):
        return self.domain


class TenantSettings(models.Model):
    """
    Tenant-specific settings
    """
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    allow_registration = models.BooleanField(default=True)
    require_email_verification = models.BooleanField(default=False)
    default_user_role = models.CharField(
        max_length=50,
        choices=[
            ('member', 'Member'),
            ('admin', 'Admin'),
            ('moderator', 'Moderator'),
        ],
        default='member'
    )
    theme_color = models.CharField(max_length=7, default='#007bff')
    logo_url = models.URLField(blank=True)
    custom_css = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Settings"
        verbose_name_plural = "Tenant Settings"
    
    def __str__(self):
        return f"{self.tenant.name} Settings"


class TenantUser(models.Model):
    """
    Intermediate model for tenant-user relationships with roles
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['tenant', 'user']
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"
    
    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"
