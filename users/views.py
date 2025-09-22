from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.serializers import (
    UserProfileSerializer,
    UserRegistrationSerializer,
    ChangeUserPassword
)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny,]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated,]

    def get_object(self):
        return self.request.user


class ChangeUserPasswordView(generics.UpdateAPIView):
    serializer_class = ChangeUserPassword
    permission_classes = [IsAuthenticated,]

    def get_object(self):
        return self.request.user
