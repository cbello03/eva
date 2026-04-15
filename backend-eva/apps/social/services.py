"""ForumService — forum thread and reply business logic."""

from __future__ import annotations

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone as tz

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment
from apps.social.models import ChatMessage, ForumReply, ForumThread, ReplyUpvote
from common.exceptions import DomainError, InsufficientRoleError, NotEnrolledError
from common.sanitization import sanitize_html


class ThreadNotFoundError(DomainError):
    status_code = 404
    code = "thread_not_found"

    def __init__(self, detail: str = "Forum thread not found"):
        super().__init__(detail)


class ReplyNotFoundError(DomainError):
    status_code = 404
    code = "reply_not_found"

    def __init__(self, detail: str = "Forum reply not found"):
        super().__init__(detail)


class PostNotFoundError(DomainError):
    status_code = 404
    code = "post_not_found"

    def __init__(self, detail: str = "Forum post not found"):
        super().__init__(detail)


def _check_enrollment(user: User, course: Course) -> None:
    """Raise if *user* is not actively enrolled in *course*.

    Teachers who own the course and Admins bypass enrollment checks.
    """
    if user.role == Role.ADMIN:
        return
    if user.role == Role.TEACHER and course.teacher_id == user.pk:
        return
    if not Enrollment.objects.filter(
        student=user, course=course, is_active=True
    ).exists():
        raise NotEnrolledError()


class ForumService:
    """Handles forum threads, replies, flagging, and upvotes."""

    # ------------------------------------------------------------------
    # Threads
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_course_access(user: User, course_id: int) -> Course:
        """Return course if user can access social features for it."""
        course = ForumService._get_course(course_id)
        _check_enrollment(user, course)
        return course

    @staticmethod
    def create_thread(user: User, course_id: int, title: str, body: str) -> ForumThread:
        """Create a new forum thread in a course."""
        course = ForumService.ensure_course_access(user, course_id)

        now = tz.now()
        return ForumThread.objects.create(
            course=course,
            author=user,
            title=sanitize_html(title),
            body=sanitize_html(body),
            last_activity_at=now,
        )

    @staticmethod
    def list_threads(
        user: User,
        course_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[int, list[ForumThread]]:
        """Return threads sorted by last_activity_at desc, paginated.

        Returns (total_count, page_items).
        """
        course = ForumService.ensure_course_access(user, course_id)

        qs = (
            ForumThread.objects.filter(course=course, is_hidden=False)
            .select_related("author")
            .order_by("-last_activity_at")
        )
        total = qs.count()
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        items = list(qs[offset : offset + limit])
        return total, items

    @staticmethod
    def get_thread(user: User, thread_id: int) -> ForumThread:
        """Return a thread with its visible replies."""
        thread = ForumService._get_thread(thread_id)
        _check_enrollment(user, thread.course)
        return thread

    # ------------------------------------------------------------------
    # Replies
    # ------------------------------------------------------------------

    @staticmethod
    def create_reply(user: User, thread_id: int, body: str) -> ForumReply:
        """Reply to a thread. Updates thread last_activity_at."""
        thread = ForumService._get_thread(thread_id)
        _check_enrollment(user, thread.course)

        reply = ForumReply.objects.create(
            thread=thread,
            author=user,
            body=sanitize_html(body),
        )

        # Update thread activity timestamp
        thread.last_activity_at = tz.now()
        thread.save(update_fields=["last_activity_at", "updated_at"])

        # TODO: notify thread author via NotificationService when implemented
        return reply

    # ------------------------------------------------------------------
    # Flagging
    # ------------------------------------------------------------------

    @staticmethod
    def flag_post(user: User, post_id: int, post_type: str = "thread") -> None:
        """Flag a thread or reply as hidden. Teacher/Admin only."""
        if user.role not in (Role.TEACHER, Role.ADMIN):
            raise InsufficientRoleError("Only teachers and admins can flag posts")

        if post_type == "reply":
            try:
                reply = ForumReply.objects.select_related("thread__course").get(pk=post_id)
            except ForumReply.DoesNotExist:
                raise PostNotFoundError()
            reply.is_hidden = True
            reply.save(update_fields=["is_hidden", "updated_at"])
            # TODO: notify post author via NotificationService
        else:
            try:
                thread = ForumThread.objects.get(pk=post_id)
            except ForumThread.DoesNotExist:
                raise PostNotFoundError()
            thread.is_hidden = True
            thread.save(update_fields=["is_hidden", "updated_at"])
            # TODO: notify post author via NotificationService

    # ------------------------------------------------------------------
    # Upvotes
    # ------------------------------------------------------------------

    @staticmethod
    def toggle_upvote(user: User, reply_id: int) -> ForumReply:
        """Toggle upvote on a reply. Returns updated reply."""
        try:
            reply = ForumReply.objects.select_related("thread__course").get(pk=reply_id)
        except ForumReply.DoesNotExist:
            raise ReplyNotFoundError()

        _check_enrollment(user, reply.thread.course)

        upvote, created = ReplyUpvote.objects.get_or_create(
            reply=reply, user=user
        )
        if not created:
            upvote.delete()
            ForumReply.objects.filter(pk=reply_id).update(
                upvote_count=models.F("upvote_count") - 1
            )
        else:
            ForumReply.objects.filter(pk=reply_id).update(
                upvote_count=models.F("upvote_count") + 1
            )

        reply.refresh_from_db()
        return reply

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_course(course_id: int) -> Course:
        try:
            return Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            from apps.courses.services import CourseNotFoundError
            raise CourseNotFoundError()

    @staticmethod
    def _get_thread(thread_id: int) -> ForumThread:
        try:
            return (
                ForumThread.objects.select_related("author", "course")
                .get(pk=thread_id)
            )
        except ForumThread.DoesNotExist:
            raise ThreadNotFoundError()
