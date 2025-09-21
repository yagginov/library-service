from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Borrowing
from .serializers import BorrowingCreateSerializer


class BorrowingCreateView(generics.CreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class BorrowingListView(generics.ListAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            qs = qs.filter(user_id=user_id)
        if is_active is not None:
            is_active = is_active.lower() == "true"
            if is_active:
                qs = qs.filter(actual_return_date__isnull=True)
            else:
                qs = qs.filter(actual_return_date__isnull=False)
        return qs


class BorrowingDetailView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class BorrowingReturnView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            borrowing = Borrowing.objects.get(pk=pk)
            borrowing.mark_returned()
        except Borrowing.DoesNotExist:
            return Response(
                {"detail": "Borrowing not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BorrowingCreateSerializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)
