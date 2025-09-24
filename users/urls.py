from django.urls import path

from users.jwt_views import CustomTokenObtainPairView, CustomTokenRefreshView
from users.views import ChangeUserPasswordView, UserProfileView, UserRegistrationView

urlpatterns = [
    path("", UserRegistrationView.as_view(), name="register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("me/", UserProfileView.as_view(), name="me"),
    path("me/change-password/", ChangeUserPasswordView.as_view(), name="change-password"),
]

app_name="users"
