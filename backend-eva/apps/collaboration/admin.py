"""Collaboration app admin registration."""

from django.contrib import admin

from apps.collaboration.models import CollabGroup, CollabGroupMember, CollabSubmission


@admin.register(CollabGroup)
class CollabGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "exercise", "max_size", "is_submitted", "created_at")
    list_filter = ("is_submitted",)


@admin.register(CollabGroupMember)
class CollabGroupMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "student", "joined_at", "last_contribution_at")


@admin.register(CollabSubmission)
class CollabSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "submitted_at")
