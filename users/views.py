from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.schemas import user_profile_schema, user_registration_schema
from users.serializers import ChangeUserPassword, UserProfileSerializer, UserRegistrationSerializer


@user_registration_schema
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


@user_profile_schema
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangeUserPasswordView(generics.UpdateAPIView):
    serializer_class = ChangeUserPassword
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
