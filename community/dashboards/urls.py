from django.urls import path
from . import views

app_name= "dashboards"



urlpatterns = [
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]
