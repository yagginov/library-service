from drf_spectacular.utils import extend_schema_view, extend_schema


payment_viewset_schema = extend_schema_view(
    list=extend_schema(
        description="Retrieve list of payments. Regular users see only payments for their own borrowings, "
                   "while admin users can see all payments in the system. "
                   "Payments are automatically created when a borrowing exceeds the expected return date.",
    ),
    retrieve=extend_schema(
        description="Retrieve detailed information about a specific payment. "
                   "Regular users can only access payments for their own borrowings, "
                   "while admin users can access any payment in the system.",
    )
)