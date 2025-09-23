from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from base import exceptions
from base.dto import PaymentData, PaymentSessionData
from base.payment_services import payment_service
from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


class PaymentProcessor:
    @staticmethod
    def mark_success(session_id: str, user) -> dict:
        payment = get_object_or_404(Payment, session_id=session_id, borrowing__user=user)

        if payment.status != Payment.Status.PENDING:
            return {"error": f"This payment was already {payment.status.lower()}."}

        if payment_service.is_paid(session_id):
            payment.status = Payment.Status.PAID
            payment.save()
            return {"message": "Payment successful!"}

        return {"error": "Payment not successful!"}

    @staticmethod
    def mark_canceled(session_id: str, user) -> dict:
        result = PaymentProcessor.check_if_session_valid(session_id)
        if "error" in result:
            return result
        payment = result.get("payment")

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

    @staticmethod
    def check_if_session_valid(session_id: str, user) -> dict:
        payment = get_object_or_404(Payment, session_id=session_id, borrowing__user=user)

        if payment.status != Payment.Status.PENDING:
            return {"error": f"This payment was already {payment.status.lower()}."}

        return {"payment": payment}

    @staticmethod
    def create_payment_by_borrowing(borrowing: Borrowing, payment_data: PaymentData):
        rent_day = (borrowing.expected_return_date - borrowing.borrow_date).days
        book_price = payment_data.price
        total_amount = rent_day * book_price * payment_data.fine_multiplier

        payment_session_data = PaymentSessionData(
            product_data=payment_data.product_data,
            unit_amount=total_amount,
            quantity=1,
        )

        session = payment_service.create_payment_session(payment_session_data)

        if not session:
            raise exceptions.PaymentSessionCreationError()

        return Payment.objects.create(
            status=payment_data.status,
            type=payment_data.type,
            borrowing=borrowing,
            money_to_pay=total_amount,
            session_id=session.id,
            session_url=session.url,
        )
