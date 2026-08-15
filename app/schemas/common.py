"""Shared API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Sanitized error body — never contains stack traces or internals."""

    error: str
    request_id: str = "-"


class HealthResponse(BaseModel):
    status: str
    service: str = "medresearch-api"


class ReadyResponse(BaseModel):
    status: str
    qdrant: bool
    embedding_model: bool
    llm_configured: bool
