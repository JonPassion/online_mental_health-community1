from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Tenant management
    path('', views.tenant_list, name='tenant_list'),
    path('create/', views.create_tenant, name='create_tenant'),
    path('<int:pk>/', views.tenant_detail, name='tenant_detail'),
    path('<int:pk>/edit/', views.edit_tenant_settings, name='edit_tenant_settings'),
    
    # Tenant user management
    path('<int:tenant_pk>/add-user/', views.add_tenant_user, name='add_tenant_user'),
    path('<int:tenant_pk>/remove-user/<int:user_pk>/', views.remove_tenant_user, name='remove_tenant_user'),
]
