from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        label="Email",
        write_only=True,
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
        fields = ["email", "password1", "password2"]

    def validate(self, attrs):
        password1 = attrs.get("password1")
        password2 = attrs.get("password2")

        if password1 != password2:
            raise serializers.ValidationError("Passwords do not match.")

        validate_password(attrs.get("password2", ""))
        return super().validate(attrs)

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        email = validated_data.get("email")
        password = validated_data.get("password1")
        return User.objects.create_user(email=email, password=password)
