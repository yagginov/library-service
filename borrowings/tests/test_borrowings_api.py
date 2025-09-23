from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer
from payments.models import Payment

User = get_user_model()


class BorrowingModelTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="p"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(title="API Book", inventory=10, daily_fee=5.0)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

    def test_mark_returned(self):
        self.borrowing.mark_returned()
        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)

        prev_inventory = self.book.inventory
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, prev_inventory + 1)

    def test_mark_returned_raises_if_already_returned(self):
        self.borrowing.mark_returned()
        with self.assertRaises(ValueError):
            self.borrowing.mark_returned()


class BorrowingSerializerTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@test.com",
            password="p"
        )
        cls.book = Book.objects.create(title="book", inventory=10, daily_fee=Decimal("1.20"))

    def setUp(self):
        self.client.force_authenticate(self.user)

    def make_serializer(self, data):
        serializer = BorrowingCreateSerializer(data=data, context={"request": self.client})
        serializer.context["request"].user = self.user
        return serializer

    def test_borrowing_create_serializer_success(self):
        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }
        serializer = self.make_serializer(data)

        self.assertTrue(serializer.is_valid())
        borrowing = serializer.save()
        self.assertEqual(borrowing.user, self.user)

        prev_inventory = self.book.inventory
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, prev_inventory - 1)

    def test_borrowing_create_serializer_inventory_zero(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }
        serializer = self.make_serializer(data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("Book is not available.", str(serializer.errors))

    def test_borrowing_create_with_wrong_date(self):
        data = {
            "book": self.book,
            "expected_return_date": date.today() - timedelta(days=4)
        }
        serializer = self.make_serializer(data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("expected_return_date", serializer.errors)


class BorrowingAPITest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="user@test.com", password="p")
        cls.admin = User.objects.create_superuser(email="admin@test.com", password="p")
        cls.book = Book.objects.create(
            title="API Book",
            inventory=10,
            daily_fee=Decimal("1.20"),
        )
        cls.borrowings = [
                Borrowing.objects.create(
                user=cls.admin,
                book=cls.book,
                expected_return_date=date.today() + timedelta(days=7),
            ) for _ in range(2)
        ] + [
            Borrowing.objects.create(
                user=cls.user,
                book=cls.book,
                expected_return_date=date.today() + timedelta(days=7),
            ) for _ in range(4)
        ]
        cls.list_url = reverse("borrowings:borrowings-list")

    def get_retrieve_url(self, id):
        return reverse("borrowings:borrowings-detail", args=[id])

    def test_list_view_with_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_view_with_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_retrieve_view_user_own_borrowing(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.get_retrieve_url(self.borrowings[4].id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("API Book", str(response.data))

    def test_retrieve_view_user_someone_else_borrowing(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.get_retrieve_url(self.borrowings[0].id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_view_admin_own_borrowing(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.get_retrieve_url(self.borrowings[0].id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_view_admin_someone_else_borrowing(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.get_retrieve_url(self.borrowings[4].id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_borrowing_api(self):
        self.client.force_authenticate(self.admin)
        new_book = Book.objects.create(title="New Book", inventory=1, daily_fee=4.0)
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 0)

    def test_create_borrowing_api_via_user(self):
        self.client.force_authenticate(self.user)
        new_book = Book.objects.create(title="New Book", inventory=1, daily_fee=4.0)
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 0)

    def test_create_borrowing_with_if_book_count_is_zero(self):
        self.client.force_authenticate(self.admin)
        new_book = Book.objects.create(title="New Book", inventory=0, daily_fee=4.0)
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_book_success(self):
        self.client.force_authenticate(self.admin)
        new_book = Book.objects.create(title="New Book", inventory=1, daily_fee=4.0)
        borrowing = Borrowing.objects.create(
            book=new_book,
            expected_return_date=str(date.today() + timedelta(days=7)),
            user=self.admin,
        )
        response = self.client.post(reverse("borrowings:borrowings-return-book", args=[borrowing.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        borrowing.refresh_from_db()
        self.assertIsNotNone(borrowing.actual_return_date)

        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 2)

    def test_return_book_that_already_returned(self):
        self.client.force_authenticate(self.admin)
        new_book = Book.objects.create(title="New Book", inventory=1, daily_fee=4.0)
        borrowing = Borrowing.objects.create(
            book=new_book,
            expected_return_date=str(date.today() + timedelta(days=7)),
            user=self.admin,
        )
        borrowing.mark_returned()
        response = self.client.post(reverse("borrowings:borrowings-return-book", args=[borrowing.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already returned", response.data["detail"])

    def test_create_borrowing_with_pending_payment(self):
        self.client.force_authenticate(self.user)
        existing_borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        Payment.objects.create(
            borrowing=existing_borrowing,
            session_url="http://example.com",
            session_id="test_session_id",
            money_to_pay=Decimal("10.00"),
            status=Payment.Status.PENDING,
        )

        new_book = Book.objects.create(
            title="New Book API",
            inventory=3,
            daily_fee=Decimal("3.00"),
        )
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You cannot borrow new books while you have pending payments.",
                      str(response.data))
        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 3)

    def test_create_borrowing_api_with_paid_payment(self):
        self.client.force_authenticate(self.user)

        existing_borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        Payment.objects.create(
            borrowing=existing_borrowing,
            session_url="http://example.com",
            session_id="test_session_id",
            money_to_pay=Decimal("10.00"),
            status=Payment.Status.PAID,
        )

        new_book = Book.objects.create(
            title="New Book API",
            inventory=3,
            daily_fee=Decimal("3.00"),
        )
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_book.refresh_from_db()
        self.assertEqual(new_book.inventory, 2)

    def test_borrowing_create_serializer_multiple_pending_payments(self):
        test_user = User.objects.create_user(
            email="test_multiple@test.com",
            password="p",
        )

        for i in range(3):
            book = Book.objects.create(
                title=f"Book {i}",
                inventory=5,
                daily_fee=Decimal("1.00"),
            )
            borrowing = Borrowing.objects.create(
                user=test_user,
                book=book,
                expected_return_date=date.today() + timedelta(days=7),
            )
            Payment.objects.create(
                borrowing=borrowing,
                session_url=f"http://example{i}.com",
                session_id=f"test_session_id_{i}",
                money_to_pay=Decimal(f"{i + 1}.00"),
                status=Payment.Status.PENDING,
            )

        new_book = Book.objects.create(
            title="New Book",
            inventory=5,
            daily_fee=Decimal("2.00"),
        )
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }

        serializer = BorrowingCreateSerializer(
            data=data,
            context={"request": self.client},
        )
        serializer.context["request"].user = test_user

        self.assertFalse(serializer.is_valid())
        self.assertIn("You cannot borrow new books while you have pending payments.",
                      str(serializer.errors))

    def test_borrowing_create_serializer_no_payments(self):
        clean_user = User.objects.create_user(
            email="clean_user@test.com",
            password="p",
        )

        new_book = Book.objects.create(
            title="New Book",
            inventory=5,
            daily_fee=Decimal("2.00"),
        )
        data = {
            "book": new_book.id,
            "expected_return_date": date.today() + timedelta(days=5),
        }

        serializer = BorrowingCreateSerializer(
            data=data,
            context={"request": self.client},
        )
        serializer.context["request"].user = clean_user

        self.assertTrue(serializer.is_valid())
        borrowing = serializer.save()
        self.assertEqual(borrowing.user, clean_user)
