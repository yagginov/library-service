from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.dto import PaymentType
from base.fine_service import FineService, fine_service
from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer
from payments.models import Payment

User = get_user_model()
patcher = None


def setUpModule():
    global patcher
    patcher = patch("borrowings.signals.send_new_borrowing_notification.delay")
    patcher.start()


def tearDownModule():
    patcher.stop()


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


class TestBorrowingCustomAction(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="password"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="password"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            inventory=5,
            daily_fee=Decimal("10.00")
        )

    def get_return_book_url(self, borrowing_id):
        return reverse("borrowings:borrowings-return-book", args=[borrowing_id])

    def test_fine_service_no_fine_for_not_overdue(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        result = fine_service.create_fine_payment_if_overdue(borrowing)
        self.assertIsNone(result)

    def test_fine_service_no_fine_for_on_time_return(self):
        expected_date = date.today() + timedelta(days=5)
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_date,
            actual_return_date=expected_date
        )

        result = fine_service.create_fine_payment_if_overdue(borrowing)
        self.assertIsNone(result)

    @patch('base.fine_service.PaymentProcessor.create_payment_by_borrowing')
    def test_fine_service_creates_fine_for_overdue(self, mock_payment_processor):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=date.today()
        )

        mock_payment = Mock(spec=Payment)
        mock_payment_processor.return_value = mock_payment

        result = fine_service.create_fine_payment_if_overdue(borrowing)

        self.assertEqual(result, mock_payment)
        mock_payment_processor.assert_called_once()

        args, kwargs = mock_payment_processor.call_args
        borrowing_arg, payment_data = args

        self.assertEqual(borrowing_arg, borrowing)
        self.assertEqual(payment_data.type, PaymentType.FINE)
        self.assertEqual(payment_data.price, self.book.daily_fee)
        self.assertEqual(payment_data.rent_days, 3)

    def test_fine_service_calculate_overdue_days(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=5),
            actual_return_date=date.today() - timedelta(days=1)
        )

        result = FineService._calculate_overdue_days(borrowing)
        self.assertEqual(result, 4)

    def test_fine_service_is_overdue_logic(self):
        # Not returned yet
        borrowing1 = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=5),
        )
        self.assertFalse(FineService._is_overdue(borrowing1))

        # Returned on time
        borrowing2 = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today(),
            actual_return_date=date.today() - timedelta(days=1),
        )
        self.assertFalse(FineService._is_overdue(borrowing2))

        # Overdue
        borrowing3 = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=2),
            actual_return_date=date.today(),
        )
        self.assertTrue(FineService._is_overdue(borrowing3))

    @patch('base.fine_service.fine_service.create_fine_payment_if_overdue')
    def test_return_book_success_with_fine(self, mock_fine_service):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=5),
        )

        mock_payment = Mock()
        mock_payment.id = 123
        mock_payment.money_to_pay = Decimal("25.00")
        mock_payment.session_url = "https://stripe.com/session/123"
        mock_payment.status = Payment.Status.PENDING
        mock_fine_service.return_value = mock_payment

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_return_book_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_fine_service.assert_called_once_with(borrowing)

        self.assertIn("fine_payment", response.data)
        fine_payment_data = response.data["fine_payment"]
        self.assertEqual(fine_payment_data["id"], 123)
        self.assertEqual(fine_payment_data["amount"], "25.00")
        self.assertEqual(fine_payment_data["session_url"], "https://stripe.com/session/123")
        self.assertEqual(fine_payment_data["status"], Payment.Status.PENDING)
        self.assertIn("Fine payment created", fine_payment_data["message"])

    def get_renew_payment_url(self, borrowing_id):
        return reverse("borrowings:borrowings-renew-payment", args=[borrowing_id])

    @patch("base.borrowing_service.borrowing_service.renew_payment_for_borrowing")
    def test_renew_payment_creates_new_payment_when_no_payment_exists(self, mock_borrowing_service):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        mock_payment = Mock()
        mock_payment.id = 456
        mock_borrowing_service.return_value = mock_payment

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_borrowing_service.assert_called_once_with(borrowing)

        self.assertEqual(len(response.data), 1)
        self.assertIn("payment", response.data[0])
        self.assertEqual(response.data[0]["payment"], "New payment created with id 456")

    def test_renew_payment_returns_message_when_pending_payment_exists(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PENDING,
            money_to_pay=Decimal("50.00"),
            session_url="https://stripe.com/session/pending",
            session_id="session_pending"
        )

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("payment", response.data[0])
        self.assertEqual(response.data[0]["payment"], "Active payment already exists")

    def test_renew_payment_nothing_to_pay_when_paid_payment_exists(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PAID,
            money_to_pay=Decimal("50.00"),
            session_url="https://stripe.com/session/paid",
            session_id="session_paid"
        )

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Nothing to pay")

    @patch("base.fine_service.fine_service.create_fine_payment_if_overdue")
    def test_renew_payment_creates_fine_for_returned_overdue_borrowing(self, mock_fine_service):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=date.today()
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PAID,
            money_to_pay=Decimal("50.00"),
            session_url="https://stripe.com/session/paid",
            session_id="session_paid"
        )

        mock_fine_payment = Mock()
        mock_fine_payment.id = 789
        mock_fine_service.return_value = mock_fine_payment

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_fine_service.assert_called_once_with(borrowing)
        
        self.assertEqual(len(response.data), 1)
        self.assertIn("fine", response.data[0])
        self.assertEqual(response.data[0]["fine"], "New fine created with id 789")

    @patch("base.fine_service.fine_service.create_fine_payment_if_overdue")
    def test_renew_payment_no_fine_for_returned_on_time_borrowing(self, mock_fine_service):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today(),
            actual_return_date=date.today() - timedelta(days=1)
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PAID,
            money_to_pay=Decimal("50.00"),
            session_url="https://stripe.com/session/paid",
            session_id="session_paid"
        )

        mock_fine_service.return_value = None

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_fine_service.assert_called_once_with(borrowing)
        
        self.assertEqual(len(response.data), 1)
        self.assertIn("fine", response.data[0])
        self.assertEqual(response.data[0]["fine"], "You are not overdue your borrowing")

    def test_renew_payment_returns_message_when_pending_fine_exists(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=date.today()
        )
        
        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PAID,
            money_to_pay=Decimal("50.00"),
            session_url="https://stripe.com/session/paid",
            session_id="session_paid"
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.FINE,
            status=Payment.Status.PENDING,
            money_to_pay=Decimal("30.00"),
            session_url="https://stripe.com/session/fine_pending",
            session_id="session_fine_pending"
        )

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("fine", response.data[0])
        self.assertEqual(response.data[0]["fine"], "Active fine payment already exists")

    def test_renew_payment_nothing_to_pay_when_fine_already_paid(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=date.today()
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PAID,
            money_to_pay=Decimal("50.00"),
            session_url="https://stripe.com/session/paid",
            session_id="session_paid"
        )

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.FINE,
            status=Payment.Status.PAID,
            money_to_pay=Decimal("30.00"),
            session_url="https://stripe.com/session/fine_paid",
            session_id="session_fine_paid"
        )

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Nothing to pay")

    @patch("base.borrowing_service.borrowing_service.renew_payment_for_borrowing")
    @patch("base.fine_service.fine_service.create_fine_payment_if_overdue")
    def test_renew_payment_creates_both_payment_and_fine(self, mock_fine_service, mock_borrowing_service):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=date.today()
        )

        mock_payment = Mock()
        mock_payment.id = 456
        mock_borrowing_service.return_value = mock_payment

        mock_fine_payment = Mock()
        mock_fine_payment.id = 789
        mock_fine_service.return_value = mock_fine_payment

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_borrowing_service.assert_called_once_with(borrowing)
        mock_fine_service.assert_called_once_with(borrowing)
        
        self.assertEqual(len(response.data), 2)

        payment_response = next(item for item in response.data if "payment" in item)
        self.assertEqual(payment_response["payment"], "New payment created with id 456")

        fine_response = next(item for item in response.data if "fine" in item)
        self.assertEqual(fine_response["fine"], "New fine created with id 789")

    def test_renew_payment_ignores_fine_logic_for_non_returned_book(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

        self.client.force_authenticate(self.user)
        
        with patch("base.borrowing_service.borrowing_service.renew_payment_for_borrowing") as mock_borrowing_service:
            mock_payment = Mock()
            mock_payment.id = 456
            mock_borrowing_service.return_value = mock_payment

            response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("payment", response.data[0])
        self.assertEqual(response.data[0]["payment"], "New payment created with id 456")

    def test_renew_payment_permission_denied_for_other_user(self):
        other_user = User.objects.create_user(
            email="other@test.com",
            password="password"
        )
        
        borrowing = Borrowing.objects.create(
            user=other_user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        self.client.force_authenticate(self.user)
        response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_renew_payment_admin_can_access_any_borrowing(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        self.client.force_authenticate(self.admin)
        
        with patch("base.borrowing_service.borrowing_service.renew_payment_for_borrowing") as mock_borrowing_service:
            mock_payment = Mock()
            mock_payment.id = 456
            mock_borrowing_service.return_value = mock_payment

            response = self.client.post(self.get_renew_payment_url(borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("payment", response.data[0])
        self.assertEqual(response.data[0]["payment"], "New payment created with id 456")

    def test_renew_payment_unauthenticated_user(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        response = self.client.post(self.get_renew_payment_url(borrowing.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
