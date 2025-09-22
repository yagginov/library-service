from django.db import transaction
from django.db.models import F

from base import exceptions
from base.dto import PaymentData, PaymentSessionData, ProductData
from base.payment_services import payment_service
from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


class BorrowingService:
    def create_borrowing(
        self,
        borrowing: Borrowing,
        book: Book,
        data: PaymentData,
    ):
        with transaction.atomic():
            borrowing.save()
            # calculate total amount
            rent_day = (borrowing.expected_return_date - borrowing.borrow_date).days
            book_price = book.daily_fee
            total_amount = rent_day * book_price * data.fine_multiplier

            # data generation for transmission to the service
            product_data = ProductData(
                name=book.title,
                description=f"author: {book.author}",
            )
            payment_data = PaymentSessionData(
                product_data=product_data,
                unit_amount=total_amount,
                quantity=1,
            )

            # create session
            session = payment_service.create_payment_session(payment_data)

            if not session:
                raise exceptions.PaymentSessionCreationError()

            Payment.objects.create(
                status=data.status,
                type=data.type,
                borrowing=borrowing,
                money_to_pay=total_amount,
                session_id=session.id,
                session_url=session.url,
            )

            updated = Book.objects.filter(pk=book.pk, inventory__gte=1).update(
                inventory=F("inventory") - 1,
            )
            if updated == 0:
                raise exceptions.BookNotAvailableError()
        return borrowing

borrowing_service = BorrowingService()
