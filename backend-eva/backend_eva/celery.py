"""Celery application configuration for EVA Learning Platform."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_eva.settings")

app = Celery("backend_eva")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "reset-expired-streaks-daily": {
        "task": "gamification.reset_expired_streaks",
        "schedule": crontab(minute=0, hour=0),  # Daily at 00:00 UTC
    },
    "reset-weekly-leaderboard": {
        "task": "gamification.reset_weekly_leaderboard",
        "schedule": crontab(minute=0, hour=0, day_of_week=1),  # Monday 00:00 UTC
    },
    "process-spaced-repetition-daily": {
        "task": "progress.process_spaced_repetition",
        "schedule": crontab(minute=0, hour=0),  # Daily at 00:00 UTC
    },
    "aggregate-analytics-hourly": {
        "task": "progress.aggregate_analytics",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
    "check-inactive-collab-members": {
        "task": "collaboration.check_inactive_collab_members",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
}
