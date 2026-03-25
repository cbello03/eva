"""Gamification Celery tasks — streak resets and leaderboard resets."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="gamification.reset_expired_streaks")
def reset_expired_streaks() -> int:
    """Daily task: reset streaks for students inactive yesterday."""
    from apps.gamification.services import GamificationService

    count = GamificationService.reset_expired_streaks()
    logger.info("Reset %d expired streaks", count)
    return count


@shared_task(name="gamification.reset_weekly_leaderboard")
def reset_weekly_leaderboard() -> None:
    """Weekly task: clear the weekly leaderboard Redis sorted set."""
    from apps.gamification.services import GamificationService

    GamificationService.reset_weekly_leaderboard()
    logger.info("Weekly leaderboard reset complete")
