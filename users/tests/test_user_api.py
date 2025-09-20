from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from users.serializers import UserRegistrationSerializer

User = get_user_model()


class TestUserRegistrationSerializer(APITestCase):

    def setUp(self):
        self.user_data = {
            "email": "test@test.com",
            "password1": "dklahfiuphUS&88tds",
            "password2": "dklahfiuphUS&88tds",
        }

    def test_create_user_with_valid_data(self):
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_create_user_with_not_mathed_passwords(self):
        self.user_data["password2"] = "not the same"
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())

    def test_create_user_with_simple_password(self):
        self.user_data["password1"] = "12345678"
        self.user_data["password2"] = "12345678"
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())

    def test_create_user_with_bad_email(self):
        self.user_data["email"] = "not email at all"
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
