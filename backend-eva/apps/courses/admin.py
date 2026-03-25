"""Courses app admin registration."""

from django.contrib import admin

from apps.courses.models import Course, Enrollment, Lesson, Unit


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "status", "published_at", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "description")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "unit", "order")
    list_filter = ("unit__course",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "is_active", "enrolled_at")
    list_filter = ("is_active", "course")
