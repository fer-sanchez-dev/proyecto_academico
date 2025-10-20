# micro_calificaciones/micro_calificaciones/settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "inseguro-dev")
DEBUG = os.getenv("DEBUG", "True") == "True"

# ✅ SOLUCIÓN: Agregar * en desarrollo o especificar sin puerto
ALLOWED_HOSTS = ['*']  # ← Permitir todos en desarrollo

# O si prefieres ser más específico:
# ALLOWED_HOSTS = [
#     'localhost',
#     '127.0.0.1',
#     'micro_calificaciones',
#     '0.0.0.0',
# ]

# 📦 Apps instaladas
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "calificaciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "calificaciones.middleware.CustomCommonMiddleware",
    "calificaciones.middleware.DisableCSRFForAPIMiddleware",  # ← Antes de CSRF
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "micro_calificaciones.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "micro_calificaciones.wsgi.application"

# 🗄️ Base de datos
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("CALIFICACIONES_DB_NAME", "calificaciones_db"),
        "USER": os.getenv("CALIFICACIONES_DB_USER", "postgres"),
        "PASSWORD": os.getenv("CALIFICACIONES_DB_PASSWORD", "postgres"),
        "HOST": os.getenv("CALIFICACIONES_DB_HOST", "db_calificaciones"),
        "PORT": os.getenv("CALIFICACIONES_DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        }
    }
}

# 🌎 Internacionalización
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# 📂 Archivos estáticos
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 🔓 CORS - Permitir peticiones desde el monolito
CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo
CORS_ALLOW_CREDENTIALS = True

# ✅ Configuración adicional para Docker
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = False
APPEND_SLASH = False  # Evitar redirecciones automáticas

# 🔐 CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://django_app:8000',
    'http://web:8000',
]

# 🔧 Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],  # ← Sin autenticación
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# 📝 Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
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
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'calificaciones': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

if DEBUG:
    print("=" * 60)
    print("🧩 MICROSERVICIO CALIFICACIONES")
    print("=" * 60)
    print(f"📊 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    print(f"🗄️  DATABASE_HOST: {DATABASES['default']['HOST']}")
    print(f"🌐 CORS: {'Permitir TODO (dev)' if CORS_ALLOW_ALL_ORIGINS else CORS_ALLOWED_ORIGINS}")
    print("=" * 60)