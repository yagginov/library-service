from django.contrib import admin

from borrowings.models import Borrowing
from payments.models import Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("status", "type", "money_to_pay", "session_url")


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "book",
        "borrow_date",
        "expected_return_date",
        "actual_return_date",
    )
    list_filter = ("user", "book", "borrow_date")
    search_fields = ("user__username", "book__title")
    readonly_fields = ("borrow_date",)
    inlines = [PaymentInline]
