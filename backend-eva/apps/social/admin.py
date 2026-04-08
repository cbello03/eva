"""Social app admin registration."""

from django.contrib import admin

from apps.social.models import ChatMessage, ForumReply, ForumThread, ReplyUpvote

admin.site.register(ForumThread)
admin.site.register(ForumReply)
admin.site.register(ReplyUpvote)
admin.site.register(ChatMessage)
