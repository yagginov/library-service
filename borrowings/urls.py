from django.urls import path

from .views import (
    BorrowingCreateView,
    BorrowingDetailView,
    BorrowingListView,
    BorrowingReturnView,
)

app_name = "borrowings"

urlpatterns = [
    path("", BorrowingCreateView.as_view(), name="borrowings-create"),
    path("list/", BorrowingListView.as_view(), name="borrowings-list"),
    path("<int:pk>/", BorrowingDetailView.as_view(), name="borrowings-detail"),
    path(
        "<int:pk>/return/",
        BorrowingReturnView.as_view(),
        name="borrowings-return",
    ),
]
