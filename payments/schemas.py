from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

payment_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Payments"],
        description="Retrieve list of payments. Regular users see only payments for their own borrowings, "
                   "while admin users can see all payments in the system. "
                   "Payments are automatically created when a borrowing exceeds the expected return date.",
    ),
    retrieve=extend_schema(
        tags=["Payments"],
        description="Retrieve detailed information about a specific payment. "
                   "Regular users can only access payments for their own borrowings, "
                   "while admin users can access any payment in the system.",
    ),
    success=extend_schema(
        tags=["Payments"],
        description="Handle successful payment callback from Stripe. "
                   "Marks the payment as successful in the system.",
    ),
    cancel=extend_schema(
        tags=["Payments"],
        description="Handle cancelled payment callback from Stripe. "
                   "User can return to payment later.",
    ),
)
