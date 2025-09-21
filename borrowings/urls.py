from django.urls import path

from .views import BorrowingCreateView

app_name = "borrowings"

urlpatterns = [
    path("", BorrowingCreateView.as_view(), name="borrowings-create"),
]
