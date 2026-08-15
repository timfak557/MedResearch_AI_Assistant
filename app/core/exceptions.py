"""Custom exception hierarchy for the MedResearch backend.

Every domain error inherits from :class:`MedResearchError` so the API layer
can map them to sanitized HTTP responses without leaking internals.
"""

from __future__ import annotations


class MedResearchError(Exception):
    """Base class for all domain errors."""

    #: Default HTTP status the API layer should use for this error family.
    status_code: int = 500
    #: Safe, user-facing message (never includes stack traces or secrets).
    public_message: str = "An internal error occurred."

    def __init__(self, message: str | None = None, *, public_message: str | None = None) -> None:
        super().__init__(message or self.public_message)
        if public_message is not None:
            self.public_message = public_message


class ConfigurationError(MedResearchError):
    public_message = "The service is misconfigured."


class DatasetError(MedResearchError):
    public_message = "A dataset operation failed."


class ParsingError(DatasetError):
    public_message = "Failed to parse dataset content."


class ValidationDataError(DatasetError):
    public_message = "Dataset validation failed."


class EmbeddingError(MedResearchError):
    status_code = 503
    public_message = "The embedding service is unavailable."


class VectorStoreError(MedResearchError):
    status_code = 503
    public_message = "The vector database is unavailable."


class RetrievalError(MedResearchError):
    status_code = 503
    public_message = "Retrieval failed. Please try again."


class LLMError(MedResearchError):
    status_code = 502
    public_message = "The language model is currently unavailable. Please try again."


class CitationError(MedResearchError):
    public_message = "Citation validation failed."


class SafetyError(MedResearchError):
    status_code = 400
    public_message = "The request was blocked by the medical safety layer."


class ConversationError(MedResearchError):
    status_code = 404
    public_message = "Conversation not found."


class InvalidInputError(MedResearchError):
    status_code = 422
    public_message = "Invalid input."


class MCPError(MedResearchError):
    public_message = "MCP tool execution failed."
