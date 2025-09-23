from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from base.fine_service import fine_service
from base.permissions import IsAdminOrOwnerWithCreatePermission
from borrowings.filters import BorrowingFilter
from borrowings.models import Borrowing
from borrowings.schemas import borrowings_viewset_schema
from borrowings.serializers import BorrowingCreateSerializer, BorrowingDetailSerializer


@borrowings_viewset_schema
class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAdminOrOwnerWithCreatePermission, ]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BorrowingFilter

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        try:
            borrowing.mark_returned()
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fine_payment = fine_service.create_fine_payment_if_overdue(borrowing)

        borrowing.refresh_from_db()
        serializer = self.get_serializer(borrowing)
        response_data = serializer.data

        if fine_payment:
            response_data["fine_payment"] = {
                "id": fine_payment.id,
                "amount": str(fine_payment.money_to_pay),
                "session_url": fine_payment.session_url,
                "status": fine_payment.status,
                "message": "Fine payment created due to overdue return. "
                           "Please complete the payment.",
            }
        return Response(response_data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingCreateSerializer
