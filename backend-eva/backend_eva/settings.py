"""
Django settings for EVA Learning Platform.

Uses pydantic-settings for environment variable loading.
"""

import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Build paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Environment-based configuration via pydantic-settings
# ---------------------------------------------------------------------------
class EnvSettings(BaseSettings):
    """All tuneable settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Django
    secret_key: str = Field(
        default="django-insecure-change-me-in-production",
        alias="SECRET_KEY",
    )
    debug: bool = Field(default=True, alias="DEBUG")
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1", alias="ALLOWED_HOSTS")

    # PostgreSQL
    db_name: str = Field(default="eva_db", alias="POSTGRES_DB")
    db_user: str = Field(default="eva_user", alias="POSTGRES_USER")
    db_password: str = Field(default="eva_password", alias="POSTGRES_PASSWORD")
    db_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    db_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", alias="REDIS_URL")

    # CORS
    cors_allowed_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ALLOWED_ORIGINS",
    )


env = EnvSettings()

# ---------------------------------------------------------------------------
# Core settings
# ---------------------------------------------------------------------------
SECRET_KEY = env.secret_key
DEBUG = env.debug
ALLOWED_HOSTS = [h.strip() for h in env.allowed_hosts.split(",") if h.strip()]

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "ninja",
    "django_extensions",
    "corsheaders",
    # Domain apps
    "apps.accounts",
    "apps.courses",
    "apps.exercises",
    "apps.gamification",
    "apps.progress",
    "apps.social",
    "apps.projects",
    "apps.collaboration",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend_eva.urls"

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

WSGI_APPLICATION = "backend_eva.wsgi.application"
ASGI_APPLICATION = "backend_eva.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.db_name,
        "USER": env.db_user,
        "PASSWORD": env.db_password,
        "HOST": env.db_host,
        "PORT": env.db_port,
    }
}


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-ve"
TIME_ZONE = "America/Caracas"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Custom user model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Django Channels — Redis channel layer
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env.redis_url],
        },
    },
}


# ---------------------------------------------------------------------------
# Celery — Redis broker
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env.redis_url
CELERY_RESULT_BACKEND = env.redis_url
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Celery Beat schedule
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "reset-expired-streaks": {
        "task": "gamification.reset_expired_streaks",
        "schedule": crontab(hour=0, minute=0),  # Daily at 00:00 UTC
    },
    "reset-weekly-leaderboard": {
        "task": "gamification.reset_weekly_leaderboard",
        "schedule": crontab(hour=0, minute=0, day_of_week=1),  # Monday 00:00 UTC
    },
    "process-spaced-repetition": {
        "task": "progress.process_spaced_repetition",
        "schedule": crontab(hour=1, minute=0),  # Daily at 01:00 UTC
    },
    "check-inactive-collab-members": {
        "task": "collaboration.check_inactive_collab_members",
        "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 UTC
    },
}

# ---------------------------------------------------------------------------
# Redis cache
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.redis_url,
    }
}

# ---------------------------------------------------------------------------
# Add backend-eva root to sys.path so `apps.*` imports work
# ---------------------------------------------------------------------------
APPS_DIR = BASE_DIR / "apps"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ---------------------------------------------------------------------------
# CORS — allow only configured frontend origin
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in env.cors_allowed_origins.split(",") if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
