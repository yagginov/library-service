from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

borrowings_viewset_schema = extend_schema_view(
    list=extend_schema(
        description="Retrieve list of borrowings. Regular users see only their own borrowings, "
                    "while admin users can see all borrowings.",
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                description="Filter by active status.",
            ),
        ],
    ),
    create=extend_schema(
        description="Borrow a book from the library. "
                    "The book inventory will be automatically decreased by 1.",
    ),
    retrieve=extend_schema(
        description="Retrieve detailed information about a specific borrowing. "
                   "Regular users can only access their own borrowings, "
                   "while admin users can access any borrowing.",
    ),
    return_book=extend_schema(
        description="Mark a borrowing as returned and set the actual return date to today. "
                   "The book inventory will be automatically increased by 1. "
                   "Only the user who borrowed the book (or admin) can return it.",
    ),
)
