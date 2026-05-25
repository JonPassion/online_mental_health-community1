from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from tenants.models import Tenant, TenantUser

is_admin = lambda u: u.is_staff or u.is_superuser


@login_required
def user_dashboard(request):
    return render(request, 'dashboards/user_dashboard.html')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_tenants = Tenant.objects.count()
    staff_count = User.objects.filter(is_staff=True).count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    return render(request, 'dashboards/admin_dashboard.html', {
        'total_users': total_users,
        'total_tenants': total_tenants,
        'staff_count': staff_count,
        'recent_users': recent_users,
    })


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().order_by('-date_joined').prefetch_related('tenantuser_set__tenant')
    tenants = Tenant.objects.all()
    return render(request, 'dashboards/manage_users.html', {
        'users': users,
        'tenants': tenants,
    })


@login_required
@user_passes_test(is_admin)
def create_user_admin(request):
    tenants = Tenant.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        system_role = request.POST.get('system_role', 'user')
        tenant_id = request.POST.get('tenant_id', '')
        tenant_role = request.POST.get('tenant_role', 'member')

        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        if not password:
            errors.append('Password is required.')
        elif password != confirm_password:
            errors.append('Passwords do not match.')
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already in use.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'dashboards/create_user.html', {
                'tenants': tenants,
                'form_data': request.POST,
            })

        user = User.objects.create_user(username=username, email=email, password=password)
        if system_role == 'superuser':
            user.is_staff = True
            user.is_superuser = True
        elif system_role == 'staff':
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False
        user.save()

        if tenant_id:
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                TenantUser.objects.create(tenant=tenant, user=user, role=tenant_role)
            except Tenant.DoesNotExist:
                messages.warning(request, 'Selected tenant not found; user created without tenant assignment.')

        messages.success(request, f'User "{username}" created successfully.')
        return redirect('dashboards:manage_users')

    return render(request, 'dashboards/create_user.html', {'tenants': tenants})


@login_required
@user_passes_test(is_admin)
def edit_user_admin(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    tenants = Tenant.objects.all()
    tenant_memberships = TenantUser.objects.filter(user=target).select_related('tenant')

    if request.method == 'POST':
        system_role = request.POST.get('system_role', 'user')
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if system_role == 'superuser':
            target.is_staff = True
            target.is_superuser = True
        elif system_role == 'staff':
            target.is_staff = True
            target.is_superuser = False
        else:
            target.is_staff = False
            target.is_superuser = False

        target.email = email
        target.first_name = first_name
        target.last_name = last_name
        target.save()

        messages.success(request, f'User "{target.username}" updated successfully.')
        return redirect('dashboards:manage_users')

    if target.is_superuser:
        current_role = 'superuser'
    elif target.is_staff:
        current_role = 'staff'
    else:
        current_role = 'user'

    return render(request, 'dashboards/edit_user.html', {
        'target': target,
        'tenants': tenants,
        'tenant_memberships': tenant_memberships,
        'current_role': current_role,
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def assign_tenant_role(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    tenant_id = request.POST.get('tenant_id')
    role = request.POST.get('role', 'member')

    if not tenant_id:
        return JsonResponse({'error': 'Tenant is required'}, status=400)

    tenant = get_object_or_404(Tenant, pk=tenant_id)
    membership, created = TenantUser.objects.get_or_create(
        tenant=tenant, user=target, defaults={'role': role}
    )
    if not created:
        membership.role = role
        membership.save()

    return JsonResponse({
        'success': True,
        'tenant': tenant.name,
        'role': role,
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def remove_tenant_membership(request, user_id, tenant_id):
    target = get_object_or_404(User, pk=user_id)
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    TenantUser.objects.filter(user=target, tenant=tenant).delete()
    return JsonResponse({'success': True})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_user_admin(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        return JsonResponse({'error': 'You cannot delete your own account.'}, status=400)
    username = target.username
    target.delete()
    return JsonResponse({'success': True, 'username': username})
