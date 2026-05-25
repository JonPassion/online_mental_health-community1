from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-^y)fu5%q93p*n3rm_$ara%g&-sgr!utop!+b)(bwp3_u@_ky5-')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Build ALLOWED_HOSTS from env, then append known proxy domains
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# Always allow Replit preview domains and localhost
for _h in ['.replit.dev', '.kirk.replit.dev', '.worf.replit.dev', 'localhost', '127.0.0.1']:
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)

# Add the specific Replit dev domain if provided
_replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
if _replit_domain and _replit_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_replit_domain)

if 'RENDER' in os.environ:
    render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
    if render_url:
        from urllib.parse import urlparse
        host = urlparse(render_url).netloc
        if host and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Trust the proxy SSL header (Replit + Render both forward this)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.dev',
    'https://*.worf.replit.dev',
    'https://*.replit.app',
    'https://*.onrender.com',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

# ─── Application ─────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'tenants',
    'chat',
    'users',
    'posts',
    'dashboards',
    'rest_framework',
    'django.contrib.humanize',
    'django_apscheduler',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenants.middleware.TenantMiddleware',
    'tenants.middleware.TenantSelectionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'community.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'community.wsgi.application'
ASGI_APPLICATION = 'community.asgi.application'

# ─── Database ────────────────────────────────────────────────────────────────

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ─── Auth ────────────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/users/auth/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/users/auth/'

# ─── Internationalisation ────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─── Static & media files ───────────────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Sessions ────────────────────────────────────────────────────────────────

SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Django Channels ─────────────────────────────────────────────────────────

REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ─── Email ───────────────────────────────────────────────────────────────────

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # prints to console in dev
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Community <noreply@community.app>')

# ─── Production hardening ───────────────────────────────────────────────────

if not DEBUG:
    SECURE_SSL_REDIRECT = False          # Render/Replit terminate TLS at the proxy
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
