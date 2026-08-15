"""Sentence-Transformers embedding service.

- Lazy model loading (first call loads the model, subsequent calls reuse it).
- CPU/GPU auto-detection.
- Batched, L2-normalized encoding (cosine-ready).
- Dynamic vector dimension detection — never hard-coded.
- Small LRU cache for query embeddings.
"""

from __future__ import annotations

import threading
from functools import lru_cache

from app.core.config import get_settings
from app.core.exceptions import EmbeddingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Wraps a SentenceTransformer model with lazy loading and batching."""

    def __init__(self, model_name: str | None = None, batch_size: int | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self._model = None
        self._dimension: int | None = None
        self._lock = threading.Lock()

    # ── model lifecycle ────────────────────────────────────────────────────
    def _resolve_model_path(self) -> str:
        """Prefer a local copy under ./models/<name> for offline deployments.

        Falls back to the configured name (downloaded from the HF hub) when
        no local copy exists.
        """
        from pathlib import Path

        candidate = Path("models") / self.model_name.split("/")[-1]
        if (candidate / "config.json").is_file():
            logger.info("Using local embedding model at %s", candidate)
            return str(candidate)
        return self.model_name

    def _load_model(self):  # type: ignore[no-untyped-def]
        if self._model is None:
            with self._lock:
                if self._model is None:  # double-checked under lock
                    try:
                        import torch
                        from sentence_transformers import SentenceTransformer
                    except ImportError as exc:
                        raise EmbeddingError(f"sentence-transformers not installed: {exc}") from exc
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    model_path = self._resolve_model_path()
                    logger.info("Loading embedding model %s on %s", self.model_name, device)
                    try:
                        self._model = SentenceTransformer(model_path, device=device)
                    except Exception as exc:
                        raise EmbeddingError(f"failed to load model {self.model_name}: {exc}") from exc
                    get_dim = getattr(self._model, "get_embedding_dimension", None) or (
                        self._model.get_sentence_embedding_dimension
                    )
                    self._dimension = int(get_dim())
                    logger.info("Embedding model ready (dimension=%d)", self._dimension)
        return self._model

    @property
    def dimension(self) -> int:
        """Vector dimension, detected from the loaded model."""
        if self._dimension is None:
            self._load_model()
        assert self._dimension is not None
        return self._dimension

    def is_ready(self) -> bool:
        return self._model is not None

    # ── encoding ───────────────────────────────────────────────────────────
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of texts into normalized vectors."""
        if not texts:
            return []
        model = self._load_model()
        try:
            vectors = model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except Exception as exc:
            raise EmbeddingError(f"embedding failed: {exc}") from exc
        return [v.tolist() for v in vectors]

    def embed_query(self, query: str) -> list[float]:
        """Encode a single query (cached for repeated identical queries)."""
        return list(self._embed_query_cached(query))

    @lru_cache(maxsize=512)  # noqa: B019 — bounded cache on a process singleton
    def _embed_query_cached(self, query: str) -> tuple[float, ...]:
        return tuple(self.embed_texts([query])[0])


_service: EmbeddingService | None = None
_service_lock = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    """Process-wide singleton embedding service."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = EmbeddingService()
    return _service
