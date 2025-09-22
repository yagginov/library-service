from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from base.permissions import IsAdminOrOwnerWithCreatePermission
from borrowings.filters import BorrowingFilter
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer, BorrowingDetailSerializer
from borrowings.schemas import borrowings_viewset_schema


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

        borrowing.refresh_from_db()
        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingCreateSerializer
