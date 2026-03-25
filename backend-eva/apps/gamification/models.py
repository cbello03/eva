"""Gamification app models — XP, levels, streaks, achievements, leaderboards."""

from django.db import models

from common.models import TimestampedModel


class GamificationProfile(TimestampedModel):
    """Aggregate gamification state for a student."""

    student = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="gamification_profile",
    )
    total_xp = models.PositiveIntegerField(default=0)
    current_level = models.PositiveIntegerField(default=1)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "gamification_profile"

    def __str__(self) -> str:
        return f"GamificationProfile(student={self.student_id}, xp={self.total_xp}, level={self.current_level})"


class XPTransaction(TimestampedModel):
    """Immutable log of every XP award."""

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="xp_transactions",
    )
    amount = models.PositiveIntegerField()
    source_type = models.CharField(max_length=50)  # "lesson", "achievement", "streak_bonus", "collab"
    source_id = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_xp_transaction"

    def __str__(self) -> str:
        return f"XPTransaction(student={self.student_id}, +{self.amount} from {self.source_type})"


class Achievement(TimestampedModel):
    """Achievement definition (system-wide)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=100)
    condition_type = models.CharField(max_length=50)  # "xp_total", "streak", "lessons_completed", etc.
    condition_value = models.PositiveIntegerField()

    class Meta:
        db_table = "gamification_achievement"

    def __str__(self) -> str:
        return f"Achievement({self.name})"


class UserAchievement(TimestampedModel):
    """Tracks which achievements a student has unlocked."""

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="user_achievements",
    )
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_user_achievement"
        unique_together = [("student", "achievement")]

    def __str__(self) -> str:
        return f"UserAchievement(student={self.student_id}, achievement={self.achievement.name})"
