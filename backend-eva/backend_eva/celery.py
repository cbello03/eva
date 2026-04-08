"""Celery application configuration for EVA Learning Platform."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_eva.settings")

app = Celery("backend_eva")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
