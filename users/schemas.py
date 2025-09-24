from drf_spectacular.utils import extend_schema, extend_schema_view

from users.serializers import ChangeUserPassword, UserRegistrationSerializer

user_registration_schema = extend_schema(
    tags=["Users"],
    description="Create a new user account in the library system. "
               "After registration, you can use the login endpoint "
                "to get JWT tokens for authentication.",
    request=UserRegistrationSerializer,
)

user_profile_schema = extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        description="Retrieve current authenticated user's profile information. "
                   "Returns personal details of the logged-in user.",
    ),
    put=extend_schema(
        tags=["Users"],
        description="Update all fields of current user's profile. "
                   "All fields are required for PUT request.",
    ),
    patch=extend_schema(
        tags=["Users"],
        description="Update specific fields of current user's profile. "
                   "Only provided fields will be updated, others remain unchanged.",
    ),
)

user_change_password_schema = extend_schema(
    description="Change password for the current authenticated user. "
               "Requires old password for security verification.",
    tags=["Users"],
    request=ChangeUserPassword
)


jwt_token_obtain_schema = extend_schema(
    description="Login with email and password to obtain access and refresh JWT tokens.",
    tags=["Users"]
)


jwt_token_refresh_schema = extend_schema(
    description="Use refresh token to obtain a new access token.",
    tags=["Users"]
)