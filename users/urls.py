from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import UserRegistrationViewSet

router = DefaultRouter()
router.register("register", UserRegistrationViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]

app_name="users"
