from drf_spectacular.utils import extend_schema, extend_schema_view

user_registration_schema = extend_schema(
    description="Create a new user account in the library system. "
               "After registration, you can use the login endpoint "
                "to get JWT tokens for authentication.",
)

user_profile_schema = extend_schema_view(
    get=extend_schema(
        description="Retrieve current authenticated user's profile information. "
                   "Returns personal details of the logged-in user.",
    ),
    put=extend_schema(
        description="Update all fields of current user's profile. "
                   "All fields are required for PUT request.",
    ),
    patch=extend_schema(
        description="Update specific fields of current user's profile. "
                   "Only provided fields will be updated, others remain unchanged.",
    ),
)
