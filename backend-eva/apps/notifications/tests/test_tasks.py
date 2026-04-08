"""Tests for notification Celery tasks — email delivery with retry policy (Req 19.6)."""

import uuid

import pytest
from unittest.mock import patch, MagicMock

from apps.accounts.models import Role, User
from apps.notifications.models import Notification, NotificationChannel
from apps.notifications.tasks import send_email_notification


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def student(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"nt_student_{uid}",
        email=f"nt_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def notification(student):
    return Notification.objects.create(
        recipient=student,
        notification_type="test",
        title="Test Notification",
        body="Test body",
        channel=NotificationChannel.EMAIL,
    )


# ------------------------------------------------------------------
# Email task behavior
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestSendEmailNotification:
    def test_sends_email_and_marks_sent(self, notification):
        with patch("django.core.mail.send_mail") as mock_send:
            send_email_notification(notification.pk)

        mock_send.assert_called_once_with(
            subject=notification.title,
            message=notification.body,
            from_email=None,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        notification.refresh_from_db()
        assert notification.email_sent is True

    def test_skips_already_sent(self, notification):
        notification.email_sent = True
        notification.save(update_fields=["email_sent"])

        with patch("django.core.mail.send_mail") as mock_send:
            send_email_notification(notification.pk)

        mock_send.assert_not_called()

    def test_nonexistent_notification_does_not_raise(self):
        # Should log error and return without raising
        send_email_notification(99999)

    def test_task_has_retry_config(self):
        """Verify the task is configured with retry policy (Req 19.6)."""
        assert send_email_notification.max_retries == 3
        assert send_email_notification.autoretry_for == (Exception,)
        assert send_email_notification.retry_backoff is True

    def test_email_failure_raises_for_retry(self, notification):
        """When send_mail raises, the exception propagates so Celery can retry."""
        with patch(
            "django.core.mail.send_mail",
            side_effect=ConnectionError("SMTP down"),
        ):
            with pytest.raises(ConnectionError):
                send_email_notification(notification.pk)

        # email_sent should still be False since it failed
        notification.refresh_from_db()
        assert notification.email_sent is False
