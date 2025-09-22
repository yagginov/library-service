from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer, BorrowingDetailSerializer

User = get_user_model()


class BorrowingModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="pass123")
        self.book = Book.objects.create(title="Book1", author="Author1", inventory=1, daily_fee=1.5, cover="HARD")
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timedelta(days=1),
        )

    def test_str_method(self):
        self.assertIn(str(self.borrowing.user_id), str(self.borrowing))
        self.assertIn(str(self.borrowing.book_id), str(self.borrowing))

    def test_mark_returned_sets_actual_date_and_increments_inventory(self):
        original_inventory = self.book.inventory
        self.borrowing.mark_returned()
        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, original_inventory + 1)

    def test_mark_returned_raises_error_if_already_returned(self):
        self.borrowing.mark_returned()
        with self.assertRaises(ValueError):
            self.borrowing.mark_returned()


class BorrowingSerializerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="pass123")
        self.book = Book.objects.create(title="Book1", author="Author1", inventory=1, daily_fee=1.5, cover="HARD")

    def test_create_serializer_decreases_inventory(self):
        data = {
            "book": self.book.id,
            "expected_return_date": (timezone.now().date() + timedelta(days=1)).isoformat()
        }
        serializer = BorrowingCreateSerializer(data=data, context={"request": type("req", (), {"user": self.user})()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        borrowing = serializer.save()
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 0)
        self.assertEqual(borrowing.user, self.user)

    def test_create_serializer_fails_if_inventory_zero(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "expected_return_date": (timezone.now().date() + timedelta(days=1)).isoformat()
        }
        serializer = BorrowingCreateSerializer(data=data, context={"request": type("req", (), {"user": self.user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("book", serializer.errors)


class BorrowingAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="pass123")
        self.user2 = User.objects.create_user(email="other@test.com", password="pass123")
        self.book = Book.objects.create(title="Book1", author="Author1", inventory=2, daily_fee=1.5, cover="HARD")
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timedelta(days=1),
        )
        self.client.login(email="user@test.com", password="pass123")

    def test_list_borrowings_authenticated_user_only(self):
        Borrowing.objects.create(
            user=self.user2,
            book=self.book,
            expected_return_date=timezone.now().date() + timedelta(days=1),
        )
        url = reverse("borrowings:borrowings-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"], self.user.email)

    def test_retrieve_borrowing_detail(self):
        url = reverse("borrowings:borrowings-detail", args=[self.borrowing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.borrowing.id)
        self.assertIn("book", response.data)

    def test_create_borrowing_endpoint(self):
        new_book = Book.objects.create(title="Book2", author="Author2", inventory=1, daily_fee=2.0, cover="SOFT")
        url = reverse("borrowings:borrowings-list")
        data = {
            "book": new_book.id,
            "expected_return_date": (timezone.now().date() + timedelta(days=2)).isoformat()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 0)

    def test_return_book_endpoint(self):
        url = reverse("borrowings:borrowings-return-book", args=[self.borrowing.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, 2)

    def test_return_book_endpoint_fails_if_already_returned(self):
        self.borrowing.mark_returned()
        url = reverse("borrowings:borrowings-return-book", args=[self.borrowing.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_permissions_unauthenticated(self):
        self.client.logout()
        url = reverse("borrowings:borrowings-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_is_active(self):
        # active borrowing
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timedelta(days=1),
        )
        url = reverse("borrowings:borrowings-list") + "?is_active=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for b in response.data:
            self.assertIsNone(b["actual_return_date"])
        self.borrowing.mark_returned()
        url = reverse("borrowings:borrowings-list") + "?is_active=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for b in response.data:
            self.assertIsNotNone(b["actual_return_date"])
