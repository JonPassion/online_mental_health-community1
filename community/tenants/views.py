from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Tenant, TenantDomain, TenantSettings, TenantUser
from .forms import TenantCreationForm, TenantSettingsForm
import re


def tenant_list(request):
    """List all tenants (for admin/management)"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to view tenants.")
        return redirect('chat:dashboard')
    
    tenants = Tenant.objects.all().order_by('name')
    context = {
        'tenants': tenants,
    }
    return render(request, 'tenants/tenant_list.html', context)


@login_required
def create_tenant(request):
    """Create a new tenant"""
    if request.method == 'POST':
        form = TenantCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create tenant
                    tenant = form.save(commit=False)
                    tenant.owner = request.user
                    tenant.slug = slugify(form.cleaned_data['name'])
                    tenant.save()
                    
                    # Create domain
                    domain = form.cleaned_data['domain']
                    TenantDomain.objects.create(
                        tenant=tenant,
                        domain=domain,
                        is_primary=True
                    )
                    
                    # Create tenant settings
                    TenantSettings.objects.create(tenant=tenant)
                    
                    # Add owner as tenant user
                    TenantUser.objects.create(
                        tenant=tenant,
                        user=request.user,
                        role='owner'
                    )
                    
                    messages.success(request, f'Tenant "{tenant.name}" created successfully!')
                    return redirect('tenants:tenant_detail', pk=tenant.pk)
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error creating tenant: {str(e)}')
    else:
        form = TenantCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'tenants/create_tenant.html', context)


@login_required
def tenant_detail(request, pk):
    """View tenant details"""
    tenant = get_object_or_404(Tenant, pk=pk)
    
    # Check if user has access to this tenant
    if not has_tenant_access(request.user, tenant):
        messages.error(request, "You don't have access to this tenant.")
        return redirect('chat:dashboard')
    
    tenant_users = TenantUser.objects.filter(tenant=tenant).select_related('user')
    settings = TenantSettings.objects.filter(tenant=tenant).first()
    
    context = {
        'tenant': tenant,
        'tenant_users': tenant_users,
        'settings': settings,
        'is_owner': tenant.owner == request.user,
    }
    return render(request, 'tenants/tenant_detail.html', context)


@login_required
def edit_tenant_settings(request, pk):
    """Edit tenant settings"""
    tenant = get_object_or_404(Tenant, pk=pk)
    
    # Check if user is owner or admin
    if not has_tenant_admin_access(request.user, tenant):
        messages.error(request, "You don't have permission to edit tenant settings.")
        return redirect('tenants:tenant_detail', pk=tenant.pk)
    
    settings, created = TenantSettings.objects.get_or_create(tenant=tenant)
    
    if request.method == 'POST':
        form = TenantSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tenant settings updated successfully!')
            return redirect('tenants:tenant_detail', pk=tenant.pk)
    else:
        form = TenantSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'tenant': tenant,
    }
    return render(request, 'tenants/edit_tenant_settings.html', context)


@login_required
@require_http_methods(["POST"])
def add_tenant_user(request, tenant_pk):
    """Add a user to a tenant"""
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    
    # Check if user has admin access
    if not has_tenant_admin_access(request.user, tenant):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    username = request.POST.get('username')
    role = request.POST.get('role', 'member')
    
    if not username:
        return JsonResponse({'error': 'Username is required'}, status=400)
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(username=username)
        
        # Check if user is already in tenant
        if TenantUser.objects.filter(tenant=tenant, user=user).exists():
            return JsonResponse({'error': 'User is already a member of this tenant'}, status=400)
        
        # Check if tenant can add more users
        if not tenant.can_add_user():
            return JsonResponse({'error': 'Tenant has reached maximum user limit'}, status=400)
        
        # Add user to tenant
        TenantUser.objects.create(tenant=tenant, user=user, role=role)
        
        return JsonResponse({
            'success': True,
            'message': f'{user.username} added to {tenant.name}',
            'user': {
                'username': user.username,
                'role': role,
                'joined_at': TenantUser.objects.get(tenant=tenant, user=user).joined_at.strftime('%Y-%m-%d')
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_tenant_user(request, tenant_pk, user_pk):
    """Remove a user from a tenant"""
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    user_to_remove = get_object_or_404(User, pk=user_pk)
    
    # Check if user has admin access
    if not has_tenant_admin_access(request.user, tenant):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Cannot remove the owner
    if tenant.owner == user_to_remove:
        return JsonResponse({'error': 'Cannot remove tenant owner'}, status=400)
    
    try:
        tenant_user = TenantUser.objects.get(tenant=tenant, user=user_to_remove)
        tenant_user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{user_to_remove.username} removed from {tenant.name}'
        })
        
    except TenantUser.DoesNotExist:
        return JsonResponse({'error': 'User is not a member of this tenant'}, status=404)


def has_tenant_access(user, tenant):
    """Check if user has any access to tenant"""
    if user.is_superuser:
        return True
    
    if tenant.owner == user:
        return True
    
    return TenantUser.objects.filter(tenant=tenant, user=user, is_active=True).exists()


def has_tenant_admin_access(user, tenant):
    """Check if user has admin access to tenant"""
    if user.is_superuser:
        return True
    
    if tenant.owner == user:
        return True
    
    return TenantUser.objects.filter(
        tenant=tenant, 
        user=user, 
        role__in=['owner', 'admin'],
        is_active=True
    ).exists()
