import os
from pathlib import Path
from decouple import config
from celery.schedules import crontab
from datetime import timedelta
from urllib.parse import urlparse
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Hosts permitidos (Render añade RENDER_EXTERNAL_URL automáticamente)
default_hosts = ['localhost', '127.0.0.1', 'backend']
env_hosts = [h.strip() for h in config('ALLOWED_HOSTS', default='').split(',') if h.strip()]
render_external_url = config('RENDER_EXTERNAL_URL', default=None)
if render_external_url:
    try:
        parsed = urlparse(render_external_url)
        if parsed.hostname:
            default_hosts.append(parsed.hostname)
    except Exception:
        pass

ALLOWED_HOSTS = list({h for h in (default_hosts + env_hosts) if h})

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_extensions",
    "apps.rooms",
    "apps.reservations",
    "apps.users",
    "apps.enterprises",
    "apps.core",
    "apps.locations",
    "apps.dashboard",
    "apps.rates",
    "apps.payments",
    "apps.calendar",
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.reservations.middleware.CurrentUserMiddleware',
]

ROOT_URLCONF = 'hotel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'hotel.wsgi.application'

# Database
USE_SQLITE = config('USE_SQLITE', default=False, cast=bool)

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='hotel'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='db'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

    # Usar DATABASE_URL si está definido (Render/Neon). SSL requerido en Render.
    db_from_env = dj_database_url.config(conn_max_age=600, ssl_require=True)
    if db_from_env:
        DATABASES['default'] = db_from_env

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Detrás de proxy (https en Render)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS/CSRF settings
frontend_url = config('FRONTEND_URL', default=None)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if frontend_url:
    CORS_ALLOWED_ORIGINS.append(frontend_url)

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://*.onrender.com",
]
if frontend_url and frontend_url.startswith("http"):
    CSRF_TRUSTED_ORIGINS.append(frontend_url)
if render_external_url and render_external_url.startswith("http"):
    CSRF_TRUSTED_ORIGINS.append(render_external_url)

CELERY_BROKER_URL = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


CELERY_BEAT_SCHEDULE = {
    "sync_room_occupancy_daily": {
        "task": "apps.reservations.tasks.sync_room_occupancy_for_today",
        "schedule": crontab(hour=6, minute=0),
    },
    "calculate_dashboard_metrics_daily": {
        "task": "apps.dashboard.tasks.calculate_dashboard_metrics_daily",
        "schedule": crontab(hour=6, minute=10),
    },
    "process_automatic_checkouts_hourly": {
        "task": "apps.reservations.tasks.process_automatic_checkouts",
        "schedule": crontab(minute=0),  # Cada hora a los 0 minutos
    },
}

CHANNEL_COMMISSION_RATES = {
    "direct": 0,
    "booking": 15,     # %
    "expedia": 18,     # %
    "other": 0,
}