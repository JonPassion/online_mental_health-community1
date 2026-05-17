from django.contrib import admin
from .models import Tenant, TenantDomain, TenantSettings, TenantUser


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'owner', 'subscription_plan', 'is_active', 'created_on']
    list_filter = ['subscription_plan', 'is_active', 'created_on']
    search_fields = ['name', 'slug', 'owner__username']
    readonly_fields = ['slug', 'created_on']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'owner', 'created_on')
        }),
        ('Configuration', {
            'fields': ('subscription_plan', 'max_users', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant__owner=request.user)


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'allow_registration', 'default_user_role', 'theme_color']
    list_filter = ['allow_registration', 'require_email_verification', 'default_user_role']
    search_fields = ['tenant__name']
    
    fieldsets = (
        ('Registration Settings', {
            'fields': ('allow_registration', 'require_email_verification')
        }),
        ('User Management', {
            'fields': ('default_user_role',)
        }),
        ('Appearance', {
            'fields': ('theme_color', 'logo_url', 'custom_css')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant__owner=request.user)


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'joined_at', 'is_active']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant__owner=request.user)
