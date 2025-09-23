from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
from notifications.tasks import send_new_borrowing_notification


@receiver(post_save, sender=Borrowing)
def notify_new_borrowing(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        book = instance.book
        message = (
            f"New borrowing created!\n\n"
            f"User: {user.email}\n"
            f"Book: {book.title}\n"
            f"Borrow date: {instance.borrow_date}\n"
            f"Expected return: {instance.expected_return_date}"
        )
        send_new_borrowing_notification.delay(message)
