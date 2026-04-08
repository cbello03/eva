"""Social app models — ForumThread, ForumReply, ReplyUpvote, ChatMessage."""

from django.db import models

from apps.accounts.models import User
from apps.courses.models import Course
from common.models import TimestampedModel


class ForumThread(TimestampedModel):
    """A discussion thread within a course forum."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="forum_threads"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="forum_threads"
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_hidden = models.BooleanField(default=False)
    last_activity_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "social_forum_thread"
        ordering = ["-last_activity_at"]

    def __str__(self) -> str:
        return self.title


class ForumReply(TimestampedModel):
    """A reply within a forum thread."""

    thread = models.ForeignKey(
        ForumThread, on_delete=models.CASCADE, related_name="replies"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="forum_replies"
    )
    body = models.TextField()
    is_hidden = models.BooleanField(default=False)
    upvote_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "social_forum_reply"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Reply by {self.author.email} on {self.thread.title}"


class ReplyUpvote(models.Model):
    """Tracks which users have upvoted a reply (one per user per reply)."""

    reply = models.ForeignKey(
        ForumReply, on_delete=models.CASCADE, related_name="upvotes"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reply_upvotes"
    )

    class Meta:
        db_table = "social_reply_upvote"
        unique_together = [("reply", "user")]

    def __str__(self) -> str:
        return f"{self.user.email} ↑ reply #{self.reply_id}"


class ChatMessage(TimestampedModel):
    """A real-time chat message within a course chat room."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="chat_messages"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_messages"
    )
    content = models.CharField(max_length=2000)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_chat_message"
        ordering = ["sent_at"]

    def __str__(self) -> str:
        return f"Chat by {self.author.email} in {self.course.title}"
