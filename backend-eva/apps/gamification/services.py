"""GamificationService — XP, levels, streaks, achievements, leaderboards."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import redis
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.gamification.models import (
    Achievement,
    GamificationProfile,
    UserAchievement,
    XPTransaction,
)

# ---------------------------------------------------------------------------
# Redis keys for leaderboards
# ---------------------------------------------------------------------------
LEADERBOARD_ALLTIME_KEY = "leaderboard:alltime"
LEADERBOARD_WEEKLY_KEY = "leaderboard:weekly"

# ---------------------------------------------------------------------------
# Level progression formula
# ---------------------------------------------------------------------------
# XP required to reach level N: 100 * N^1.5 (cumulative)
# Level 1 = 0 XP, Level 2 = 100 XP, Level 3 ≈ 283 XP, etc.
BASE_XP = 100


def xp_for_level(level: int) -> int:
    """Return the cumulative XP required to reach *level*."""
    if level <= 1:
        return 0
    return int(BASE_XP * math.pow(level, 1.5))


# Streak milestones that award bonus XP
STREAK_MILESTONES: dict[int, int] = {
    7: 50,
    30: 200,
    100: 500,
    365: 2000,
}


@dataclass
class LevelUpResult:
    old_level: int
    new_level: int
    total_xp: int


@dataclass
class StreakResult:
    current_streak: int
    longest_streak: int
    milestone_reached: int | None
    bonus_xp: int


def _get_redis() -> redis.Redis:
    """Return a Redis client from the configured URL."""
    return redis.from_url(settings.CACHES["default"].get("LOCATION", settings.CELERY_BROKER_URL))


class GamificationService:
    """Handles XP awards, leveling, streaks, achievements, and leaderboards."""

    # ------------------------------------------------------------------
    # Profile helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_or_create_profile(student: User) -> GamificationProfile:
        """Return the student's gamification profile, creating one if needed."""
        profile, _ = GamificationProfile.objects.get_or_create(student=student)
        return profile

    # ------------------------------------------------------------------
    # XP
    # ------------------------------------------------------------------

    @staticmethod
    def award_xp(
        student: User,
        source_type: str,
        source_id: int,
        amount: int,
    ) -> XPTransaction:
        """Award XP, update profile, update leaderboards, check level up.

        Returns the created XPTransaction.
        """
        profile = GamificationService.get_or_create_profile(student)

        # Record transaction
        txn = XPTransaction.objects.create(
            student=student,
            amount=amount,
            source_type=source_type,
            source_id=source_id,
        )

        # Update profile
        profile.total_xp += amount
        profile.save(update_fields=["total_xp", "updated_at"])

        # Update Redis leaderboards
        try:
            r = _get_redis()
            r.zincrby(LEADERBOARD_ALLTIME_KEY, amount, str(student.pk))
            r.zincrby(LEADERBOARD_WEEKLY_KEY, amount, str(student.pk))
        except Exception:
            pass  # Leaderboard update is best-effort

        # Check level up
        GamificationService.check_level_up(student)

        # Evaluate achievements
        GamificationService.evaluate_achievements(student)

        return txn

    # ------------------------------------------------------------------
    # Level up
    # ------------------------------------------------------------------

    @staticmethod
    def check_level_up(student: User) -> LevelUpResult | None:
        """Advance level if XP threshold is crossed. Returns result or None."""
        profile = GamificationService.get_or_create_profile(student)
        old_level = profile.current_level

        # Find the highest level the student qualifies for
        new_level = old_level
        while xp_for_level(new_level + 1) <= profile.total_xp:
            new_level += 1

        if new_level <= old_level:
            return None

        profile.current_level = new_level
        profile.save(update_fields=["current_level", "updated_at"])

        # TODO: Send level-up notification via NotificationService

        return LevelUpResult(
            old_level=old_level,
            new_level=new_level,
            total_xp=profile.total_xp,
        )

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    @staticmethod
    def evaluate_achievements(student: User) -> list[Achievement]:
        """Check all achievement conditions and grant any newly met ones.

        Idempotent — unique_together on UserAchievement prevents duplicates.
        Returns list of newly granted achievements.
        """
        profile = GamificationService.get_or_create_profile(student)
        granted: list[Achievement] = []

        # Build a stats dict for condition evaluation
        stats: dict[str, int] = {
            "xp_total": profile.total_xp,
            "streak": profile.current_streak,
            "longest_streak": profile.longest_streak,
            "current_level": profile.current_level,
        }

        # Count completed lessons from LessonSession
        from apps.exercises.models import LessonSession

        stats["lessons_completed"] = LessonSession.objects.filter(
            student=student, is_completed=True
        ).count()

        all_achievements = Achievement.objects.all()
        already_unlocked = set(
            UserAchievement.objects.filter(student=student).values_list(
                "achievement_id", flat=True
            )
        )

        for achievement in all_achievements:
            if achievement.pk in already_unlocked:
                continue

            current_value = stats.get(achievement.condition_type, 0)
            if current_value >= achievement.condition_value:
                try:
                    UserAchievement.objects.create(
                        student=student,
                        achievement=achievement,
                    )
                    granted.append(achievement)
                    # TODO: Send achievement notification via NotificationService
                except IntegrityError:
                    pass  # Already granted (race condition guard)

        return granted

    @staticmethod
    def get_achievement_progress(student: User) -> dict[str, int]:
        """Return current progress values for all condition types."""
        profile = GamificationService.get_or_create_profile(student)

        from apps.exercises.models import LessonSession

        return {
            "xp_total": profile.total_xp,
            "streak": profile.current_streak,
            "longest_streak": profile.longest_streak,
            "current_level": profile.current_level,
            "lessons_completed": LessonSession.objects.filter(
                student=student, is_completed=True
            ).count(),
        }

    # ------------------------------------------------------------------
    # Streaks
    # ------------------------------------------------------------------

    @staticmethod
    def update_streak(student: User) -> StreakResult:
        """Increment streak if last_activity_date != today (student tz).

        Awards bonus XP at milestones (7, 30, 100, 365 days).
        """
        profile = GamificationService.get_or_create_profile(student)
        today = tz.localdate(timezone=tz.get_current_timezone())

        milestone_reached: int | None = None
        bonus_xp = 0

        if profile.last_activity_date == today:
            # Already active today — no change
            return StreakResult(
                current_streak=profile.current_streak,
                longest_streak=profile.longest_streak,
                milestone_reached=None,
                bonus_xp=0,
            )

        # Increment streak
        profile.current_streak += 1
        profile.last_activity_date = today

        if profile.current_streak > profile.longest_streak:
            profile.longest_streak = profile.current_streak

        profile.save(
            update_fields=[
                "current_streak",
                "longest_streak",
                "last_activity_date",
                "updated_at",
            ]
        )

        # Check milestones
        if profile.current_streak in STREAK_MILESTONES:
            milestone_reached = profile.current_streak
            bonus_xp = STREAK_MILESTONES[milestone_reached]
            GamificationService.award_xp(
                student=student,
                source_type="streak_bonus",
                source_id=milestone_reached,
                amount=bonus_xp,
            )

        return StreakResult(
            current_streak=profile.current_streak,
            longest_streak=profile.longest_streak,
            milestone_reached=milestone_reached,
            bonus_xp=bonus_xp,
        )

    # ------------------------------------------------------------------
    # Leaderboard
    # ------------------------------------------------------------------

    @staticmethod
    def get_leaderboard(period: str, user: User) -> dict:
        """Return top 100 + requesting user's rank/xp.

        *period* must be ``"weekly"`` or ``"alltime"``.
        Falls back to DB query if Redis is unavailable.
        """
        key = LEADERBOARD_WEEKLY_KEY if period == "weekly" else LEADERBOARD_ALLTIME_KEY

        try:
            r = _get_redis()
            # Top 100 (score descending)
            top_raw = r.zrevrange(key, 0, 99, withscores=True)

            entries = []
            user_ids = [int(uid) for uid, _ in top_raw]
            users_map = {
                u.pk: u
                for u in User.objects.filter(pk__in=user_ids).only(
                    "pk", "display_name"
                )
            }

            for rank, (uid_bytes, score) in enumerate(top_raw, start=1):
                uid = int(uid_bytes)
                u = users_map.get(uid)
                entries.append(
                    {
                        "rank": rank,
                        "student_id": uid,
                        "display_name": u.display_name if u else "Unknown",
                        "total_xp": int(score),
                    }
                )

            # Requesting user's rank
            user_score = r.zscore(key, str(user.pk))
            user_rank = None
            user_xp = 0
            if user_score is not None:
                user_xp = int(user_score)
                # zrevrank is 0-indexed
                raw_rank = r.zrevrank(key, str(user.pk))
                user_rank = (raw_rank + 1) if raw_rank is not None else None

            return {
                "period": period,
                "entries": entries,
                "user_rank": user_rank,
                "user_xp": user_xp,
            }

        except Exception:
            # Fallback: query DB directly
            return GamificationService._leaderboard_from_db(period, user)

    @staticmethod
    def _leaderboard_from_db(period: str, user: User) -> dict:
        """DB fallback for leaderboard when Redis is unavailable."""
        profiles = (
            GamificationProfile.objects.select_related("student")
            .order_by("-total_xp")[:100]
        )

        entries = []
        for rank, p in enumerate(profiles, start=1):
            entries.append(
                {
                    "rank": rank,
                    "student_id": p.student_id,
                    "display_name": p.student.display_name,
                    "total_xp": p.total_xp,
                }
            )

        # User's rank
        user_profile = GamificationProfile.objects.filter(student=user).first()
        user_rank = None
        user_xp = 0
        if user_profile:
            user_xp = user_profile.total_xp
            user_rank = (
                GamificationProfile.objects.filter(
                    total_xp__gt=user_profile.total_xp
                ).count()
                + 1
            )

        return {
            "period": period,
            "entries": entries,
            "user_rank": user_rank,
            "user_xp": user_xp,
        }

    # ------------------------------------------------------------------
    # Streak reset (called by Celery task)
    # ------------------------------------------------------------------

    @staticmethod
    def reset_expired_streaks() -> int:
        """Reset streaks for students who were inactive yesterday.

        Returns the number of profiles reset.
        """
        yesterday = date.today()
        # Students whose last_activity_date is before yesterday
        expired = GamificationProfile.objects.filter(
            current_streak__gt=0,
        ).exclude(
            last_activity_date__gte=yesterday,
        )
        count = expired.update(current_streak=0)
        return count

    # ------------------------------------------------------------------
    # Weekly leaderboard reset (called by Celery task)
    # ------------------------------------------------------------------

    @staticmethod
    def reset_weekly_leaderboard() -> None:
        """Clear the weekly leaderboard Redis sorted set."""
        try:
            r = _get_redis()
            r.delete(LEADERBOARD_WEEKLY_KEY)
        except Exception:
            pass  # Best-effort
