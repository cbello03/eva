import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 1. Definición de rutas base
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Configuración con Pydantic (Tarea 1.1 - Manejo de variables de entorno)
class Settings(BaseSettings):
    DEBUG: bool = True
    SECRET_KEY: str
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    DATABASE_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

env = Settings()

# 3. Configuraciones Básicas de Django
DEBUG = env.DEBUG
SECRET_KEY = env.SECRET_KEY
ALLOWED_HOSTS = env.ALLOWED_HOSTS.split(",")

INSTALLED_APPS = [
    'daphne', # Debe ir de primero para WebSockets (Channels)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Nuestras futuras apps se cargarán aquí
    'apps.common', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application' # Para WebSockets

# 4. Configuración de Base de Datos (PostgreSQL)
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default=env.DATABASE_URL)
}

# 5. Configuración de Redis (Caché y Channels)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env.REDIS_URL],
        },
    },
}

# Configuración de archivos estáticos
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'