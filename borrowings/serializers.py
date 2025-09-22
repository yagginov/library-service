from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from datetime import date

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing


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
        book = validated_data["book"]

        with transaction.atomic():
            updated = Book.objects.filter(pk=book.pk, inventory__gte=1).update(
                inventory=F("inventory") - 1
            )
            if updated == 0:
                raise serializers.ValidationError("Book is not available.")

            borrowing = Borrowing.objects.create(user=user, **validated_data)

        return borrowing


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        ]
        read_only_fields = fields
