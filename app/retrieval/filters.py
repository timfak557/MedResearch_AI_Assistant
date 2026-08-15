"""Translation of API-level filters into Qdrant filters."""

from __future__ import annotations

from qdrant_client import models as qm

from app.core.security import sanitize_metadata_value
from app.models.retrieval import RetrievalFilters
from app.vectorstore.qdrant_service import QdrantService


def sanitize_filters(
    *,
    source: str | None = None,
    question_type: str | None = None,
    focus: str | None = None,
) -> RetrievalFilters:
    """Validate and normalize raw filter inputs."""
    return RetrievalFilters(
        source=sanitize_metadata_value(source, field="source"),
        question_type=sanitize_metadata_value(question_type, field="question_type"),
        focus=sanitize_metadata_value(focus, field="focus"),
    )


def to_qdrant_filter(filters: RetrievalFilters | None) -> qm.Filter | None:
    """Build the Qdrant filter object (None when no filters set)."""
    if filters is None:
        return None
    return QdrantService.build_filter(
        source=filters.source,
        question_type=filters.question_type,
        focus=filters.focus,
    )
