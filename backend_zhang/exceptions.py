"""Backend exception types.

The service layer catches these exceptions and converts them into the unified
``{"success": False, "message": ...}`` response format, so that JSON file
errors, invalid arguments, etc. never crash the program.
"""


class BackendError(Exception):
    """Base backend exception; ``message`` is a user-facing hint."""

    default_message = "Operation failed"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(BackendError):
    """Field validation failed (username, password, price, category, etc.)."""

    default_message = "Validation failed"


class NotFoundError(BackendError):
    """User or item does not exist."""

    default_message = "Record not found"


class PermissionDeniedError(BackendError):
    """Unauthorized operation (a non-seller editing/removing/deleting an item, etc.)."""

    default_message = "Permission denied for this item"


class ConflictError(BackendError):
    """Data conflict (duplicate username, status forbids the operation, etc.)."""

    default_message = "Data conflict"


class DataFileError(BackendError):
    """JSON data file read/write error (corrupt file, no permission, disk error, etc.)."""

    default_message = "Data file read/write failed"
