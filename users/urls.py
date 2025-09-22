from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    UserProfileView,
    UserRegistrationView,
    ChangeUserPasswordView,
)

urlpatterns = [
    path("", UserRegistrationView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", UserProfileView.as_view(), name="me"),
    path("me/change-password/", ChangeUserPasswordView.as_view()),
]

app_name="users"
