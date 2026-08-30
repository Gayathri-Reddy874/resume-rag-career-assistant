"""
Custom exception hierarchy.

Using specific exception types (instead of raising HTTPException deep inside
service code, or swallowing errors into a generic string) keeps the service
layer framework-agnostic and lets the API layer decide the correct HTTP
status + response shape in one place (see app/main.py exception handlers).
"""


class CareerAssistantError(Exception):
    """Base class for all application-specific errors."""


class UnsupportedFileTypeError(CareerAssistantError):
    """Raised when an uploaded file has a disallowed extension."""


class FileTooLargeError(CareerAssistantError):
    """Raised when an uploaded file exceeds the configured size limit."""


class EmptyDocumentError(CareerAssistantError):
    """Raised when no extractable text is found in an uploaded file."""


class NoResumeFoundError(CareerAssistantError):
    """Raised when a question is asked before any resume has been uploaded for the user."""


class ModelInferenceError(CareerAssistantError):
    """Raised when the underlying LLM/embedding call fails."""
