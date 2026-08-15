"""MCP tool implementations.

Every tool is a thin adapter over the shared service layer — no retrieval
or business logic lives here. All inputs are validated with the same
sanitizers used by the REST API, and all outputs are plain JSON-safe dicts.
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import MedResearchError
from app.core.logging import get_logger
from app.core.security import clamp_top_k, sanitize_query
from app.services.search_service import get_search_service
from app.vectorstore.qdrant_service import get_qdrant_service

logger = get_logger(__name__)


def _doc_to_dict(doc: Any) -> dict[str, Any]:
    return {
        "record_id": doc.record_id,
        "question": doc.question,
        "answer": doc.answer,
        "source": doc.source,
        "source_url": doc.source_url,
        "focus": doc.focus,
        "question_type": doc.question_type,
        "score": doc.score,
    }


def _safe(fn):  # type: ignore[no-untyped-def]
    """Wrap tool execution so errors surface as structured, sanitized data."""

    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return fn(*args, **kwargs)
        except MedResearchError as exc:
            logger.warning("MCP tool error: %s", exc)
            return {"error": exc.public_message}
        except Exception as exc:
            logger.error("MCP tool unexpected error: %s", type(exc).__name__)
            return {"error": "Tool execution failed."}

    return wrapper


@_safe
def search_medical_knowledge(
    query: str,
    top_k: int = 5,
    source: str | None = None,
    focus: str | None = None,
    question_type: str | None = None,
) -> dict[str, Any]:
    results = get_search_service().search_medical_knowledge(
        query, top_k=top_k, source=source, focus=focus, question_type=question_type
    )
    return {"query": query, "results": [_doc_to_dict(d) for d in results]}


@_safe
def get_medical_record(record_id: str) -> dict[str, Any]:
    record_id = (record_id or "").strip()
    if not record_id:
        return {"error": "record_id is required."}
    qdrant = get_qdrant_service()
    # Fetch all chunks belonging to the record via payload filter.
    flt = qdrant.build_filter(parent_record_id=record_id)
    try:
        scroll, _ = qdrant.connect().scroll(
            collection_name=qdrant.collection, scroll_filter=flt,
            limit=64, with_payload=True,
        )
    except Exception as exc:
        raise MedResearchError(f"scroll failed: {exc}") from exc
    if not scroll:
        return {"error": f"No record found with id {record_id}."}
    chunks = sorted(scroll, key=lambda p: (p.payload or {}).get("chunk_index", 0))
    payload = chunks[0].payload or {}
    return {
        "record_id": record_id,
        "question": payload.get("question", ""),
        "answer": payload.get("answer", ""),
        "focus": payload.get("focus", ""),
        "source": payload.get("source", ""),
        "source_url": payload.get("source_url", ""),
        "question_type": payload.get("question_type", ""),
        "total_chunks": payload.get("total_chunks", len(chunks)),
    }


@_safe
def find_related_questions(question: str, top_k: int = 5) -> dict[str, Any]:
    clean = sanitize_query(question)
    k = clamp_top_k(top_k)
    results = get_search_service().search_medical_knowledge(clean, top_k=k)
    return {
        "question": clean,
        "related_questions": [
            {
                "record_id": d.record_id,
                "question": d.question,
                "focus": d.focus,
                "question_type": d.question_type,
                "source": d.source,
                "score": d.score,
            }
            for d in results
        ],
    }


@_safe
def compare_medical_topics(topic_a: str, topic_b: str) -> dict[str, Any]:
    a = sanitize_query(topic_a)
    b = sanitize_query(topic_b)
    service = get_search_service()
    return {
        "topic_a": {"topic": a, "evidence": [
            _doc_to_dict(d) for d in service.search_medical_knowledge(a, top_k=3)
        ]},
        "topic_b": {"topic": b, "evidence": [
            _doc_to_dict(d) for d in service.search_medical_knowledge(b, top_k=3)
        ]},
        "note": (
            "Evidence retrieved independently for each topic from MedQuAD. "
            "Compare the answers; no synthesized comparison is generated here."
        ),
    }


@_safe
def list_medical_sources() -> dict[str, Any]:
    return {"sources": get_search_service().list_sources()}


@_safe
def list_question_types() -> dict[str, Any]:
    return {"question_types": get_search_service().list_question_types()}


@_safe
def get_system_statistics() -> dict[str, Any]:
    return get_search_service().statistics()
