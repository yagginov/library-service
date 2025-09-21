from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from base.permissions import IsAdminOrIsAuthenticatedReadOnly
from books.models import Book
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly, ]
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]
    filterset_fields = ("cover", "author", )
    search_fields = ("title", "author", )
    ordering_fields = (
        "title",
        "author",
        "daily_fee",
        "inventory",
    )

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny, ]
        else:
            permission_classes = [IsAdminOrIsAuthenticatedReadOnly, ]
        return [permission() for permission in permission_classes]
