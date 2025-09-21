from rest_framework import generics, permissions

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
