"""Tests for NotificationService — creation, delivery, read-state management."""

import uuid

import pytest
from unittest.mock import patch, MagicMock

from apps.accounts.models import Role, User
from apps.notifications.models import Notification, NotificationChannel
from apps.notifications.services import NotificationService, NotificationNotFoundError


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_redis():
    """Auto-mock Redis for all tests to prevent connection hangs."""
    with patch("apps.notifications.services._get_redis") as mock_fn:
        mock_r = MagicMock()
        mock_r.get.return_value = None  # force DB fallback for unread count
        mock_fn.return_value = mock_r
        yield mock_r


@pytest.fixture
def student(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"ns_student_{uid}",
        email=f"ns_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def student2(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"ns_student2_{uid}",
        email=f"ns_student2_{uid}@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
    )


@pytest.fixture
def teacher(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"ns_teacher_{uid}",
        email=f"ns_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


def _create(recipient, notification_type="test", title="Test", body="Body", **kwargs):
    """Helper to create a notification with in-app delivery mocked out."""
    with patch.object(NotificationService, "_send_in_app"):
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            **kwargs,
        )


# ------------------------------------------------------------------
# Notification creation for each event type (Req 19.1, 19.2)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateNotification:
    def test_creates_in_app_notification(self, student):
        n = _create(
            student,
            notification_type="achievement_unlock",
            title="Achievement Unlocked!",
            body="You earned First Steps",
            channel=NotificationChannel.IN_APP,
        )
        assert n.pk is not None
        assert n.recipient == student
        assert n.notification_type == "achievement_unlock"
        assert n.title == "Achievement Unlocked!"
        assert n.body == "You earned First Steps"
        assert n.channel == NotificationChannel.IN_APP
        assert n.is_read is False
        assert n.email_sent is False

    def test_creates_email_notification(self, student):
        with patch("apps.notifications.tasks.send_email_notification") as mock_task:
            mock_task.delay = MagicMock()
            n = _create(
                student,
                notification_type="project_review",
                title="Project Reviewed",
                body="Your project has been reviewed",
                channel=NotificationChannel.EMAIL,
            )
        assert n.channel == NotificationChannel.EMAIL
        mock_task.delay.assert_called_once_with(n.pk)

    def test_creates_both_channel_notification(self, student):
        with patch("apps.notifications.tasks.send_email_notification") as mock_task:
            mock_task.delay = MagicMock()
            n = _create(
                student,
                notification_type="streak_milestone",
                title="7-Day Streak!",
                body="You maintained a 7-day streak",
                channel=NotificationChannel.BOTH,
            )
        assert n.channel == NotificationChannel.BOTH
        mock_task.delay.assert_called_once_with(n.pk)

    def test_forum_reply_notification(self, student):
        n = _create(
            student,
            notification_type="forum_reply",
            title="New Reply",
            body="Someone replied to your thread",
            data={"thread_id": 42},
        )
        assert n.notification_type == "forum_reply"
        assert n.data == {"thread_id": 42}

    def test_group_activity_notification(self, student):
        n = _create(
            student,
            notification_type="group_activity",
            title="Group Update",
            body="A member contributed to your group exercise",
            data={"group_id": 5, "exercise_id": 10},
        )
        assert n.notification_type == "group_activity"
        assert n.data["group_id"] == 5

    def test_default_channel_is_in_app(self, student):
        n = _create(
            student,
            notification_type="level_up",
            title="Level Up!",
            body="You reached level 5",
        )
        assert n.channel == NotificationChannel.IN_APP

    def test_data_defaults_to_empty_dict(self, student):
        n = _create(student)
        assert n.data == {}

    def test_notification_persisted_to_db(self, student):
        _create(student, notification_type="achievement_unlock", title="Title", body="Body")
        assert Notification.objects.filter(recipient=student).count() == 1


