"""Models for retrieval results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedDocument(BaseModel):
    """A single retrieval hit returned to services, API, and MCP."""

    record_id: str
    chunk_id: str
    question: str
    answer: str
    source: str = ""
    source_url: str = ""
    focus: str = ""
    question_type: str = ""
    score: float = Field(ge=-1.0, le=1.0)


class RetrievalFilters(BaseModel):
    """Optional metadata filters for retrieval."""

    source: str | None = None
    question_type: str | None = None
    focus: str | None = None
