from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

book_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Books"],
        description="Retrieve a list of all available books in the library.",
        parameters=[
            OpenApiParameter(
                name="cover",
                type=OpenApiTypes.STR,
                description="Filter by cover type",
                enum=["HARD", "SOFT"],
            ),
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.STR,
                description="Filter by exact author name",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                description="Search by title and authors",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                description="Order by field. Add '-' prefix for descending order.",
                enum=[
                    "title",
                    "-title",
                    "author",
                    "-author",
                    "daily_fee",
                    "-daily_fee",
                    "inventory",
                    "-inventory"
                ],
            ),
        ],
    ),
    create=extend_schema(
        tags=["Books"],
        description="Add a new book to the library catalog. "
                    "Only admin users can create books.",
    ),
    retrieve=extend_schema(
        tags=["Books"],
        description="Retrieve detailed information about a specific book by its ID.",
    ),
    update=extend_schema(
        tags=["Books"],
        description="Update all fields of a specific book. "
                    "Only admin users can update books.",
    ),
    partial_update=extend_schema(
        tags=["Books"],
        description="Update specific fields of a book. "
                    "Only admin users can update books.",
    ),
    destroy=extend_schema(
        tags=["Books"],
        description="Remove a book from the library catalog. "
                    "Only admin users can delete books.",
    ),
)
