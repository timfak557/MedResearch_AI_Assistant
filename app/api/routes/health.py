"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.embeddings.embedding_service import get_embedding_service
from app.schemas.common import HealthResponse, ReadyResponse
from app.vectorstore.qdrant_service import get_qdrant_service

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns healthy while the API process is running.",
)
def health() -> HealthResponse:
    return HealthResponse(status="healthy")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness check",
    description=(
        "Checks Qdrant connectivity, embedding model availability, and LLM "
        "configuration. Returns 503 when any dependency is not ready."
    ),
    responses={503: {"description": "One or more dependencies are not ready."}},
)
def ready(response: Response) -> ReadyResponse:
    settings = get_settings()
    qdrant_ok = get_qdrant_service().health_check()

    embedder = get_embedding_service()
    try:
        model_ok = embedder.dimension > 0
    except Exception:
        model_ok = False

    llm_ok = settings.llm_configured
    all_ok = qdrant_ok and model_ok and llm_ok
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ready" if all_ok else "not_ready",
        qdrant=qdrant_ok,
        embedding_model=model_ok,
        llm_configured=llm_ok,
    )
