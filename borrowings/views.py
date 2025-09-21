from rest_framework import generics, permissions

from .models import Borrowing
from .serializers import BorrowingCreateSerializer


class BorrowingCreateView(generics.CreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
