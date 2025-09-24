from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.schemas import jwt_token_obtain_schema, jwt_token_refresh_schema


@jwt_token_obtain_schema
class CustomTokenObtainPairView(TokenObtainPairView):
    pass


@jwt_token_refresh_schema
class CustomTokenRefreshView(TokenRefreshView):
    pass