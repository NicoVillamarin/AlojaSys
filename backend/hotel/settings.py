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

# URL pública externa del backend (para webhooks), opcional
EXTERNAL_BASE_URL = config('EXTERNAL_BASE_URL', default=None)

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
    "apps.housekeeping",
    "apps.users",
    "apps.enterprises",
    "apps.core",
    "apps.locations",
    "apps.dashboard",
    "apps.rates",
    "apps.payments",
    "apps.calendar",
    "apps.notifications",
    "apps.invoicing",
    "apps.otas",
    "apps.chatbot",
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# Media files - WhiteNoise puede servir archivos media en producción
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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

# LOGGING para depurar AFIP WSAA/WSFE
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # WhatsApp / Chatbot (necesario para ver logs del webhook en producción)
        'apps.chatbot': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.invoicing.services.afip_auth_service': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.invoicing.services.afip_invoice_service': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.invoicing.services.afip_service': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
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

# Configuración de Redis/Celery
# Preferimos REDIS_URL (Railway plugin). Si no existe, caemos a REDIS_HOST:6379.
REDIS_URL = config('REDIS_URL', default=None)
REDIS_HOST = config('REDIS_HOST', default='hotel_redis')
if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379/0"
    CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379/0"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Cache compartido (Redis) para tokens/locks de AFIP y otros
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL if REDIS_URL else f"redis://{REDIS_HOST}:6379/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 0,  # sin expiración global; manejamos TTL manualmente
    }
}


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
    "generate_daily_housekeeping_tasks_hourly": {
        # Scheduler fino que dispara la generación diaria según daily_generation_time
        # y timezone de cada hotel (ver apps.housekeeping.tasks.schedule_daily_tasks)
        "task": "apps.housekeeping.tasks.schedule_daily_tasks",
        "schedule": crontab(minute="*/10"),  # Cada 10 minutos
    },
    "check_overdue_housekeeping_tasks": {
        "task": "apps.housekeeping.tasks.check_overdue_tasks",
        "schedule": crontab(minute=15),  # Cada hora a los 15 minutos
    },
    "auto_cancel_expired_reservations_daily": {
        "task": "apps.reservations.tasks.auto_cancel_expired_reservations",
        "schedule": crontab(hour=8, minute=0),  # Diario a las 8:00 AM
    },
    "auto_mark_no_show_daily": {
        "task": "apps.reservations.tasks.auto_mark_no_show_daily",
        "schedule": crontab(hour=9, minute=0),  # Diario a las 9:00 AM
    },
    "rebalance_housekeeping_workload": {
        "task": "apps.housekeeping.tasks.rebalance_housekeeping_workload",
        "schedule": crontab(minute="*/15"),  # Cada 15 minutos
    },
    "process_pending_refunds_hourly": {
        "task": "apps.payments.tasks.process_pending_refunds",
        "schedule": crontab(minute=30),  # Cada hora a los 30 minutos
    },
    "retry_failed_refunds_daily": {
        "task": "apps.payments.tasks.retry_failed_refunds",
        "schedule": crontab(hour=10, minute=0),  # Diario a las 10:00 AM
    },
    "auto_cancel_expired_pending_daily": {
        "task": "apps.reservations.tasks.auto_cancel_expired_pending_reservations",
        "schedule": crontab(hour=8, minute=30),  # Diario a las 8:30 AM (antes del auto no-show)
    },
    "auto_cancel_pending_deposits_daily": {
        "task": "apps.reservations.tasks.auto_cancel_pending_deposits",
        "schedule": crontab(hour=8, minute=15),  # Diario a las 8:15 AM (antes de otras tareas)
    },
    # Tareas de facturación
    "retry_failed_invoices_hourly": {
        "task": "apps.invoicing.tasks.retry_failed_invoices_task",
        "schedule": crontab(minute=15),  # Cada hora a los 15 minutos
    },
    "cleanup_expired_invoices_daily": {
        "task": "apps.invoicing.tasks.cleanup_expired_invoices_task",
        "schedule": crontab(hour=2, minute=0),  # Diario a las 2:00 AM
    },
    "validate_afip_connection_hourly": {
        "task": "apps.invoicing.tasks.validate_afip_connection_task",
        "schedule": crontab(minute=45),  # Cada hora a los 45 minutos
    },
    "generate_daily_invoice_report": {
        "task": "apps.invoicing.tasks.generate_daily_invoice_report_task",
        "schedule": crontab(hour=23, minute=0),  # Diario a las 11:00 PM
    },
    # OTAs - Import ICS (más frecuente para near‑real time)
    "otas_import_ics_1min": {
        "task": "apps.otas.tasks.import_all_ics",
        "schedule": 60.0,  # cada 1 minuto (near real-time)
    },
    # OTAs - Google Calendar (pull) cada 1 minuto
    "otas_import_google_1min": {
        "task": "apps.otas.tasks.import_all_google",
        "schedule": 60.0,
    },
    # Pull de reservas cada 5 minutos (mock/sandbox hasta credenciales reales)
    "otas_pull_reservations_5min": {
        "task": "apps.otas.tasks.pull_reservations_all_hotels_task",
        "schedule": 300.0,
    },
}

