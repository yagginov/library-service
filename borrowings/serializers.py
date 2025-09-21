from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from books.models import Book

from .models import Borrowing


class BorrowingCreateSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
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

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.is_anonymous:
            raise serializers.ValidationError("Authentication required.")

        book = validated_data["book"]

        with transaction.atomic():
            updated = Book.objects.filter(
                pk=book.pk,
                inventory__gte=1
            ).update(inventory=F("inventory") - 1)

            if updated == 0:
                raise serializers.ValidationError("Book is not available.")

            borrowing = Borrowing.objects.create(user=user, **validated_data)

        return borrowing
