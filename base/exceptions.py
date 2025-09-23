class BorrowingError(Exception):
    def __init__(self, message: str = "Some error while creating Borrowing.") -> None:
        super().__init__(message)


class PaymentSessionCreationError(BorrowingError):
    def __init__(self, message: str = "Payment session was not created.") -> None:
        super().__init__(message)


class BookNotAvailableError(BorrowingError):
    def __init__(self, message: str = "Book is not available.") -> None:
        super().__init__(message)
