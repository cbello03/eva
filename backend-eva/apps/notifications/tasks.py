"""Notification Celery tasks — email delivery with retry policy."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="notifications.send_email_notification",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    retry_backoff_max=300,
)
def send_email_notification(notification_id: int) -> None:
    """Send an email for a notification. Retries up to 3 times with exponential backoff."""
    from django.core.mail import send_mail

    from apps.notifications.models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(
            pk=notification_id
        )
    except Notification.DoesNotExist:
        logger.error("Notification %s not found; skipping email", notification_id)
        return

    if notification.email_sent:
        logger.info("Email already sent for notification %s", notification_id)
        return

    recipient = notification.recipient
    send_mail(
        subject=notification.title,
        message=notification.body,
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[recipient.email],
        fail_silently=False,
    )

    notification.email_sent = True
    notification.save(update_fields=["email_sent", "updated_at"])
    logger.info("Email sent for notification %s to %s", notification_id, recipient.email)
