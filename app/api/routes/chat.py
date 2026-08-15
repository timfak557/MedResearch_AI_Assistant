"""Chat endpoints: /api/v1/chat and conversation management."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import chat_service
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Evidence-grounded medical chat",
    description=(
        "Runs the full RAG pipeline: safety classification, conversation-aware "
        "query rewriting, semantic retrieval, grounded generation with "
        "citations, citation validation, and output safety checks."
    ),
    responses={
        422: {"description": "Invalid input."},
        502: {"description": "Language model failure."},
        503: {"description": "Retrieval infrastructure unavailable."},
    },
)
def chat(request: ChatRequest, service: ChatService = Depends(chat_service)) -> ChatResponse:
    result = service.chat(request.message, request.conversation_id)
    return ChatResponse(
        conversation_id=result.conversation_id,
        answer=result.answer,
        sources=[
            ChatSource(
                id=c.id,
                record_id=c.record_id,
                question=c.question,
                source=c.source,
                source_url=c.source_url,
                focus=c.focus,
                score=c.score,
            )
            for c in result.sources
        ],
        retrieval_count=result.retrieval_count,
        confidence=result.confidence,
        insufficient_context=result.insufficient_context,
        safety_category=result.safety_category,
        disclaimer=result.disclaimer,
    )


@router.delete(
    "/conversations/{conversation_id}",
    summary="Clear a conversation",
    description="Deletes the conversation history for the given ID.",
    responses={404: {"description": "Conversation not found."}},
)
def delete_conversation(
    conversation_id: str, service: ChatService = Depends(chat_service)
) -> dict[str, str]:
    service.clear_conversation(conversation_id)
    return {"status": "cleared", "conversation_id": conversation_id}
