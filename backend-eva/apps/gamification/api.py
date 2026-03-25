"""Gamification API routes — profile, leaderboard, achievements, XP history."""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Query, Router

from apps.accounts.api import jwt_auth
from apps.gamification.models import Achievement, UserAchievement, XPTransaction
from apps.gamification.schemas import (
    AchievementOut,
    GamificationProfileOut,
    LeaderboardEntryOut,
    LeaderboardOut,
    XPTransactionOut,
)
from apps.gamification.services import GamificationService
from common.pagination import PaginatedResponse, PaginationParams

router = Router(tags=["gamification"])


@router.get("/gamification/profile", response=GamificationProfileOut, auth=jwt_auth)
def get_profile(request: HttpRequest):
    """Return the authenticated student's gamification profile."""
    profile = GamificationService.get_or_create_profile(request.auth)
    return GamificationProfileOut(
        total_xp=profile.total_xp,
        current_level=profile.current_level,
        current_streak=profile.current_streak,
        longest_streak=profile.longest_streak,
        last_activity_date=profile.last_activity_date,
    )


@router.get("/gamification/leaderboard", response=LeaderboardOut, auth=jwt_auth)
def get_leaderboard(request: HttpRequest, period: str = "weekly"):
    """Return leaderboard for the given period (weekly or alltime)."""
    if period not in ("weekly", "alltime"):
        period = "weekly"

    data = GamificationService.get_leaderboard(period, request.auth)
    return LeaderboardOut(
        period=data["period"],
        entries=[LeaderboardEntryOut(**e) for e in data["entries"]],
        user_rank=data["user_rank"],
        user_xp=data["user_xp"],
    )


@router.get("/gamification/achievements", response=list[AchievementOut], auth=jwt_auth)
def get_achievements(request: HttpRequest):
    """Return all achievements with unlock status and progress for the user."""
    user = request.auth
    progress = GamificationService.get_achievement_progress(user)

    unlocked_map: dict[int, UserAchievement] = {
        ua.achievement_id: ua
        for ua in UserAchievement.objects.filter(student=user).select_related(
            "achievement"
        )
    }

    result = []
    for ach in Achievement.objects.all():
        ua = unlocked_map.get(ach.pk)
        result.append(
            AchievementOut(
                id=ach.pk,
                name=ach.name,
                description=ach.description,
                icon=ach.icon,
                condition_type=ach.condition_type,
                condition_value=ach.condition_value,
                is_unlocked=ua is not None,
                unlocked_at=ua.unlocked_at if ua else None,
                current_progress=progress.get(ach.condition_type, 0),
            )
        )
    return result


@router.get("/gamification/xp-history", auth=jwt_auth)
def get_xp_history(request: HttpRequest, params: PaginationParams = Query(...)):
    """Return paginated XP transaction log for the authenticated user."""
    qs = XPTransaction.objects.filter(student=request.auth).order_by("-timestamp")
    total = qs.count()
    limit = max(1, min(params.limit, 100))
    offset = max(0, params.offset)
    items = list(qs[offset : offset + limit])

    results = [
        XPTransactionOut(
            id=txn.pk,
            amount=txn.amount,
            source_type=txn.source_type,
            source_id=txn.source_id,
            timestamp=txn.timestamp,
        )
        for txn in items
    ]

    next_offset = offset + limit if offset + limit < total else None
    return PaginatedResponse(
        count=total,
        next_offset=next_offset,
        results=results,
    )
