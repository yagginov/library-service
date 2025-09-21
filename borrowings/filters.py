from django_filters import rest_framework as filters

from borrowings.models import Borrowing


class BorrowingFilter(filters.FilterSet):
    is_active = filters.BooleanFilter(method="filter_is_active", label="is_active")

    class Meta:
        model = Borrowing
        fields = ["user_id", "is_active"]

    def filter_is_active(self, queryset, name, value):
        if value:
            return queryset.filter(actual_return_date__isnull=True)
        return queryset.filter(actual_return_date__isnull=False)
