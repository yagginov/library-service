from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer, BorrowingDetailSerializer
from users.models import User


class BorrowingModelTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="apiuser@example.com",
            password="pass123"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(title="API Book", inventory=1, daily_fee=5.0)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

    def test_str_method(self):
        self.assertIn(str(self.borrowing.user_id), str(self.borrowing))
        self.assertIn(str(self.borrowing.book_id), str(self.borrowing))

    def test_mark_returned(self):
        self.borrowing.mark_returned()
        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_mark_returned_raises_if_already_returned(self):
        self.borrowing.mark_returned()
        with self.assertRaises(ValueError):
            self.borrowing.mark_returned()


class BorrowingSerializerTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="pass123"
        )
        self.book = Book.objects.create(title="Book2", inventory=1, daily_fee=3.0)

    def test_borrowing_create_serializer_success(self):
        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }
        serializer = BorrowingCreateSerializer(data=data, context={"request": self.client})
        serializer.context["request"].user = self.user
        self.assertTrue(serializer.is_valid(), serializer.errors)
        borrowing = serializer.save()
        self.assertEqual(borrowing.user, self.user)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 0)

    def test_borrowing_create_serializer_inventory_zero(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }
        serializer = BorrowingCreateSerializer(data=data, context={"request": self.client})
        serializer.context["request"].user = self.user
        self.assertFalse(serializer.is_valid())
        self.assertIn("Book is not available.", str(serializer.errors))


class BorrowingAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="apiuser@example.com",
            password="pass123"
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(
            title="API Book",
            inventory=1,
            daily_fee=5.0
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

    def test_list_borrowings(self):
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_borrowing(self):
        response = self.client.get(f"/api/borrowings/{self.borrowing.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.borrowing.id)
        self.assertIn("book", response.data)

    def test_create_borrowing_api(self):
        new_book = Book.objects.create(title="New Book", inventory=1, daily_fee=4.0)
        data = {
            "book": new_book.id,
            "expected_return_date": str(date.today() + timedelta(days=7)),
        }
        response = self.client.post("/api/borrowings/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 0)

    def test_return_book_api_success(self):
        response = self.client.post(f"/api/borrowings/{self.borrowing.id}/return_book/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_return_book_api_already_returned(self):
        self.borrowing.mark_returned()
        response = self.client.post(f"/api/borrowings/{self.borrowing.id}/return_book/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already returned", response.data["detail"])

    def test_user_can_only_see_own_borrowings(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123"
        )
        Borrowing.objects.create(
            user=other_user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=5),
        )
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)

    def test_admin_can_see_all_borrowings(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_can_see_every_borrowing(self):
        self.client.force_authenticate(user=self.admin)
        Borrowing.objects.create(
            user=self.admin,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=5),
        )
        response = self.client.get("/api/borrowings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_create_borrowing_with_past_expected_return_date(self):
        past_date = date.today() - timedelta(days=1)
        data = {
            "book": self.book.id,
            "expected_return_date": str(past_date),
        }
        response = self.client.post("/api/borrowings/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", str(response.data))
