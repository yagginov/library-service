from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from borrowings.models import Borrowing
from notifications.tasks import (
    send_overdue_borrowings_messages,
    send_new_borrowing_notification,
    send_success_payment_notification,
)
from notifications.services import NotificationTelegramService
from telegram import Bot

User = get_user_model()

class TestNotificationService(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(email="admin@books.com", password="p", is_staff=True)
        cls.user = User.objects.create_user(email="user@books.com", password="p")
        cls.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverChoices.SOFT,
            inventory=5,
            daily_fee=1.5,
        )

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_message(self, mock_send):
        service = NotificationTelegramService()
        service.send("Test message")
        mock_send.assert_called_once_with("Test message")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_overdue_borrowing_notification(self, mock_send):
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with(f"Book: {borrowing.book.title} borrowed {borrowing.borrow_date} is overdue")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_new_borrowing_notification(self, mock_send):
        send_new_borrowing_notification("New borrowing created!")
        mock_send.assert_called_once_with("New borrowing created!")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_success_payment_notification(self, mock_send):
        send_success_payment_notification("Payment successful!")
        mock_send.assert_called_once_with("Payment successful!")

class TestNotificationTasks(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="user@books.com", password="p")
        cls.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverChoices.SOFT,
            inventory=5,
            daily_fee=1.5,
        )

    @patch("notifications.tasks.notification.send")
    def test_send_overdue_borrowings_messages_with_overdue(self, mock_send):
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with(f"Book: {borrowing.book.title} borrowed {borrowing.borrow_date} is overdue")

    @patch("notifications.tasks.notification.send")
    def test_send_overdue_borrowings_messages_without_overdue(self, mock_send):
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=3),
        )
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with("No borrowings overdue today!")

    @patch("notifications.tasks.notification.send")
    def test_send_success_payment_notification(self, mock_send):
        send_success_payment_notification("Payment successful!")
        mock_send.assert_called_once_with("Payment successful!")

    @patch("notifications.tasks.notification.send")
    def test_send_new_borrowing_notification(self, mock_send):
        send_new_borrowing_notification("New borrowing created!")
        mock_send.assert_called_once_with("New borrowing created!")

    @patch("notifications.tasks.notification.send")
    def test_send_multiple_overdue_borrowings(self, mock_send):
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today() - timedelta(days=15),
            expected_return_date=date.today() - timedelta(days=10),
        )
        send_overdue_borrowings_messages()
        self.assertEqual(mock_send.call_count, 2)

    @patch("notifications.tasks.notification.send")
    def test_send_new_borrowing_notification_with_dynamic_message(self, mock_send):
        message = f"New borrowing created for {self.book.title}"
        send_new_borrowing_notification(message)
        mock_send.assert_called_once_with(message)

    @patch("notifications.tasks.notification.send")
    def test_send_success_payment_notification_with_dynamic_message(self, mock_send):
        message = "Payment successful for your borrowing."
        send_success_payment_notification(message)
        mock_send.assert_called_once_with(message)

    @patch("notifications.tasks.notification.send")
    def test_no_overdue_borrowing_notifications(self, mock_send):
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with("No borrowings overdue today!")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_notification_for_multiple_users(self, mock_send):
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )
        admin_user = User.objects.create_user(email="admin@books.com", password="p", is_staff=True)
        Borrowing.objects.create(
            book=self.book,
            user=admin_user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )
        send_overdue_borrowings_messages()
        self.assertEqual(mock_send.call_count, 2)

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_notification_without_overdue_borrowings(self, mock_send):
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=3),
        )
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with("No borrowings overdue today!")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_notification_for_no_borrowings(self, mock_send):
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with("No borrowings overdue today!")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_new_borrowing_notification_empty_message(self, mock_send):
        send_new_borrowing_notification("")
        mock_send.assert_called_once_with("")

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_success_payment_notification_empty_message(self, mock_send):
        send_success_payment_notification("")
        mock_send.assert_called_once_with("")

    @patch("notifications.tasks.notification.send")
    def test_send_multiple_notifications(self, mock_send):
        for _ in range(10):
            send_success_payment_notification("Payment successful!")
        self.assertEqual(mock_send.call_count, 10)

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_multiple_overdue_borrowings(self, mock_send):
        for i in range(5):
            Borrowing.objects.create(
                book=self.book,
                user=self.user,
                borrow_date=date.today() - timedelta(days=10),
                expected_return_date=date.today() - timedelta(days=5),
            )
        send_overdue_borrowings_messages()
        self.assertEqual(mock_send.call_count, 5)

    @patch("notifications.services.NotificationTelegramService.send")
    def test_send_notification_for_admin(self, mock_send):
        admin = User.objects.create_user(email="admin@books.com", password="p", is_staff=True)
        Borrowing.objects.create(
            book=self.book,
            user=admin,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=5),
        )
        send_overdue_borrowings_messages()
        mock_send.assert_called_once_with(f"Book: {self.book.title} borrowed {date.today() - timedelta(days=10)} is overdue")
