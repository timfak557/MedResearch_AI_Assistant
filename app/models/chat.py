"""Internal models for the chat pipeline result."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.rag.citations import Citation


class ChatResult(BaseModel):
    """Full result of one chat pipeline run (service-layer output)."""

    conversation_id: str
    answer: str
    sources: list[Citation] = Field(default_factory=list)
    retrieval_count: int = 0
    confidence: float = 0.0
    insufficient_context: bool = False
    safety_category: str = "general_medical_information"
    disclaimer: str = ""
