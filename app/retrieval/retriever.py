"""Semantic retriever: query → embedding → Qdrant → filtered, deduped hits.

Pipeline (spec section 18):
    query → embed → top-K candidates → score filter → per-record dedup →
    final top results
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import RetrievalError, VectorStoreError
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService, get_embedding_service
from app.models.retrieval import RetrievalFilters, RetrievedDocument
from app.retrieval.filters import to_qdrant_filter
from app.vectorstore.qdrant_service import QdrantService, get_qdrant_service

logger = get_logger(__name__)


class Retriever:
    """Retrieves the highest-quality unique records for a query."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        qdrant_service: QdrantService | None = None,
    ) -> None:
        self._embedder = embedding_service or get_embedding_service()
        self._qdrant = qdrant_service or get_qdrant_service()

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        final_k: int | None = None,
        min_score: float | None = None,
        filters: RetrievalFilters | None = None,
    ) -> list[RetrievedDocument]:
        """Run the full retrieval pipeline for a sanitized query."""
        settings = get_settings()
        candidates_k = top_k or settings.top_k
        keep_k = final_k or settings.final_context_k
        threshold = min_score if min_score is not None else settings.min_relevance_score

        try:
            vector = self._embedder.embed_query(query)
        except Exception as exc:
            raise RetrievalError(f"query embedding failed: {exc}") from exc

        try:
            points = self._qdrant.search(
                vector,
                top_k=candidates_k,
                score_threshold=threshold,
                query_filter=to_qdrant_filter(filters),
            )
        except VectorStoreError:
            raise
        except Exception as exc:
            raise RetrievalError(f"vector search failed: {exc}") from exc

        # Deduplicate: keep only the best-scoring chunk per parent record.
        best_per_record: dict[str, RetrievedDocument] = {}
        for point in points:
            payload = point.payload or {}
            record_id = str(payload.get("parent_record_id", ""))
            if not record_id or record_id in best_per_record:
                continue  # points arrive score-descending; first is best
            best_per_record[record_id] = RetrievedDocument(
                record_id=record_id,
                chunk_id=str(payload.get("chunk_id", "")),
                question=str(payload.get("question", "")),
                answer=str(payload.get("answer") or payload.get("chunk_text", "")),
                source=str(payload.get("source", "")),
                source_url=str(payload.get("source_url", "")),
                focus=str(payload.get("focus", "")),
                question_type=str(payload.get("question_type", "")),
                score=float(point.score),
            )

        results = list(best_per_record.values())[:keep_k]
        logger.debug("retrieved %d candidates → %d unique records", len(points), len(results))
        return results


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
