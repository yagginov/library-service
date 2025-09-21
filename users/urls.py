from django.urls import path

from users.views import UserProfileView, UserRegistrationView

urlpatterns = [
    path("", UserRegistrationView.as_view(), name="register"),
    path("me/", UserProfileView.as_view(), name="me"),
]

app_name="users"
