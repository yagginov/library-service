from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from base.permissions import IsAdminOrOwnerWithCreatePermission
from borrowings.filters import BorrowingFilter
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BorrowingCreateSerializer
    permission_classes = [IsAdminOrOwnerWithCreatePermission, ]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BorrowingFilter

    def get_queryset(self):
        if self.request.user.is_staff:
            return Borrowing.objects.all()
        return Borrowing.objects.filter(user=self.request.user)

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

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)
