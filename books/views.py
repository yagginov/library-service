from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

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
