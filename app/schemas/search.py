"""Request/response schemas for the search API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
        description="Medical question or keywords to search for.",
        examples=["What are the symptoms of diabetes?"],
    )
    top_k: int | None = Field(
        default=5, ge=1, le=20, description="Number of results to return."
    )
    source: str | None = Field(default=None, description="Filter by source, e.g. 'CancerGov'.")
    focus: str | None = Field(default=None, description="Filter by medical topic.")
    question_type: str | None = Field(default=None, description="Filter by question type, e.g. 'symptoms'.")


class SearchResultItem(BaseModel):
    record_id: str
    question: str
    answer: str
    source: str = ""
    source_url: str = ""
    focus: str = ""
    question_type: str = ""
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
