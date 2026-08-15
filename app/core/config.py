"""Centralized application configuration.

All values come from environment variables (optionally via a local ``.env``
file). Secrets are stored as ``SecretStr`` so they are never rendered by
``repr``/``str`` or accidentally logged.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── LLM (OpenAI-compatible) ────────────────────────────────────────────
    openai_api_key: SecretStr = Field(default=SecretStr(""), alias="OPENAI_API_KEY")
    openai_model: str = Field(default="", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, gt=0, alias="LLM_MAX_TOKENS")
    llm_timeout_seconds: float = Field(default=60.0, gt=0, alias="LLM_TIMEOUT_SECONDS")

    # ── Embeddings ─────────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    embedding_batch_size: int = Field(default=64, gt=0, alias="EMBEDDING_BATCH_SIZE")

    # ── Qdrant ─────────────────────────────────────────────────────────────
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: SecretStr = Field(default=SecretStr(""), alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="medquad_documents", alias="QDRANT_COLLECTION")

    # ── Dataset paths ──────────────────────────────────────────────────────
    medquad_repository: str = Field(
        default="https://github.com/abachaa/MedQuAD.git", alias="MEDQUAD_REPOSITORY"
    )
    medquad_data_path: Path = Field(default=Path("data/raw/MedQuAD"), alias="MEDQUAD_DATA_PATH")
    processed_data_path: Path = Field(
        default=Path("data/processed/medquad.jsonl"), alias="PROCESSED_DATA_PATH"
    )
    chunks_data_path: Path = Field(
        default=Path("data/processed/medquad_chunks.jsonl"), alias="CHUNKS_DATA_PATH"
    )

    # ── Retrieval ──────────────────────────────────────────────────────────
    top_k: int = Field(default=10, gt=0, alias="TOP_K")
    final_context_k: int = Field(default=5, gt=0, alias="FINAL_CONTEXT_K")
    min_relevance_score: float = Field(default=0.45, ge=0.0, le=1.0, alias="MIN_RELEVANCE_SCORE")
    max_context_chars: int = Field(default=12000, gt=0, alias="MAX_CONTEXT_CHARS")

    # ── Chunking ───────────────────────────────────────────────────────────
    chunk_size: int = Field(default=1000, gt=0, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, ge=0, alias="CHUNK_OVERLAP")

    # ── App limits / behavior ──────────────────────────────────────────────
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_query_length: int = Field(default=2000, gt=0, alias="MAX_QUERY_LENGTH")
    max_top_k: int = Field(default=20, gt=0, alias="MAX_TOP_K")
    conversation_max_turns: int = Field(default=10, gt=0, alias="CONVERSATION_MAX_TURNS")
    conversation_ttl_seconds: int = Field(default=3600, gt=0, alias="CONVERSATION_TTL_SECONDS")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    @field_validator("chunk_overlap")
    @classmethod
    def _overlap_smaller_than_chunk(cls, v: int, info) -> int:  # type: ignore[no-untyped-def]
        chunk_size = info.data.get("chunk_size", 1000)
        if v >= chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_configured(self) -> bool:
        """True when enough LLM configuration is present to call the API."""
        return bool(self.openai_api_key.get_secret_value() and self.openai_model)

    def safe_dump(self) -> dict[str, object]:
        """Configuration dump with secrets redacted — safe for logs."""
        data = self.model_dump()
        for key in ("openai_api_key", "qdrant_api_key"):
            secret: SecretStr = getattr(self, key)
            data[key] = "***" if secret.get_secret_value() else ""
        return data


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
