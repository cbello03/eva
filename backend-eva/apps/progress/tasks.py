"""Progress Celery tasks — spaced repetition scheduling."""

import datetime
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="progress.process_spaced_repetition")
def process_spaced_repetition() -> int:
    """Daily task: find SpacedRepetitionItems due for review and log them.

    Queries all SpacedRepetitionItem records where next_review_date <= today,
    groups them by student, and logs the count of items processed.

    Returns the number of students with due reviews.
    """
    from django.db.models import Count

    from apps.progress.models import SpacedRepetitionItem

    today = datetime.date.today()

    # Find all items due for review
    due_items = SpacedRepetitionItem.objects.filter(next_review_date__lte=today)

    # Group by student and count
    student_counts = (
        due_items.values("student_id")
        .annotate(item_count=Count("id"))
        .order_by("student_id")
    )

    total_items = 0
    students_with_reviews = 0

    for entry in student_counts:
        students_with_reviews += 1
        total_items += entry["item_count"]

    logger.info(
        "Spaced repetition: %d items due for %d students",
        total_items,
        students_with_reviews,
    )

    return students_with_reviews
