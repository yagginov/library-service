from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BorrowingViewSet

app_name = "borrowings"

router = DefaultRouter()
router.register("", BorrowingViewSet, basename="borrowings")

urlpatterns = [
    path("", include(router.urls)),
]
