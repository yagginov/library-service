from datetime import date

from celery import shared_task

import notifications.services
from borrowings.models import Borrowing


@shared_task
def send_overdue_borrowings_messages():
    today = date.today()
    notification = notifications.services.notification
    overdue_borrowings = Borrowing.objects.filter(
        actual_return_date__isnull=True,
        expected_return_date__lte=today
    )

    if overdue_borrowings:
        for borrowing in overdue_borrowings:
            notification.send(f"Book: {borrowing.book.title} borrowed {borrowing.borrow_date} is overdue")
    else:
        notification.send("No borrowings overdue today!")

@shared_task
def send_new_borrowing_notification(message: str):
    notification = notifications.services.notification
    notification.send(message)

@shared_task
def send_success_payment_notification(message: str):
    notification = notifications.services.notification
    notification.send(message)
