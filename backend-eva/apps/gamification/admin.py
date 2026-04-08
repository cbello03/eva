"""Gamification app admin registration."""

from django.contrib import admin

from apps.gamification.models import (
    Achievement,
    GamificationProfile,
    UserAchievement,
    XPTransaction,
)

admin.site.register(GamificationProfile)
admin.site.register(XPTransaction)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
