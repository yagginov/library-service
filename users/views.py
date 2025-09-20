from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets

from users.serializers import UserRegistrationSerializer

User = get_user_model()


class UserRegistrationViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserRegistrationSerializer
