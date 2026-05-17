from .models import Tenant, TenantUser


def tenant_context(request):
    """
    Add tenant information to template context
    """
    context = {}
    
    if request.user.is_authenticated:
        # Get all tenants the user has access to
        user_tenants = Tenant.objects.filter(
            users__user=request.user,
            users__is_active=True,
            is_active=True
        ).distinct()
        
        context['user_tenants'] = user_tenants
        context['tenant_count'] = user_tenants.count()
    
    return context
