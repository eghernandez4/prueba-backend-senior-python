"""
Domain and business exception hierarchy.
"""

from fastapi import status


class DomainException(Exception):
    """
    Base exception for all domain and business rule errors.

    Encapsulates HTTP status code and message to allow a single generic
    exception handler in the presentation layer (Open/Closed Principle).
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ApplicationNotFoundError(DomainException):
    """Raised when an application is not found."""

    def __init__(self, application_id: int) -> None:
        self.application_id = application_id
        super().__init__(
            message=f"Application with ID {application_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnsupportedProductError(DomainException):
    """Raised when a product type is unsupported or has no policy registered."""

    def __init__(self, product: str) -> None:
        super().__init__(
            message=f"No policy strategy registered for product: {product}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
