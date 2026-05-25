from django.urls import path
from . import views

app_name = "dashboards"

urlpatterns = [
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/users/create/', views.create_user_admin, name='create_user_admin'),
    path('admin/users/<int:user_id>/edit/', views.edit_user_admin, name='edit_user_admin'),
    path('admin/users/<int:user_id>/delete/', views.delete_user_admin, name='delete_user_admin'),
    path('admin/users/<int:user_id>/assign-tenant/', views.assign_tenant_role, name='assign_tenant_role'),
    path('admin/users/<int:user_id>/remove-tenant/<uuid:tenant_id>/', views.remove_tenant_membership, name='remove_tenant_membership'),
]
