# settings.py
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from pathlib import Path
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

sentry_sdk.init(
    dsn="https://19acd0571ebfa9fbca48f9cb49425076@o4510215137853440.ingest.us.sentry.io/4510215145455616",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
)


# ======================
# Seguridad / Debug
# ======================
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-please-change-this-in-production"
)

# DJANGO_DEBUG in .env should be "True" or "False"
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("1", "true", "yes")

# Allow hosts: coma-separados en .env
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]

# Si detrás de un reverse proxy que pone X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ======================
# Apps / Middleware
# ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # servir estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'proyecto_academico.urls'

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

WSGI_APPLICATION = 'proyecto_academico.wsgi.application'

# ======================
# Base de datos (Postgres)
# ======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'proyecto_academico_db'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', '1234'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
        # 👇 AÑADIDO: Opciones de conexión para Docker
        'CONN_MAX_AGE': 60,  # Reutilizar conexiones (mejor performance)
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# ======================
# Validadores de contraseña
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ======================
# Email (dev vs prod)
# ======================
EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ("1", "true", "yes")
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'webmaster@localhost')

# ======================
# Internacionalización / Timezone
# ======================
LANGUAGE_CODE = 'es-es'
TIME_ZONE = os.getenv('TIME_ZONE', 'America/Bogota')
USE_I18N = True
USE_TZ = True

# ======================
# Archivos estáticos
# ======================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "app" / "static"]
# 👇 CAMBIADO: Usar /vol/static para Docker (coincide con el volumen)
STATIC_ROOT = os.getenv('STATIC_ROOT', '/vol/static')

# Whitenoise para servir archivos estáticos comprimidos y cacheados
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 👇 AÑADIDO: Configuración de archivos media (uploads de usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/vol/media')

# ======================
# Autenticación / URLs
# ======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
AUTH_USER_MODEL = 'app.CustomUser'
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT', 14400))

# ======================
# Seguridad extra (solo cuando DEBUG=False)
# ======================
if not DEBUG:
    # 👇 CAMBIADO: Solo activa esto si tienes HTTPS configurado
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ("1", "true", "yes")
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ("1", "true", "yes")
    CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() in ("1", "true", "yes")

    # HSTS (solo con HTTPS)
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', 0))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() in ("1", "true", "yes")
    SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() in ("1", "true", "yes")

    # Previene clickjacking
    X_FRAME_OPTIONS = 'DENY'

# ======================
# Logging (archivo)
# ======================
import os
from pathlib import Path

LOG_DIR = Path(os.getenv("DJANGO_LOG_DIR", "/app/logs"))

# Intentar crear el directorio, pero manejar errores de permisos
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # Verificar si podemos escribir
    test_file = LOG_DIR / '.write_test'
    test_file.touch()
    test_file.unlink()
    LOG_FILE = str(LOG_DIR / 'django.log')
    USE_FILE_HANDLER = True
except (PermissionError, OSError):
    print(f"⚠️ No se puede escribir en {LOG_DIR}, usando solo consola para logs")
    LOG_FILE = None
    USE_FILE_HANDLER = False

# Configuración base de handlers
handlers = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}

# Solo agregar el handler de archivo si tenemos permisos
if USE_FILE_HANDLER:
    handlers['file'] = {
        'level': 'ERROR',
        'class': 'logging.FileHandler',
        'filename': LOG_FILE,
        'formatter': 'verbose',
    }
    handler_list = ['console', 'file']
else:
    handler_list = ['console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': handlers,
    'loggers': {
        'django': {
            'handlers': handler_list,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': handler_list,
            'level': 'ERROR',
            'propagate': False,
        },
        'app': {
            'handlers': handler_list,
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': handler_list,
        'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
    },
}

# ========== CONFIGURACIÓN MICROSERVICIOS ==========
# Modo de operación del microservicio
# 'monolith': Solo usa el monolito (comportamiento original)
# 'hybrid': Usa el microservicio pero valida contra el monolito
# 'proxy': Solo usa el microservicio (migración completa)
MICROSERVICE_MODE = os.getenv('MICROSERVICE_MODE', 'hybrid')

# Habilitar uso del microservicio de calificaciones
USE_MICROSERVICE_CALIFICACIONES = os.getenv('USE_MICROSERVICE_CALIFICACIONES', 'True').lower() in ('true', '1', 'yes')

# URL del microservicio (usar nombre del contenedor para red Docker)
MICROSERVICE_CALIFICACIONES_URL = os.getenv(
    'MICROSERVICE_CALIFICACIONES_URL',
    'http://micro_calificaciones:8001/api'  # ← Esta es la correcta
)

# Timeout para llamadas al microservicio (en segundos)
MICROSERVICE_TIMEOUT = int(os.getenv('MICROSERVICE_TIMEOUT', 5))

    
# 👇 AÑADIDO: Imprimir configuración útil al iniciar (solo en desarrollo)
if DEBUG:
    print("=" * 60)
    print("🐛 MODO DESARROLLO ACTIVADO")
    print("=" * 60)
    print(f"📂 BASE_DIR: {BASE_DIR}")
    print(f"🗄️  DATABASE_HOST: {DATABASES['default']['HOST']}")
    print(f"📊 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    print(f"📁 STATIC_ROOT: {STATIC_ROOT}")
    print(f"📁 MEDIA_ROOT: {MEDIA_ROOT}")
    print("=" * 60)
    print(f"🔌 Microservicio Calificaciones: {'HABILITADO' if USE_MICROSERVICE_CALIFICACIONES else 'DESHABILITADO'}")
    print(f"🌐 URL Microservicio: {MICROSERVICE_CALIFICACIONES_URL}")
    print(f"⚙️  Modo: {MICROSERVICE_MODE}")