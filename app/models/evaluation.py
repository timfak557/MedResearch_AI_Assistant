"""Models for evaluation results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalMetrics(BaseModel):
    protocol: str
    sample_size: int
    recall_at_1: float = Field(ge=0, le=1)
    recall_at_5: float = Field(ge=0, le=1)
    recall_at_10: float = Field(ge=0, le=1)
    mrr: float = Field(ge=0, le=1)
    ndcg_at_10: float = Field(ge=0, le=1)
    retrieval_latency_ms: dict[str, float]


class GenerationMetrics(BaseModel):
    skipped: bool = False
    reason: str | None = None
    questions_evaluated: int = 0
    citation_correctness: float | None = None
    citation_completeness: float | None = None
    answer_faithfulness_lexical: float | None = None
    unsupported_claim_rate: float | None = None


class SafetyMetrics(BaseModel):
    classification_cases: int
    classification_accuracy: float = Field(ge=0, le=1)
    emergency_blocked_before_rag: bool
    safety_compliance: float = Field(ge=0, le=1)


class EvaluationResults(BaseModel):
    timestamp: str
    embedding_model: str
    collection: str
    retrieval: RetrievalMetrics
    generation: GenerationMetrics
    safety: SafetyMetrics
