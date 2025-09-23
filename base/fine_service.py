from decimal import Decimal
from typing import Optional

from django.conf import settings

from base.dto import PaymentData, ProductData, PaymentType
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
        return (borrowing.actual_return_date - borrowing.expected_return_date).days

    @staticmethod
    def _prepare_fine_payment_data(
            borrowing: Borrowing,
            days_overdue: int
    ) -> PaymentData:
        total_fine_amount = days_overdue * borrowing.book.daily_fee * Decimal(
            str(fine_multiplier)
        )
        rent_days = (borrowing.expected_return_date - borrowing.borrow_date).days
        adjusted_price = total_fine_amount / rent_days if rent_days > 0 else total_fine_amount

        return PaymentData(
            type=PaymentType.FINE,
            price=adjusted_price,
            product_data=ProductData(
                name=f"Fine for overdue: {borrowing.book.title}",
                description=f"Book overdue for {days_overdue} days. "
                            f"Daily fee: ${borrowing.book.daily_fee}, "
                            f"Fine multiplier: {fine_multiplier}"
            )
        )

fine_service = FineService()
