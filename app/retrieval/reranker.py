"""Optional reranking stage.

The default implementation is a no-op that preserves vector-similarity
order, so the system works without a heavy cross-encoder. A cross-encoder
reranker can be added later by implementing :class:`BaseReranker`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.retrieval import RetrievedDocument


class BaseReranker(ABC):
    """Interface for rerankers. Implementations must be stateless per call."""

    @abstractmethod
    def rerank(self, query: str, documents: list[RetrievedDocument]) -> list[RetrievedDocument]:
        """Return documents re-ordered by relevance to ``query``."""


class NoopReranker(BaseReranker):
    """Keeps the original vector-similarity ordering."""

    def rerank(self, query: str, documents: list[RetrievedDocument]) -> list[RetrievedDocument]:
        return documents


class CrossEncoderReranker(BaseReranker):
    """Cross-encoder reranker (optional heavy dependency).

    Loaded lazily; only used when explicitly configured. Falls back to a
    clear error rather than degrading silently.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):  # type: ignore[no-untyped-def]
        if self._model is None:
            from sentence_transformers import CrossEncoder  # heavy import, lazy

            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, query: str, documents: list[RetrievedDocument]) -> list[RetrievedDocument]:
        if not documents:
            return documents
        model = self._load()
        scores = model.predict([(query, d.answer) for d in documents])
        ranked = sorted(zip(documents, scores, strict=True), key=lambda p: float(p[1]), reverse=True)
        return [d for d, _ in ranked]


def get_reranker() -> BaseReranker:
    """Default reranker for the current deployment (no-op)."""
    return NoopReranker()
