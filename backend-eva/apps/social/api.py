"""Social API routes — forums (threads, replies, flagging, upvotes)."""

from django.http import HttpRequest
from ninja import Query, Router

from apps.accounts.api import jwt_auth
from apps.accounts.models import Role
from apps.social.schemas import (
    ReplyCreateIn,
    ReplyOut,
    ThreadCreateIn,
    ThreadListOut,
    ThreadOut,
)
from apps.social.services import ForumService
from common.permissions import require_role

router = Router(tags=["social"], auth=jwt_auth)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _thread_out(thread, include_replies: bool = False) -> ThreadOut:
    """Build a ThreadOut from a ForumThread instance."""
    replies = []
    if include_replies:
        for r in thread.replies.filter(is_hidden=False).select_related("author"):
            replies.append(ReplyOut(
                id=r.pk,
                thread_id=r.thread_id,
                author_id=r.author_id,
                author_display_name=r.author.display_name,
                body=r.body,
                is_hidden=r.is_hidden,
                upvote_count=r.upvote_count,
                created_at=r.created_at,
            ))
    return ThreadOut(
        id=thread.pk,
        course_id=thread.course_id,
        author_id=thread.author_id,
        author_display_name=thread.author.display_name,
        title=thread.title,
        body=thread.body,
        is_hidden=thread.is_hidden,
        last_activity_at=thread.last_activity_at,
        created_at=thread.created_at,
        replies=replies,
    )


# ------------------------------------------------------------------
# Thread endpoints
# ------------------------------------------------------------------

@router.get("/courses/{course_id}/forum/threads", response=ThreadListOut)
def list_threads(
    request: HttpRequest,
    course_id: int,
    offset: int = Query(0),
    limit: int = Query(20),
):
    """List forum threads for a course (paginated, 20/page)."""
    total, threads = ForumService.list_threads(
        request.auth, course_id, offset=offset, limit=limit
    )
    next_offset = offset + limit if offset + limit < total else None
    return ThreadListOut(
        count=total,
        next_offset=next_offset,
        results=[_thread_out(t) for t in threads],
    )


@router.post("/courses/{course_id}/forum/threads", response={201: ThreadOut})
def create_thread(request: HttpRequest, course_id: int, payload: ThreadCreateIn):
    """Create a new forum thread in a course."""
    thread = ForumService.create_thread(
        request.auth, course_id, payload.title, payload.body
    )
    return 201, _thread_out(thread)


@router.get("/forum/threads/{thread_id}", response=ThreadOut)
def get_thread(request: HttpRequest, thread_id: int):
    """Get thread detail with replies."""
    thread = ForumService.get_thread(request.auth, thread_id)
    return _thread_out(thread, include_replies=True)


# ------------------------------------------------------------------
# Reply endpoints
# ------------------------------------------------------------------

@router.post("/forum/threads/{thread_id}/replies", response={201: ReplyOut})
def create_reply(request: HttpRequest, thread_id: int, payload: ReplyCreateIn):
    """Reply to a forum thread."""
    reply = ForumService.create_reply(request.auth, thread_id, payload.body)
    return 201, ReplyOut(
        id=reply.pk,
        thread_id=reply.thread_id,
        author_id=reply.author_id,
        author_display_name=request.auth.display_name,
        body=reply.body,
        is_hidden=reply.is_hidden,
        upvote_count=reply.upvote_count,
        created_at=reply.created_at,
    )


# ------------------------------------------------------------------
# Flagging
# ------------------------------------------------------------------

@router.post("/forum/posts/{post_id}/flag", response={204: None})
@require_role(Role.TEACHER, Role.ADMIN)
def flag_post(request: HttpRequest, post_id: int, post_type: str = Query("thread")):
    """Flag a forum thread or reply as hidden (Teacher/Admin only)."""
    ForumService.flag_post(request.auth, post_id, post_type=post_type)
    return 204, None


# ------------------------------------------------------------------
# Upvotes
# ------------------------------------------------------------------

@router.post("/forum/replies/{reply_id}/upvote", response=ReplyOut)
def toggle_upvote(request: HttpRequest, reply_id: int):
    """Toggle upvote on a forum reply."""
    reply = ForumService.toggle_upvote(request.auth, reply_id)
    return ReplyOut(
        id=reply.pk,
        thread_id=reply.thread_id,
        author_id=reply.author_id,
        author_display_name=reply.author.display_name,
        body=reply.body,
        is_hidden=reply.is_hidden,
        upvote_count=reply.upvote_count,
        created_at=reply.created_at,
    )
