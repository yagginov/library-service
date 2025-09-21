from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )

    class Meta:
        ordering = ["-borrow_date"]

    def __str__(self):
        return (f"{self.user_id} borrowed "
                f"{self.book_id} on {self.borrow_date}")

    def mark_returned(self):
        if self.actual_return_date is not None:
            raise ValueError("Borrowing already returned.")

        with transaction.atomic():
            self.actual_return_date = timezone.now().date()
            self.save()

            Book.objects.filter(
                pk=self.book_id
            ).update(inventory=F("inventory") + 1)
