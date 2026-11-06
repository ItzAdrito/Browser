"""Domain-specific exceptions for PyBrowser."""


class BrowserException(Exception):
    """Base exception for all browser runtime errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class InvalidURLError(BrowserException):
    """Raised when an input cannot be resolved into a valid URL or search query."""


class StorageError(BrowserException):
    """Raised when an underlying database or persistence operation fails."""


class ProfileError(BrowserException):
    """Raised when web engine profile or session initialization fails."""
