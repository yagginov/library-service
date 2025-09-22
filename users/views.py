from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from users.schemas import user_profile_schema, user_registration_schema
from users.serializers import UserProfileSerializer, UserRegistrationSerializer


@user_registration_schema
class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer


@user_profile_schema
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