# Asegurar registro explícito de tareas de OTAs en Celery (además del autodiscover)
CELERY_IMPORTS = (
    "apps.otas.tasks",
)

CHANNEL_COMMISSION_RATES = {
    "direct": 0,
    "whatsapp": 0,
    "booking": 15,     # %
    "expedia": 18,     # %
    "other": 0,
}

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='dsozqrhns')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='')

# Configuración híbrida de archivos
USE_CLOUDINARY = config('USE_CLOUDINARY', default=False, cast=bool)

if USE_CLOUDINARY:
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True
        )
        
        # Configuración para Cloudinary
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    except ImportError:
        # Si cloudinary no está instalado, usar almacenamiento local
        USE_CLOUDINARY = False
        MEDIA_URL = '/media/'
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
        import warnings
        warnings.warn(
            "USE_CLOUDINARY=True pero cloudinary no está instalado. "
            "Usando almacenamiento local. Instala: pip install cloudinary django-cloudinary-storage"
        )
else:
    # Configuración local
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =============================================================================
# CONFIGURACIÓN DE EMAIL / RESEND
# =============================================================================

import logging
logger = logging.getLogger(__name__)

# Configuración básica: backend por defecto (consola en desarrollo)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# Clave para Resend HTTP API (recomendado en producción y funciona en local con HTTPS)
RESEND_API_KEY = config('RESEND_API_KEY', default=None)
# Si tiene API key, activar Resend API por defecto (se puede desactivar con USE_RESEND_API=False)
# Si no se especifica USE_RESEND_API, se activa automáticamente si hay RESEND_API_KEY
use_resend_default = bool(RESEND_API_KEY) if RESEND_API_KEY else False
USE_RESEND_API = config('USE_RESEND_API', default=use_resend_default, cast=bool)

# Log informativo sobre configuración de email
# Nota: evitamos prints/emoji para no romper en Windows (cp1252) y durante tests.
if USE_RESEND_API and RESEND_API_KEY:
    logger.info("EMAIL: Resend API habilitado (funciona en local y producción)")
elif RESEND_API_KEY and not USE_RESEND_API:
    logger.warning("EMAIL: RESEND_API_KEY configurada pero USE_RESEND_API=False")
elif not RESEND_API_KEY:
    logger.info("EMAIL: Resend API no configurado, usando backend de Django")

# Para producción, usar SMTP solo si está permitido por la plataforma
EMAIL_USE_SMTP = config('EMAIL_USE_SMTP', default=False, cast=bool)
if EMAIL_USE_SMTP:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    # Timeout explícito para evitar que email.send() quede colgado indefinidamente
    EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=15, cast=int)
    
    logger.info(
        "EMAIL: Configurado para SMTP: %s:%s, TLS=%s, User=%s***, Timeout=%ss",
        EMAIL_HOST,
        EMAIL_PORT,
        EMAIL_USE_TLS,
        (EMAIL_HOST_USER[:3] if EMAIL_HOST_USER else "N/A"),
        EMAIL_TIMEOUT,
    )
else:
    if not DEBUG:
        logger.warning(
            "EMAIL: EMAIL_USE_SMTP=False en producción. Los emails NO se enviarán por SMTP; "
            "usa Resend HTTP API (USE_RESEND_API=True) para envíos reales."
        )
    else:
        logger.info("EMAIL usando backend de consola (desarrollo)")

# Email del remitente por defecto
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@alojaSys.com')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Para desarrollo, también podemos usar archivo
if config('EMAIL_USE_FILE', default=False, cast=bool):
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')

# =============================================================================
# CONFIGURACIÓN DE FACTURACIÓN ELECTRÓNICA
# =============================================================================

# Configuración de facturación
AUTO_GENERATE_INVOICE_PDF = config('AUTO_GENERATE_INVOICE_PDF', default=True, cast=bool)
INVOICE_PDF_STORAGE_PATH = os.path.join(MEDIA_ROOT, 'invoices', 'pdf')

# Configuración AFIP
AFIP_TEST_MODE = config('AFIP_TEST_MODE', default=True, cast=bool)
AFIP_USE_MOCK = config('AFIP_USE_MOCK', default=False, cast=bool)
AFIP_CERTIFICATE_PATH = config('AFIP_CERTIFICATE_PATH', default='')
AFIP_PRIVATE_KEY_PATH = config('AFIP_PRIVATE_KEY_PATH', default='')

# Configuración de reintentos
INVOICE_MAX_RETRIES = config('INVOICE_MAX_RETRIES', default=3, cast=int)
INVOICE_RETRY_DELAY = config('INVOICE_RETRY_DELAY', default=300, cast=int)  # 5 minutos

# Configuración de PDFs
INVOICE_PDF_TEMPLATE = 'invoicing/invoice_template.html'
INVOICE_PDF_LOGO_PATH = os.path.join(STATIC_ROOT, 'img', 'logo.png')