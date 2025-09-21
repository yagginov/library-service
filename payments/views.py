from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)
        return queryset
