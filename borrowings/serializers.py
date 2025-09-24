from datetime import date

from rest_framework import serializers

from base import exceptions
from base.borrowing_service import borrowing_service
from base.dto import PaymentData
from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentSerializer


class BorrowingCreateSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.only("id", "inventory")
    )
    borrow_date = serializers.DateField(read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        ]
        read_only_fields = ["id", "borrow_date", "actual_return_date"]

    def validate(self, attrs):
        user = self.context["request"].user

        pending_payments = Payment.objects.filter(
            borrowing__user=user,
            status=Payment.Status.PENDING,
        ).exists()

        if pending_payments:
            raise serializers.ValidationError(
                "You cannot borrow new books while you have pending payments."
            )
        return attrs

    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError("Book is not available.")
        return value

    def validate_expected_return_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                "Expected return date cannot be in the past."
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user

        try:
            borrowing = borrowing_service.create_borrowing(payment_data=PaymentData(), user=user, **validated_data)
        except exceptions.PaymentSessionCreationError as e:
            raise serializers.ValidationError(e)
        except exceptions.BookNotAvailableError as e:
            raise serializers.ValidationError(e)
        except exceptions.BorrowingError as e:
            raise serializers.ValidationError(e)
        except Exception:
            raise serializers.ValidationError("Something went wrong.")

        return borrowing


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "payments",
        ]
        read_only_fields = fields


class RenewPaymentResponseSerializer(serializers.Serializer):
    payment = serializers.CharField(required=False)
    fine = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
