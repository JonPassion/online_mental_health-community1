from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from community.health import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('tenants/', include('tenants.urls')),
    path('chat/', include('chat.urls')),
    path('users/', include('users.urls')),
    path('posts/', include('posts.urls')),
    path('dashboard/', include('dashboards.urls')),

    # 👇 Redirect root URL to the login page in users app
    path('', RedirectView.as_view(url='/users/auth/', permanent=False)),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
