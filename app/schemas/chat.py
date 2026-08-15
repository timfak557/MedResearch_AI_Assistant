"""Request/response schemas for the chat API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's medical question.",
        examples=["What are the symptoms of diabetes?"],
    )
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID for follow-up questions; omit to start a new conversation.",
    )


class ChatSource(BaseModel):
    id: int
    record_id: str
    question: str
    source: str = ""
    source_url: str = ""
    focus: str = ""
    score: float = 0.0


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[ChatSource]
    retrieval_count: int
    confidence: float
    insufficient_context: bool
    safety_category: str
    disclaimer: str
