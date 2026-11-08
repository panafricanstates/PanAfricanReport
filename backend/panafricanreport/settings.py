# panafricanreport/settings.py

from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default

# --- Security & Debug ---
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-placeholder-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Render automatically injects its hostname at runtime
ALLOWED_HOSTS = ["*"]

# --- Installed Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "django_filters",
    'drf_yasg',
    "newsfeeds",
    "cron_tasks",
    "corsheaders",
]

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 40,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # 👈 add this
    ],
}


# --- Middleware ---
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # local Next.js dev server
    "https://panafricanreport.vercel.app",  # production Next.js
]


ROOT_URLCONF = "panafricanreport.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "panafricanreport.wsgi.application"

# --- Database ---
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }


# --- Database ---
DATABASES = {
    "default": dj_database_url.config(
        # First, check if DATABASE_URL is set in environment (e.g., from Docker)
        env="DATABASE_URL",
        # default="postgresql://panafricanreport_db_g6eb_user:xHf8sjXRzBtUDzAvXygpRXGJeL9vi9nW@dpg-d5orgucoud1c739er1t0-a.oregon-postgres.render.com/panafricanreport_db_g6eb",
        default="postgresql://postgres.aguqzmpcugwepgqoifrb:ubuntu1reportt@aws-1-eu-west-1.pooler.supabase.com:5432/postgres",
        conn_max_age=600,
        ssl_require=True,
    )
}

# --- Password Validators ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Enable WhiteNoise for serving static files on Render
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Optional but recommended
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Cron endpoints (external pinger; no Celery/Redis) ---
# If CRON_SECRET is set, callers must send it as X-Cron-Secret or ?token=...
CRON_SECRET = os.getenv("CRON_SECRET", "report123")
CRON_MAX_WORKERS = _env_int("CRON_MAX_WORKERS", 4)
CRON_FETCH_CONCURRENCY = _env_int("CRON_FETCH_CONCURRENCY", 4)


# --- Default Primary Key ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FALLBACK_NEWS_IMAGE = "https://res.cloudinary.com/dewgby1vd/image/upload/v1770741203/a22dd152-efff-44f8-acf3-c0069ceed8ea_soycrr.png"


