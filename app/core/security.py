"""Security utilities: input validation, sanitization, and secure headers.

These helpers are shared by the FastAPI layer and the MCP tools so both
entry points enforce identical limits.
"""

from __future__ import annotations

import re
import unicodedata

from app.core.config import get_settings
from app.core.exceptions import InvalidInputError

#: Characters that are stripped from queries (control chars except newline/tab).
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

#: Secure headers applied to every HTTP response.
SECURE_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'",
}


def sanitize_query(query: str, *, max_length: int | None = None) -> str:
    """Validate and normalize a user query.

    Raises :class:`InvalidInputError` for empty or oversized input.
    Medical content is preserved verbatim — only control characters and
    excessive whitespace are removed.
    """
    settings = get_settings()
    limit = max_length or settings.max_query_length

    if query is None:
        raise InvalidInputError("query is required", public_message="Query must not be empty.")

    query = unicodedata.normalize("NFC", str(query))
    query = _CONTROL_CHARS.sub(" ", query)
    query = re.sub(r"\s+", " ", query).strip()

    if not query:
        raise InvalidInputError("query is empty", public_message="Query must not be empty.")
    if len(query) > limit:
        raise InvalidInputError(
            f"query length {len(query)} exceeds limit {limit}",
            public_message=f"Query is too long (maximum {limit} characters).",
        )
    return query


def clamp_top_k(top_k: int | None, *, default: int | None = None) -> int:
    """Clamp a requested top_k into [1, MAX_TOP_K]."""
    settings = get_settings()
    value = top_k if top_k is not None else (default or settings.final_context_k)
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidInputError("top_k must be an integer", public_message="top_k must be an integer.")
    return max(1, min(value, settings.max_top_k))


def sanitize_metadata_value(value: str | None, *, field: str, max_length: int = 200) -> str | None:
    """Sanitize an optional metadata filter value (source / focus / question_type)."""
    if value is None:
        return None
    value = _CONTROL_CHARS.sub("", str(value)).strip()
    if not value:
        return None
    if len(value) > max_length:
        raise InvalidInputError(
            f"{field} filter too long",
            public_message=f"{field} filter is too long (maximum {max_length} characters).",
        )
    return value


def sanitize_error_message(exc: Exception) -> str:
    """Return a safe, generic message for unexpected exceptions."""
    from app.core.exceptions import MedResearchError

    if isinstance(exc, MedResearchError):
        return exc.public_message
    return "An unexpected error occurred."
