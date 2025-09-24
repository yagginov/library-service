from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from base.borrowing_service import borrowing_service
from base.fine_service import fine_service
from base.permissions import IsAdminOrOwnerWithCreatePermission
from borrowings.filters import BorrowingFilter
from borrowings.models import Borrowing
from borrowings.schemas import borrowings_viewset_schema
from borrowings.serializers import BorrowingCreateSerializer, BorrowingDetailSerializer, RenewPaymentResponseSerializer
from payments.models import Payment


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

    @extend_schema(responses={200: RenewPaymentResponseSerializer(many=True)})
    @action(detail=True, methods=["post"])
    def renew_payment(self, request, pk=None):
        borrowing = self.get_object()
        payments = borrowing.payments.all()
        responses = []

        paid_payment = payments.filter(
            type=Payment.Type.PAYMENT, status=Payment.Status.PAID
        ).first()
        pending_payment = payments.filter(
            type=Payment.Type.PAYMENT, status=Payment.Status.PENDING
        ).first()

        if not paid_payment:
            if pending_payment:
                responses.append({"payment": "Active payment already exists"})
            else:
                payment = borrowing_service.renew_payment_for_borrowing(borrowing)
                responses.append({"payment": f"New payment created with id {payment.id}"})

        if borrowing.actual_return_date:
            paid_fine = payments.filter(
                type=Payment.Type.FINE, status=Payment.Status.PAID
            ).first()
            pending_fine = payments.filter(
                type=Payment.Type.FINE, status=Payment.Status.PENDING
            ).first()

            if not paid_fine:
                if pending_fine:
                    responses.append({"fine": "Active fine payment already exists"})
                else:
                    fine = fine_service.create_fine_payment_if_overdue(borrowing)
                    if fine:
                        responses.append({"fine": f"New fine created with id {fine.id}"})
                    else:
                        responses.append({"fine": "You are not overdue your borrowing"})

        if not responses:
            return Response(
                [{"message": "Nothing to pay"}],
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(responses, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingCreateSerializer
