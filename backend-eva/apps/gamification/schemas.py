"""Gamification app Pydantic schemas for request/response validation."""

from datetime import date, datetime

from ninja import Schema


class GamificationProfileOut(Schema):
    """Full gamification profile for a student."""

    total_xp: int
    current_level: int
    current_streak: int
    longest_streak: int
    last_activity_date: date | None


class XPTransactionOut(Schema):
    """Single XP transaction record."""

    id: int
    amount: int
    source_type: str
    source_id: int
    timestamp: datetime


class AchievementOut(Schema):
    """Achievement with unlock status and progress toward condition."""

    id: int
    name: str
    description: str
    icon: str
    condition_type: str
    condition_value: int
    is_unlocked: bool
    unlocked_at: datetime | None = None
    current_progress: int = 0


class StreakOut(Schema):
    """Streak information for a student."""

    current_streak: int
    longest_streak: int
    last_activity_date: date | None


class LeaderboardEntryOut(Schema):
    """Single entry in the leaderboard."""

    rank: int
    student_id: int
    display_name: str
    total_xp: int


class LeaderboardOut(Schema):
    """Leaderboard response with top entries and requesting user's position."""

    period: str
    entries: list[LeaderboardEntryOut]
    user_rank: int | None = None
    user_xp: int = 0
