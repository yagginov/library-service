from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth.hashers import check_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        label="Email",
        required=True,
    )
    password1 = serializers.CharField(
        label="Password",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )
    password2 = serializers.CharField(
        label="Password (again)",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = ["id", "email", "password1", "password2"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already being used by someone."
            )
        return value

    def validate(self, attrs):
        password1 = attrs.get("password1")
        password2 = attrs.get("password2")

        if password1 != password2:
            raise serializers.ValidationError("Passwords do not match.")

        validate_password(password1)
        return super().validate(attrs)

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        email = validated_data.get("email")
        password = validated_data.get("password1")
        return User.objects.create_user(email=email, password=password)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class ChangeUserPassword(serializers.Serializer):
    old_password = serializers.CharField(
        label="Old password",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )
    password1 = serializers.CharField(
        label="New password",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )
    password2 = serializers.CharField(
        label="Repeat new password",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )

    def validate(self, attrs):
        user = self.context["request"].user
        old_password = attrs.get("old_password")
        password1 = attrs.get("password1")
        password2 = attrs.get("password2")

        if not check_password(old_password, user.password):
            raise serializers.ValidationError("Old password is invalid.")

        if password1 != password2:
            raise serializers.ValidationError("New passwords do not match.")

        validate_password(password1)
        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password1"])
        instance.save()
        return instance
