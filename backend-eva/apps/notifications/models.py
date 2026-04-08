"""Notifications app models — Notification."""

from django.db import models

from apps.accounts.models import User
from common.models import TimestampedModel


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app"
    EMAIL = "email"
    BOTH = "both"


class Notification(TimestampedModel):
    """A notification delivered to a user via in-app, email, or both."""

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=50, db_index=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    channel = models.CharField(
        max_length=10,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"Notification({self.notification_type}) → {self.recipient.email}"
