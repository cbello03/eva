"""Tests for ForumService — forum CRUD, pagination, flagging, upvotes."""

import uuid

import pytest

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment
from apps.social.models import ForumReply, ForumThread, ReplyUpvote
from apps.social.services import (
    ForumService,
    PostNotFoundError,
    ReplyNotFoundError,
    ThreadNotFoundError,
)
from common.exceptions import InsufficientRoleError, NotEnrolledError


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def teacher(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"fs_teacher_{uid}",
        email=f"fs_teacher_{uid}@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest.fixture
def student(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"fs_student_{uid}",
        email=f"fs_student_{uid}@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def student2(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"fs_student2_{uid}",
        email=f"fs_student2_{uid}@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
    )


@pytest.fixture
def admin(db):
    uid = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"fs_admin_{uid}",
        email=f"fs_admin_{uid}@test.com",
        password="Pass1234",
        display_name="Admin",
        role=Role.ADMIN,
    )


@pytest.fixture
def course(teacher):
    return Course.objects.create(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


@pytest.fixture
def enrollment2(student2, course):
    return Enrollment.objects.create(student=student2, course=course)


@pytest.fixture
def thread(student, course, enrollment):
    return ForumService.create_thread(student, course.pk, "Thread Title", "Thread body")


# ------------------------------------------------------------------
# Thread creation
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateThread:
    def test_creates_thread(self, student, course, enrollment):
        thread = ForumService.create_thread(student, course.pk, "Title", "Body")
        assert thread.pk is not None
        assert thread.title == "Title"
        assert thread.body == "Body"
        assert thread.author == student
        assert thread.course == course
        assert thread.is_hidden is False

    def test_sanitizes_content(self, student, course, enrollment):
        thread = ForumService.create_thread(
            student, course.pk, "<script>alert(1)</script>Title", "Body<img onerror=x>"
        )
        assert "<script>" not in thread.title
        assert "onerror" not in thread.body

    def test_rejects_unenrolled_student(self, student, course):
        with pytest.raises(NotEnrolledError):
            ForumService.create_thread(student, course.pk, "Title", "Body")

    def test_teacher_owner_can_create(self, teacher, course):
        thread = ForumService.create_thread(teacher, course.pk, "Teacher Thread", "Body")
        assert thread.author == teacher

    def test_admin_can_create(self, admin, course):
        thread = ForumService.create_thread(admin, course.pk, "Admin Thread", "Body")
        assert thread.author == admin

    def test_invalid_course_raises(self, student):
        from apps.courses.services import CourseNotFoundError

        with pytest.raises(CourseNotFoundError):
            ForumService.create_thread(student, 99999, "Title", "Body")


# ------------------------------------------------------------------
# Thread listing and pagination
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestListThreads:
    def test_returns_threads(self, student, course, enrollment, thread):
        total, items = ForumService.list_threads(student, course.pk)
        assert total == 1
        assert len(items) == 1
        assert items[0].pk == thread.pk

    def test_excludes_hidden_threads(self, student, course, enrollment, thread):
        thread.is_hidden = True
        thread.save()
        total, items = ForumService.list_threads(student, course.pk)
        assert total == 0
        assert len(items) == 0

    def test_pagination_offset_limit(self, student, course, enrollment):
        for i in range(5):
            ForumService.create_thread(student, course.pk, f"Thread {i}", "Body")
        total, items = ForumService.list_threads(student, course.pk, offset=0, limit=2)
        assert total == 5
        assert len(items) == 2

    def test_pagination_offset_beyond(self, student, course, enrollment, thread):
        total, items = ForumService.list_threads(student, course.pk, offset=100, limit=20)
        assert total == 1
        assert len(items) == 0

    def test_limit_clamped_to_100(self, student, course, enrollment, thread):
        total, items = ForumService.list_threads(student, course.pk, offset=0, limit=200)
        # limit is clamped to 100 internally
        assert total == 1
        assert len(items) == 1

    def test_limit_clamped_to_1_minimum(self, student, course, enrollment, thread):
        total, items = ForumService.list_threads(student, course.pk, offset=0, limit=0)
        assert len(items) == 1  # limit=0 clamped to 1

    def test_sorted_by_last_activity_desc(self, student, course, enrollment):
        from django.utils import timezone as tz
        from datetime import timedelta

        t1 = ForumService.create_thread(student, course.pk, "First", "Body")
        t2 = ForumService.create_thread(student, course.pk, "Second", "Body")
        # Force distinct timestamps so ordering is deterministic
        t1.last_activity_at = tz.now() - timedelta(minutes=5)
        t1.save(update_fields=["last_activity_at"])
        t2.last_activity_at = tz.now()
        t2.save(update_fields=["last_activity_at"])

        _, items = ForumService.list_threads(student, course.pk)
        assert items[0].pk == t2.pk
        assert items[1].pk == t1.pk

    def test_rejects_unenrolled(self, student, course):
        with pytest.raises(NotEnrolledError):
            ForumService.list_threads(student, course.pk)


# ------------------------------------------------------------------
# Get thread
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestGetThread:
    def test_returns_thread(self, student, course, enrollment, thread):
        result = ForumService.get_thread(student, thread.pk)
        assert result.pk == thread.pk

    def test_not_found(self, student, course, enrollment):
        with pytest.raises(ThreadNotFoundError):
            ForumService.get_thread(student, 99999)

    def test_rejects_unenrolled(self, student2, thread):
        with pytest.raises(NotEnrolledError):
            ForumService.get_thread(student2, thread.pk)


# ------------------------------------------------------------------
# Reply creation
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateReply:
    def test_creates_reply(self, student, thread, enrollment):
        reply = ForumService.create_reply(student, thread.pk, "Reply body")
        assert reply.pk is not None
        assert reply.body == "Reply body"
        assert reply.author == student
        assert reply.thread == thread

    def test_updates_thread_last_activity(self, student, thread, enrollment):
        old_activity = thread.last_activity_at
        ForumService.create_reply(student, thread.pk, "Reply")
        thread.refresh_from_db()
        assert thread.last_activity_at >= old_activity

    def test_sanitizes_body(self, student, thread, enrollment):
        reply = ForumService.create_reply(
            student, thread.pk, "<script>xss</script>Clean"
        )
        assert "<script>" not in reply.body

    def test_rejects_unenrolled(self, student2, thread):
        with pytest.raises(NotEnrolledError):
            ForumService.create_reply(student2, thread.pk, "Reply")

    def test_invalid_thread_raises(self, student, enrollment):
        with pytest.raises(ThreadNotFoundError):
            ForumService.create_reply(student, 99999, "Reply")


# ------------------------------------------------------------------
# Flagging
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestFlagPost:
    def test_teacher_flags_thread(self, teacher, thread):
        ForumService.flag_post(teacher, thread.pk, post_type="thread")
        thread.refresh_from_db()
        assert thread.is_hidden is True

    def test_admin_flags_thread(self, admin, thread):
        ForumService.flag_post(admin, thread.pk, post_type="thread")
        thread.refresh_from_db()
        assert thread.is_hidden is True

    def test_teacher_flags_reply(self, teacher, student, thread, enrollment):
        reply = ForumService.create_reply(student, thread.pk, "Bad reply")
        ForumService.flag_post(teacher, reply.pk, post_type="reply")
        reply.refresh_from_db()
        assert reply.is_hidden is True

    def test_student_cannot_flag(self, student, thread, enrollment):
        with pytest.raises(InsufficientRoleError):
            ForumService.flag_post(student, thread.pk, post_type="thread")

    def test_flag_nonexistent_thread_raises(self, teacher):
        with pytest.raises(PostNotFoundError):
            ForumService.flag_post(teacher, 99999, post_type="thread")

    def test_flag_nonexistent_reply_raises(self, teacher):
        with pytest.raises(PostNotFoundError):
            ForumService.flag_post(teacher, 99999, post_type="reply")


# ------------------------------------------------------------------
# Upvote toggle
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestToggleUpvote:
    def test_first_upvote_increments(self, student, thread, enrollment):
        reply = ForumService.create_reply(student, thread.pk, "Reply")
        result = ForumService.toggle_upvote(student, reply.pk)
        assert result.upvote_count == 1
        assert ReplyUpvote.objects.filter(reply=reply, user=student).exists()

    def test_second_upvote_removes(self, student, thread, enrollment):
        reply = ForumService.create_reply(student, thread.pk, "Reply")
        ForumService.toggle_upvote(student, reply.pk)
        result = ForumService.toggle_upvote(student, reply.pk)
        assert result.upvote_count == 0
        assert not ReplyUpvote.objects.filter(reply=reply, user=student).exists()

    def test_toggle_cycle(self, student, thread, enrollment):
        reply = ForumService.create_reply(student, thread.pk, "Reply")
        ForumService.toggle_upvote(student, reply.pk)  # +1
        ForumService.toggle_upvote(student, reply.pk)  # -1
        result = ForumService.toggle_upvote(student, reply.pk)  # +1
        assert result.upvote_count == 1

    def test_multiple_users_upvote(self, student, student2, thread, enrollment, enrollment2):
        reply = ForumService.create_reply(student, thread.pk, "Reply")
        ForumService.toggle_upvote(student, reply.pk)
        result = ForumService.toggle_upvote(student2, reply.pk)
        assert result.upvote_count == 2

    def test_rejects_unenrolled(self, student2, thread, enrollment):
        reply = ForumService.create_reply(
            # Use enrolled student to create the reply
            thread.author, thread.pk, "Reply"
        )
        with pytest.raises(NotEnrolledError):
            ForumService.toggle_upvote(student2, reply.pk)

    def test_nonexistent_reply_raises(self, student, enrollment):
        with pytest.raises(ReplyNotFoundError):
            ForumService.toggle_upvote(student, 99999)
