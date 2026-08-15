"""Search service: the single retrieval entry point for API and MCP."""

from __future__ import annotations

from app.core.logging import get_logger
from app.core.security import clamp_top_k, sanitize_query
from app.embeddings.embedding_service import get_embedding_service
from app.models.retrieval import RetrievedDocument
from app.retrieval.filters import sanitize_filters
from app.retrieval.reranker import BaseReranker, get_reranker
from app.retrieval.retriever import Retriever, get_retriever
from app.vectorstore.qdrant_service import QdrantService, get_qdrant_service

logger = get_logger(__name__)


class SearchService:
    """Connects embedding, retrieval, Qdrant, reranking, and filtering."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        reranker: BaseReranker | None = None,
        qdrant: QdrantService | None = None,
    ) -> None:
        self._retriever = retriever or get_retriever()
        self._reranker = reranker or get_reranker()
        self._qdrant = qdrant or get_qdrant_service()

    def search_medical_knowledge(
        self,
        query: str,
        *,
        top_k: int | None = None,
        source: str | None = None,
        focus: str | None = None,
        question_type: str | None = None,
        min_score: float | None = None,
    ) -> list[RetrievedDocument]:
        """Sanitized, filtered, optionally reranked semantic search."""
        clean_query = sanitize_query(query)
        k = clamp_top_k(top_k)
        filters = sanitize_filters(source=source, question_type=question_type, focus=focus)

        documents = self._retriever.retrieve(
            clean_query,
            final_k=k,
            min_score=min_score,
            filters=filters,
        )
        return self._reranker.rerank(clean_query, documents)

    # ── metadata helpers (API /sources, /question-types, /statistics) ──────
    def list_sources(self) -> list[str]:
        return sorted(self._qdrant.facet_values("source"))

    def list_question_types(self) -> list[str]:
        return sorted(self._qdrant.facet_values("question_type"))

    def statistics(self) -> dict[str, object]:
        embedder = get_embedding_service()
        return {
            "collection": self._qdrant.collection,
            "total_chunks": self._qdrant.count(),
            "sources": len(self.list_sources()),
            "question_types": len(self.list_question_types()),
            "embedding_model": embedder.model_name,
            "qdrant_healthy": self._qdrant.health_check(),
        }


_service: SearchService | None = None


def get_search_service() -> SearchService:
    global _service
    if _service is None:
        _service = SearchService()
    return _service
