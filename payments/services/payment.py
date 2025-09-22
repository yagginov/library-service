from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import F

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

from base.payment_services import payment_service


class PaymentProcessor:
    @staticmethod
    def mark_success(session_id: str) -> dict:
        payment = get_object_or_404(Payment, session_id=session_id)

        if payment.status != Payment.Status.PENDING:
            return {"error": f"This payment was already {payment.status.lower()}."}

        if payment_service.is_paid(session_id):
            payment.status = Payment.Status.PAID
            payment.save()
            return {"message": "Payment successful!"}

        return {"message": "Payment not successful!"}

    @staticmethod
    def mark_cancelled(session_id: str) -> dict:
        payment = get_object_or_404(Payment, session_id=session_id)

        if payment.status != Payment.Status.PENDING:
            return {"error": f"This payment was already {payment.status.lower()}."}

        with transaction.atomic():
            payment.status = Payment.Status.CANCELLED
            payment.save()

            Borrowing.objects.filter(id=payment.borrowing_id).update(
                actual_return_date=timezone.now()
            )

            payment_service.mark_session_as_expired(session_id)

            Book.objects.filter(id=payment.borrowing.book_id).update(
                inventory=F("inventory") + 1
            )

        return {"message": "Payment was cancelled."}
