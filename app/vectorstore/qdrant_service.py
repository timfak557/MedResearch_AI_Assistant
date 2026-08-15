"""Qdrant vector store service.

Implements the full spec-16 interface with cosine similarity, payload
indexes, batched idempotent upserts (deterministic point IDs prevent
duplicate insertion), and retry on transient failures.
"""

from __future__ import annotations

import threading
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client import models as qm
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError
from app.core.logging import get_logger
from app.models.documents import DocumentChunk

logger = get_logger(__name__)

#: Payload fields that receive keyword indexes for filtering.
INDEXED_FIELDS = ("source", "focus", "question_type", "parent_record_id")

_RETRY = retry(
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=8),
    reraise=True,
)


class QdrantService:
    """Thin, typed wrapper around qdrant-client for this application."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection: str | None = None,
    ) -> None:
        settings = get_settings()
        self.url = url or settings.qdrant_url
        self._api_key = api_key if api_key is not None else (
            settings.qdrant_api_key.get_secret_value() or None
        )
        self.collection = collection or settings.qdrant_collection
        self._client: QdrantClient | None = None
        self._lock = threading.Lock()

    # ── connection ─────────────────────────────────────────────────────────
    def connect(self) -> QdrantClient:
        """Create (or reuse) the client connection."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    try:
                        self._client = QdrantClient(
                            url=self.url, api_key=self._api_key, timeout=30
                        )
                    except Exception as exc:
                        raise VectorStoreError(f"cannot connect to Qdrant: {exc}") from exc
        return self._client

    def health_check(self) -> bool:
        """True when Qdrant answers a lightweight call."""
        try:
            self.connect().get_collections()
            return True
        except Exception:
            return False

    # ── collection management ──────────────────────────────────────────────
    def collection_exists(self, collection: str | None = None) -> bool:
        name = collection or self.collection
        try:
            return bool(self.connect().collection_exists(name))
        except Exception as exc:
            raise VectorStoreError(f"collection_exists failed: {exc}") from exc

    def create_collection(self, vector_dimension: int, collection: str | None = None) -> None:
        """Create the collection (cosine distance) and payload indexes."""
        name = collection or self.collection
        client = self.connect()
        try:
            if not client.collection_exists(name):
                client.create_collection(
                    collection_name=name,
                    vectors_config=qm.VectorParams(
                        size=vector_dimension, distance=qm.Distance.COSINE
                    ),
                )
                logger.info("Created collection %s (dim=%d, cosine)", name, vector_dimension)
            for field_name in INDEXED_FIELDS:
                client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=qm.PayloadSchemaType.KEYWORD,
                )
        except Exception as exc:
            raise VectorStoreError(f"create_collection failed: {exc}") from exc

    def delete_collection(self, collection: str | None = None) -> None:
        name = collection or self.collection
        try:
            self.connect().delete_collection(name)
            logger.info("Deleted collection %s", name)
        except Exception as exc:
            raise VectorStoreError(f"delete_collection failed: {exc}") from exc

    # ── data operations ────────────────────────────────────────────────────
    @staticmethod
    def _payload(chunk: DocumentChunk) -> dict[str, Any]:
        return {
            "chunk_id": chunk.chunk_id,
            "parent_record_id": chunk.parent_record_id,
            "question": chunk.question,
            "answer": chunk.answer,
            "chunk_text": chunk.chunk_text,
            "focus": chunk.focus,
            "source": chunk.source,
            "source_url": chunk.source_url,
            "question_type": chunk.question_type,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            "file_path": chunk.file_path,
        }

    @_RETRY
    def upsert_documents(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        *,
        collection: str | None = None,
        batch_size: int = 256,
    ) -> int:
        """Idempotent batched upsert (deterministic IDs → no duplicates)."""
        if len(chunks) != len(vectors):
            raise VectorStoreError("chunks and vectors length mismatch")
        name = collection or self.collection
        client = self.connect()
        total = 0
        try:
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_vectors = vectors[i : i + batch_size]
                points = [
                    qm.PointStruct(
                        id=chunk.chunk_id,  # deterministic UUID → re-upsert overwrites
                        vector=vector,
                        payload=self._payload(chunk),
                    )
                    for chunk, vector in zip(batch_chunks, batch_vectors, strict=True)
                ]
                client.upsert(collection_name=name, points=points, wait=True)
                total += len(points)
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"upsert failed at offset {total}: {exc}") from exc
        return total

    @staticmethod
    def build_filter(
        *,
        source: str | None = None,
        focus: str | None = None,
        question_type: str | None = None,
        parent_record_id: str | None = None,
    ) -> qm.Filter | None:
        conditions = [
            qm.FieldCondition(key=key, match=qm.MatchValue(value=value))
            for key, value in (
                ("source", source),
                ("focus", focus),
                ("question_type", question_type),
                ("parent_record_id", parent_record_id),
            )
            if value
        ]
        return qm.Filter(must=conditions) if conditions else None

    def search(
        self,
        vector: list[float],
        *,
        top_k: int = 10,
        score_threshold: float | None = None,
        query_filter: qm.Filter | None = None,
        collection: str | None = None,
    ) -> list[qm.ScoredPoint]:
        name = collection or self.collection
        try:
            return self.connect().query_points(
                collection_name=name,
                query=vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
            ).points
        except Exception as exc:
            raise VectorStoreError(f"search failed: {exc}") from exc

    def get_by_id(self, point_id: str, *, collection: str | None = None) -> qm.Record | None:
        name = collection or self.collection
        try:
            records = self.connect().retrieve(name, ids=[point_id], with_payload=True)
            return records[0] if records else None
        except Exception as exc:
            raise VectorStoreError(f"get_by_id failed: {exc}") from exc

    def count(self, *, collection: str | None = None) -> int:
        name = collection or self.collection
        try:
            return int(self.connect().count(name, exact=True).count)
        except Exception as exc:
            raise VectorStoreError(f"count failed: {exc}") from exc

    def delete_by_filter(self, query_filter: qm.Filter, *, collection: str | None = None) -> None:
        name = collection or self.collection
        try:
            self.connect().delete(
                collection_name=name,
                points_selector=qm.FilterSelector(filter=query_filter),
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreError(f"delete_by_filter failed: {exc}") from exc

    # ── aggregations used by API/MCP ───────────────────────────────────────
    def facet_values(self, field: str, *, collection: str | None = None, limit: int = 200) -> list[str]:
        """Distinct values for an indexed payload field."""
        name = collection or self.collection
        try:
            result = self.connect().facet(
                collection_name=name, key=field, limit=limit, exact=False
            )
            return [str(hit.value) for hit in result.hits]
        except Exception as exc:
            raise VectorStoreError(f"facet failed for {field}: {exc}") from exc


_service: QdrantService | None = None
_service_lock = threading.Lock()


def get_qdrant_service() -> QdrantService:
    """Process-wide singleton Qdrant service."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = QdrantService()
    return _service
