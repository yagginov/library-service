from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from base.payment_services import payment_service
from payments.models import Payment
from payments.schemas import payment_viewset_schema
from payments.serializers import PaymentSerializer
from payments.services.payment import PaymentProcessor


@payment_viewset_schema
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)
        return queryset

    @action(detail=False, methods=["get"])
    def success(self, request: Request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "No session_id provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PaymentProcessor.mark_success(session_id)
        status_code = (
            status.HTTP_400_BAD_REQUEST if "error" in result else status.HTTP_200_OK
        )
        return Response(result, status=status_code)

    @action(detail=False, methods=["get"])
    def cancel(self, request: Request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "No session_id provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PaymentProcessor.check_if_session_valid(session_id)
        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"message": "You can return to payment later."},
            status=status.HTTP_200_OK,
        )
