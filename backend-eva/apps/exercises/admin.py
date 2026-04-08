"""Exercises app admin registration."""

from django.contrib import admin

from apps.exercises.models import AnswerRecord, Exercise, LessonSession


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("lesson", "exercise_type", "order", "difficulty", "is_collaborative")
    list_filter = ("exercise_type", "difficulty", "is_collaborative")
    search_fields = ("question_text", "topic")


@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "is_completed", "correct_first_attempt", "total_exercises")
    list_filter = ("is_completed",)


@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "exercise", "is_correct", "is_first_attempt", "answered_at")
    list_filter = ("is_correct", "is_first_attempt")
