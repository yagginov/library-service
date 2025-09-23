from decimal import Decimal
from typing import Optional

from django.conf import settings

from base.dto import PaymentData, PaymentType, ProductData
from borrowings.models import Borrowing
from payments.models import Payment
from payments.services.payment import PaymentProcessor

fine_multiplier = settings.FINE_MULTIPLIER


class FineService:
    def create_fine_payment_if_overdue(
            self,
            borrowing: Borrowing
    ) -> Optional[Payment]:
        if not self._is_overdue(borrowing):
            return None

        days_overdue = self._calculate_overdue_days(borrowing)
        payment_data = self._prepare_fine_payment_data(borrowing, days_overdue)

        return PaymentProcessor.create_payment_by_borrowing(borrowing, payment_data)

    @staticmethod
    def _is_overdue(borrowing: Borrowing) -> bool:
        return (
            borrowing.actual_return_date is not None and
            borrowing.actual_return_date > borrowing.expected_return_date
        )

    @staticmethod
    def _calculate_overdue_days(borrowing: Borrowing) -> int:
        return abs((borrowing.actual_return_date - borrowing.expected_return_date).days)

    @staticmethod
    def _prepare_fine_payment_data(
            borrowing: Borrowing,
            days_overdue: int
    ) -> PaymentData:
        overdue_days = FineService._calculate_overdue_days(borrowing)
        price = borrowing.book.daily_fee

        return PaymentData(
            type=PaymentType.FINE,
            price=price,
            rent_days=overdue_days,
            fine_multiplier=fine_multiplier,
            product_data=ProductData(
                name=f"Fine for overdue: {borrowing.book.title}",
                description=f"Book overdue for {days_overdue} days. "
                            f"Daily fee: ${borrowing.book.daily_fee}, "
                            f"Fine multiplier: {fine_multiplier}"
            )
        )

fine_service = FineService()
