from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base import exceptions
from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

User = get_user_model()

class TestPaymentViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(email="admin@books.com", password="p", is_staff=True)
        cls.user = User.objects.create_user(email="user@books.com", password="p")
        cls.book = Book.objects.create(
            title="t",
            author="a",
            cover=Book.CoverChoices.SOFT,
            inventory=100,
            daily_fee=Decimal("1.10"),
        )
        cls.borrowings = [
            Borrowing.objects.create(
                expected_return_date=date.today() + timedelta(days=3),
                book=cls.book,
                user=cls.admin,
            ) for _ in range(2)
        ] + [
            Borrowing.objects.create(
                expected_return_date=date.today() + timedelta(days=3),
                book=cls.book,
                user=cls.user,
            ) for _ in range(4)
        ]
        cls.payments = [
            Payment.objects.create(
                borrowing=cls.borrowings[i],
                session_url="http://example.com",
                session_id="id",
                money_to_pay=Decimal("12.10"),
            ) for i in range(len(cls.borrowings))
        ]
        cls.list_url = reverse("payments:payment-list")

    @staticmethod
    def get_retrieve_url(id: int) -> str:
        return reverse("payments:payment-detail", args=[id])

    def test_list_view_with_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.payments))

    def test_list_view_with_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Payment.objects.filter(borrowing__user=self.user).count())

    def test_retrieve_view_admin_own_payment(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.get_retrieve_url(self.payments[0].id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_view_admin_someone_else_payment(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.get_retrieve_url(self.payments[3].id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_view_user_own_payment(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.get_retrieve_url(self.payments[3].id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_view_user_someone_else_payment(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.get_retrieve_url(self.payments[0].id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_view_anonymus(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_view_anonymus(self):
        self.client.logout()
        response = self.client.get(self.get_retrieve_url(self.payments[0]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPaymentAutomations(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="user@books.com", password="p")

    def setUp(self):
        self.client.force_authenticate(self.user)

    @patch("payments.services.payment.payment_service")
    def test_payment_automatic_creation(self, mock_payment_service):
        session = MagicMock()
        session.url = "http://payments-url/"
        session.id = "session_id"
        mock_payment_service.create_payment_session.return_value = session
        book = Book.objects.create(
            title="test",
            author="author",
            cover=Book.CoverChoices.SOFT,
            inventory=100,
            daily_fee=Decimal("1.10"),
        )
        prev_book_inventory = book.inventory

        borrowing_data = {
            "expected_return_date": date.today() + timedelta(days=3),
            "book": book.id,
        }
        borrowing_create_url = reverse("borrowings:borrowings-list")
        response = self.client.post(borrowing_create_url, data=borrowing_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        book.refresh_from_db()
        self.assertEqual(book.inventory, prev_book_inventory - 1)
        self.assertEqual(book.borrowings.all().count(), 1)
        borrowing = book.borrowings.first()
        self.assertEqual(borrowing.payments.all().count(), 1)
        payment = borrowing.payments.first()
        self.assertEqual(payment.session_id, session.id)
        self.assertEqual(payment.session_url, session.url)


class TestPaymentCustomActions(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="user@books.com", password="p")

    def setUp(self):
        self.book = Book.objects.create(
            title="t",
            author="a",
            cover=Book.CoverChoices.SOFT,
            inventory=100,
            daily_fee=Decimal("1.10"),
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=4),
            book=self.book,
            user=self.user,
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="http://example.com",
            session_id="session_id",
            money_to_pay=Decimal("12.10"),
        )
        self.client.force_authenticate(self.user)

    @patch("payments.services.payment.payment_service")
    def test_payment_success_with_stripe_session_paid(self, mock_payment_service):
        mock_payment_service.is_paid.return_value = True

        url = reverse("payments:payment-success") + f"?session_id={self.payment.session_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Payment successful!", str(response.data))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)

    @patch("payments.services.payment.payment_service")
    def test_payment_success_with_stripe_session_unpaid(self, mock_payment_service):
        mock_payment_service.is_paid.return_value = False

        url = reverse("payments:payment-success") + f"?session_id={self.payment.session_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Payment not successful!", str(response.data))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)

    def test_payment_success_with_wrong_status(self):
        self.payment.status = Payment.Status.CANCELED
        self.payment.save()

        url = reverse("payments:payment-success") + f"?session_id={self.payment.session_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This payment was already canceled.", str(response.data))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.CANCELED)

    def test_payment_success_with_wrong_session_id_provided(self):
        url = reverse("payments:payment-success") + "?session_id=not_actual_session_id"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_success_without_session_id(self):
        url = reverse("payments:payment-success")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No session_id provided", str(response.data))

    def test_payment_cancel_success_with_pending_payment(self):
        url = reverse("payments:payment-cancel") + f"?session_id={self.payment.session_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("You can return to payment later.", str(response.data))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)

    def test_payment_cancel_with_wrong_status(self):
        self.payment.status = Payment.Status.CANCELED
        self.payment.save()

        url = reverse("payments:payment-cancel") + f"?session_id={self.payment.session_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This payment was already canceled.", str(response.data))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.CANCELED)

    def test_payment_cancel_with_wrong_session_id_provided(self):
        url = reverse("payments:payment-cancel") + "?session_id=not_actual_session_id"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_cancel_without_session_id(self):
        url = reverse("payments:payment-cancel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No session_id provided", str(response.data))
