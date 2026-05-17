from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Tenant, TenantUser


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to handle tenant context for multi-tenant functionality
    """
    
    def process_request(self, request):
        """
        Add tenant context to the request
        """
        # Set default tenant context
        request.tenant = None
        request.tenant_user = None
        request.is_tenant_admin = False
        
        # If user is authenticated, try to determine their tenant context
        if request.user.is_authenticated:
            # For now, we'll use a simple approach where users can belong to multiple tenants
            # and we'll determine the active tenant based on the request or session
            
            # Try to get tenant from session (if set)
            tenant_id = request.session.get('active_tenant_id')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                    if self._has_tenant_access(request.user, tenant):
                        request.tenant = tenant
                        request.tenant_user = TenantUser.objects.get(
                            tenant=tenant, 
                            user=request.user, 
                            is_active=True
                        )
                        request.is_tenant_admin = self._has_tenant_admin_access(request.user, tenant)
                except (Tenant.DoesNotExist, TenantUser.DoesNotExist):
                    # Clear invalid tenant from session
                    request.session.pop('active_tenant_id', None)
            
            # If no tenant in session, try to get user's primary tenant
            if not request.tenant:
                # Get the first tenant the user has access to
                tenant_user = TenantUser.objects.filter(
                    user=request.user, 
                    is_active=True,
                    tenant__is_active=True
                ).select_related('tenant').first()
                
                if tenant_user:
                    request.tenant = tenant_user.tenant
                    request.tenant_user = tenant_user
                    request.is_tenant_admin = self._has_tenant_admin_access(request.user, tenant_user.tenant)
                    # Set in session for future requests
                    request.session['active_tenant_id'] = str(tenant_user.tenant.id)
        
        return None
    
    def _has_tenant_access(self, user, tenant):
        """Check if user has any access to tenant"""
        if user.is_superuser:
            return True
        
        if tenant.owner == user:
            return True
        
        return TenantUser.objects.filter(
            tenant=tenant, 
            user=user, 
            is_active=True
        ).exists()
    
    def _has_tenant_admin_access(self, user, tenant):
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


class TenantSelectionMiddleware(MiddlewareMixin):
    """
    Middleware to handle tenant selection from URL parameters
    """
    
    def process_request(self, request):
        """
        Handle tenant selection from URL parameters
        """
        if request.user.is_authenticated and 'tenant_id' in request.GET:
            try:
                tenant = Tenant.objects.get(
                    id=request.GET['tenant_id'], 
                    is_active=True
                )
                
                # Check if user has access to this tenant
                if self._has_tenant_access(request.user, tenant):
                    request.session['active_tenant_id'] = str(tenant.id)
                    # Redirect to remove tenant_id from URL
                    from django.urls import resolve
                    from django.http import HttpResponseRedirect
                    
                    # Get current URL without tenant_id parameter
                    url = request.path
                    if request.META.get('QUERY_STRING'):
                        query_params = request.META['QUERY_STRING'].split('&')
                        filtered_params = [
                            param for param in query_params 
                            if not param.startswith('tenant_id=')
                        ]
                        if filtered_params:
                            url += '?' + '&'.join(filtered_params)
                    
                    return HttpResponseRedirect(url)
                else:
                    from django.contrib import messages
                    messages.error(request, "You don't have access to that tenant.")
                    
            except (Tenant.DoesNotExist, ValueError):
                from django.contrib import messages
                messages.error(request, "Tenant not found.")
        
        return None
    
    def _has_tenant_access(self, user, tenant):
        """Check if user has any access to tenant"""
        if user.is_superuser:
            return True
        
        if tenant.owner == user:
            return True
        
        return TenantUser.objects.filter(
            tenant=tenant, 
            user=user, 
            is_active=True
        ).exists()