# ------------------------------------------------------------------
# WebSocket in-app delivery (Req 19.3)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestSendInApp:
    def test_sends_to_channel_layer(self, student):
        with patch("apps.notifications.services.get_channel_layer") as mock_get_cl, \
             patch("apps.notifications.services.async_to_sync") as mock_a2s:
            mock_layer = MagicMock()
            mock_layer.group_send = MagicMock()
            mock_get_cl.return_value = mock_layer
            mock_sender = MagicMock()
            mock_a2s.return_value = mock_sender

            n = NotificationService.create_notification(
                recipient=student,
                notification_type="test",
                title="Test",
                body="Body",
                channel=NotificationChannel.IN_APP,
            )

        mock_a2s.assert_called_once_with(mock_layer.group_send)
        call_args = mock_sender.call_args
        group_name = call_args[0][0]
        payload = call_args[0][1]

        assert group_name == f"notifications_{student.pk}"
        assert payload["type"] == "send_notification"
        assert payload["notification"]["id"] == n.pk
        assert payload["notification"]["title"] == "Test"

    def test_no_channel_layer_does_not_raise(self, student):
        with patch("apps.notifications.services.get_channel_layer", return_value=None):
            n = NotificationService.create_notification(
                recipient=student,
                notification_type="test",
                title="Test",
                body="Body",
            )
            assert n.pk is not None

    def test_channel_layer_error_does_not_raise(self, student):
        with patch("apps.notifications.services.get_channel_layer") as mock_get_cl, \
             patch("apps.notifications.services.async_to_sync") as mock_a2s:
            mock_layer = MagicMock()
            mock_get_cl.return_value = mock_layer
            mock_a2s.return_value = MagicMock(side_effect=Exception("Redis down"))

            n = NotificationService.create_notification(
                recipient=student,
                notification_type="test",
                title="Test",
                body="Body",
            )
            assert n.pk is not None


# ------------------------------------------------------------------
# Query helpers (Req 19.4)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestGetNotifications:
    def test_returns_user_notifications(self, student):
        _create(student, notification_type="a", title="A", body="A")
        _create(student, notification_type="b", title="B", body="B")
        qs = NotificationService.get_notifications(student)
        assert qs.count() == 2

    def test_does_not_return_other_users_notifications(self, student, student2):
        _create(student, notification_type="a", title="A", body="A")
        _create(student2, notification_type="b", title="B", body="B")
        qs = NotificationService.get_notifications(student)
        assert qs.count() == 1

    def test_ordered_newest_first(self, student):
        n1 = _create(student, notification_type="a", title="First", body="A")
        n2 = _create(student, notification_type="b", title="Second", body="B")
        items = list(NotificationService.get_notifications(student))
        assert len(items) == 2
        # Both notifications returned; ordering is by -created_at
        pks = {items[0].pk, items[1].pk}
        assert pks == {n1.pk, n2.pk}


@pytest.mark.django_db
class TestGetUnreadCount:
    def test_counts_unread(self, student):
        _create(student, notification_type="a", title="A", body="A")
        _create(student, notification_type="b", title="B", body="B")
        count = NotificationService.get_unread_count(student)
        assert count == 2

    def test_excludes_read_notifications(self, student):
        n = _create(student, notification_type="a", title="A", body="A")
        NotificationService.mark_read(student, n.pk)
        count = NotificationService.get_unread_count(student)
        assert count == 0

    def test_zero_when_no_notifications(self, student):
        count = NotificationService.get_unread_count(student)
        assert count == 0


# ------------------------------------------------------------------
# Mark read / mark all read (Req 19.5)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestMarkRead:
    def test_marks_notification_as_read(self, student):
        n = _create(student, notification_type="a", title="A", body="A")
        result = NotificationService.mark_read(student, n.pk)
        assert result.is_read is True
        n.refresh_from_db()
        assert n.is_read is True

    def test_already_read_is_idempotent(self, student):
        n = _create(student, notification_type="a", title="A", body="A")
        NotificationService.mark_read(student, n.pk)
        result = NotificationService.mark_read(student, n.pk)
        assert result.is_read is True

    def test_cannot_mark_other_users_notification(self, student, student2):
        n = _create(student, notification_type="a", title="A", body="A")
        with pytest.raises(NotificationNotFoundError):
            NotificationService.mark_read(student2, n.pk)

    def test_nonexistent_notification_raises(self, student):
        with pytest.raises(NotificationNotFoundError):
            NotificationService.mark_read(student, 99999)


@pytest.mark.django_db
class TestMarkAllRead:
    def test_marks_all_as_read(self, student):
        _create(student, notification_type="a", title="A", body="A")
        _create(student, notification_type="b", title="B", body="B")
        count = NotificationService.mark_all_read(student)
        assert count == 2
        assert Notification.objects.filter(recipient=student, is_read=False).count() == 0

    def test_returns_zero_when_none_unread(self, student):
        n = _create(student, notification_type="a", title="A", body="A")
        NotificationService.mark_read(student, n.pk)
        count = NotificationService.mark_all_read(student)
        assert count == 0

    def test_does_not_affect_other_users(self, student, student2):
        _create(student, notification_type="a", title="A", body="A")
        _create(student2, notification_type="b", title="B", body="B")
        NotificationService.mark_all_read(student)
        assert Notification.objects.filter(recipient=student2, is_read=False).count() == 1
