from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import Payment
from notifications.tasks import send_success_payment_notification


@receiver(post_save, sender=Payment)
def notify_success_payment(sender, instance, created, **kwargs):
    if created and instance.status == Payment.Status.PAID:
        borrowing = instance.borrowing
        user = borrowing.user
        book = borrowing.book
        message = (
            f"Successful payment!\n\n"
            f"User: {user.email}\n"
            f"Book: {book.title}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Amount paid: {instance.money_to_pay}"
        )
        send_success_payment_notification.delay(message)
