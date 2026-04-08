"""Collaboration Celery tasks — inactive member detection."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="collaboration.check_inactive_collab_members")
def check_inactive_collab_members() -> int:
    """Periodic task: find group members with no contribution within 48 hours.

    Notifies inactive members and their course teachers.
    Returns the number of inactive members found.
    """
    from apps.collaboration.services import CollaborationService

    inactive_members = CollaborationService.check_inactive_members(hours=48)

    # TODO: notify each inactive member and their teacher via NotificationService
    for member in inactive_members:
        logger.info(
            "Inactive collab member: student=%s group=%s exercise=%s",
            member.student.email,
            member.group_id,
            member.group.exercise_id,
        )

    logger.info("Found %d inactive collaboration members", len(inactive_members))
    return len(inactive_members)
