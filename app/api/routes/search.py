"""Search endpoints: /api/v1/search, /sources, /question-types, /statistics."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import search_service
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search over the MedQuAD knowledge base",
    description=(
        "Embeds the query, searches Qdrant with optional metadata filters, "
        "and returns deduplicated, score-ranked records."
    ),
    responses={
        422: {"description": "Invalid input (empty or oversized query, bad filters)."},
        503: {"description": "Vector store or embedding service unavailable."},
    },
)
def search(request: SearchRequest, service: SearchService = Depends(search_service)) -> SearchResponse:
    results = service.search_medical_knowledge(
        request.query,
        top_k=request.top_k,
        source=request.source,
        focus=request.focus,
        question_type=request.question_type,
    )
    return SearchResponse(
        query=request.query,
        results=[SearchResultItem(**doc.model_dump()) for doc in results],
    )


@router.get(
    "/sources",
    summary="List available sources",
    description="Distinct source names present in the knowledge base (e.g. CancerGov, GARD).",
)
def sources(service: SearchService = Depends(search_service)) -> dict[str, list[str]]:
    return {"sources": service.list_sources()}


@router.get(
    "/question-types",
    summary="List available question types",
    description="Distinct question types present in the knowledge base (e.g. symptoms, treatment).",
)
def question_types(service: SearchService = Depends(search_service)) -> dict[str, list[str]]:
    return {"question_types": service.list_question_types()}


@router.get(
    "/statistics",
    summary="Knowledge base statistics",
    description="Collection size, source/question-type counts, embedding model, and Qdrant health.",
)
def statistics(service: SearchService = Depends(search_service)) -> dict[str, object]:
    return service.statistics()
