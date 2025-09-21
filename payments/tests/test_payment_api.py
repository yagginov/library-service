from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

User = get_user_model()

class TestPaymentViewSet(APITestCase):
    @classmethod
    def setUpTestData(self):
        self.admin = User.objects.create_user(email="admin@books.com", password="p", is_staff=True)
        self.user = User.objects.create_user(email="user@books.com", password="p")
        self.book = Book.objects.create(
            title="t",
            author="a",
            cover=Book.CoverChoices.SOFT,
            inventory=100,
            daily_fee=Decimal("1.10"),
        )
        self.borrowings = [
            Borrowing.objects.create(
                expected_return_date=date.today() + timedelta(days=3),
                book=self.book,
                user=self.admin,
            ) for _ in range(2)
        ] + [
            Borrowing.objects.create(
                expected_return_date=date.today() + timedelta(days=3),
                book=self.book,
                user=self.user,
            ) for _ in range(4)
        ]
        self.payments = [
            Payment.objects.create(
                borrowing=self.borrowings[i],
                session_url="http://example.com",
                session_id="id",
                money_to_pay=Decimal("12.10"),
            ) for i in range(len(self.borrowings))
        ]
        self.list_url = reverse("payments:payment-list")

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
