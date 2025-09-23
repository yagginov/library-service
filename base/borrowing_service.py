from django.db import transaction
from django.db.models import F

from base import exceptions
from base.dto import PaymentData, ProductData
from books.models import Book
from borrowings.models import Borrowing
from payments.services.payment import PaymentProcessor


class BorrowingService:
    def create_borrowing(self, payment_data: PaymentData, **kwargs):
        with transaction.atomic():
            borrowing = Borrowing.objects.create(**kwargs)
            book = borrowing.book

            payment_data.product_data = ProductData(
                name=book.title,
                description=f"author: {book.author}",
            )
            payment_data.price = book.daily_fee
            payment = PaymentProcessor.create_payment_by_borrowing(borrowing, payment_data)

            updated = Book.objects.filter(pk=book.pk, inventory__gte=1).update(
                inventory=F("inventory") - 1,
            )
            if updated == 0:
                raise exceptions.BookNotAvailableError()
        return borrowing

borrowing_service = BorrowingService()
