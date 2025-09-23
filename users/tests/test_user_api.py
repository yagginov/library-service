from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
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


class TestUserRegistrationViewSet(APITestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@test.com",
            "password1": "(*FDfas9hdgoaisdoi(&f0du",
            "password2": "(*FDfas9hdgoaisdoi(&f0du",
        }
        self.url = reverse("users:register")

    def test_create_user_with_valid_data(self):
        response = self.client.post(self.url, data=self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_create_second_user_with_same_email(self):
        User.objects.create_user(email="test@test.com", password="p")

        response = self.client.post(self.url, data=self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_create_user_with_wrong_email(self):
        self.user_data["email"] = "not email at all"
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_create_user_with_not_mathed_password(self):
        self.user_data["password2"] = "not the same"
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertTrue(any("passwords" in error.lower() for error in response.data["non_field_errors"]))

    def test_create_user_with_no_password(self):
        del self.user_data["password1"]
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password1", response.data)


class TestUserProfileView(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="test@test.com",
            password="testpass",
            first_name="name",
            last_name="last_name"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("users:me")

    def test_get_user_profile(self):
        response = self.client.get(self.url)
        self.url = reverse("users:me")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("first_name", response.data)
        self.assertIn("last_name", response.data)
        self.assertIn("email", response.data)

    def test_update_user_profile(self):
        response = self.client.patch(
            self.url, {"email": "test1@test.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test1@test.com")
