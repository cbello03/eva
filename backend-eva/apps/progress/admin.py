"""Progress app admin registration."""

from django.contrib import admin

from apps.progress.models import (
    CourseProgress,
    DailyActivity,
    LessonProgress,
    SpacedRepetitionItem,
    TopicMastery,
)

admin.site.register(CourseProgress)
admin.site.register(LessonProgress)
admin.site.register(DailyActivity)
admin.site.register(TopicMastery)
admin.site.register(SpacedRepetitionItem)
