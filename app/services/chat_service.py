"""Chat service: the full RAG pipeline behind /api/v1/chat and MCP.

Pipeline (spec section 27):
    message → safety classification → query rewriting → retrieval →
    optional reranking → context building → LLM → citation validation →
    output safety validation → final response
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
from app.core.security import sanitize_query
from app.models.chat import ChatResult
from app.rag.citations import validate_citations
from app.rag.context_builder import build_context
from app.rag.generator import LLMGenerator, get_generator
from app.rag.prompts import INSUFFICIENT_CONTEXT_MESSAGE, MEDICAL_DISCLAIMER
from app.retrieval.reranker import BaseReranker, get_reranker
from app.retrieval.retriever import Retriever, get_retriever
from app.safety.guardrails import check_input, check_output
from app.services.conversation_service import ConversationService, get_conversation_service

logger = get_logger(__name__)

#: Answer used when the LLM output fails output-safety validation.
_BLOCKED_OUTPUT_MESSAGE = (
    "I generated a response that did not pass the medical safety checks, so "
    "I can't share it. Please rephrase your question, and remember to consult "
    "a qualified healthcare professional for personal medical decisions."
)


class ChatService:
    """Orchestrates one chat turn end to end."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        reranker: BaseReranker | None = None,
        generator: LLMGenerator | None = None,
        conversations: ConversationService | None = None,
    ) -> None:
        self._retriever = retriever or get_retriever()
        self._reranker = reranker or get_reranker()
        self._generator = generator or get_generator()
        self._conversations = conversations or get_conversation_service()

    def chat(self, message: str, conversation_id: str | None = None) -> ChatResult:
        start = time.time()

        conversation = self._conversations.get_or_create(conversation_id)
        clean_message = sanitize_query(message)

        # 1) Input safety.
        decision = check_input(clean_message)
        if not decision.allow_rag:
            self._conversations.add_turn(conversation, "user", clean_message)
            self._conversations.add_turn(conversation, "assistant", decision.direct_response or "")
            self._log(decision.category.value, 0, start)
            return ChatResult(
                conversation_id=conversation.id,
                answer=decision.direct_response or "",
                safety_category=decision.category.value,
                disclaimer=MEDICAL_DISCLAIMER,
            )

        # 2) Conversation-aware query rewriting (fresh retrieval every turn;
        #    previous answers are never used as evidence).
        retrieval_query = self._conversations.rewrite_query(conversation, clean_message)

        # 3) Retrieval + optional reranking.
        documents = self._retriever.retrieve(retrieval_query)
        documents = self._reranker.rerank(retrieval_query, documents)

        # 4) Insufficient context → honest refusal, no LLM call.
        if not documents:
            answer = INSUFFICIENT_CONTEXT_MESSAGE
            self._conversations.add_turn(conversation, "user", clean_message)
            self._conversations.add_turn(conversation, "assistant", answer)
            self._log(decision.category.value, 0, start)
            return ChatResult(
                conversation_id=conversation.id,
                answer=f"{answer}\n\n{MEDICAL_DISCLAIMER}",
                retrieval_count=0,
                insufficient_context=True,
                safety_category=decision.category.value,
                disclaimer=MEDICAL_DISCLAIMER,
            )

        # 5) Context building (budgeted, deduped, score-ordered).
        context, included = build_context(documents)

        # 6) Generation. LLM failures surface as LLMError → API 502.
        answer = self._generator.generate_answer(
            retrieval_query,
            context,
            conversation_summary=self._conversations.summary(conversation) or None,
        )

        # 7) Citation validation — fabricated citations are stripped.
        citation_result = validate_citations(answer, included)
        if not citation_result.valid:
            logger.warning(
                "citation issues: invalid=%s malformed=%s",
                citation_result.invalid_ids, citation_result.malformed,
            )
            answer = self._strip_invalid_citations(answer, citation_result.invalid_ids)
            citation_result = validate_citations(answer, included)

        # 8) Output safety validation.
        output = check_output(answer, answer_prefix=decision.answer_prefix)
        if not output.safe:
            logger.warning("output blocked: %s", "; ".join(output.reasons))
            final_answer = f"{_BLOCKED_OUTPUT_MESSAGE}\n\n{MEDICAL_DISCLAIMER}"
        else:
            final_answer = output.final_answer

        # 9) Record history (assistant answers are context, never evidence).
        self._conversations.add_turn(conversation, "user", clean_message)
        self._conversations.add_turn(conversation, "assistant", final_answer)

        insufficient = INSUFFICIENT_CONTEXT_MESSAGE.lower() in final_answer.lower()
        confidence = self._confidence(documents, citation_result.valid, insufficient)
        self._log(decision.category.value, len(documents), start)

        return ChatResult(
            conversation_id=conversation.id,
            answer=final_answer,
            sources=citation_result.citations,
            retrieval_count=len(documents),
            confidence=confidence,
            insufficient_context=insufficient,
            safety_category=decision.category.value,
            disclaimer=MEDICAL_DISCLAIMER,
        )

    def clear_conversation(self, conversation_id: str) -> None:
        self._conversations.clear(conversation_id)

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _strip_invalid_citations(answer: str, invalid_ids: list[int]) -> str:
        import re

        for cid in invalid_ids:
            answer = re.sub(rf"\[\s*{cid}\s*\]", "", answer)
        return re.sub(r"\s{2,}", " ", answer).strip()

    @staticmethod
    def _confidence(documents, citations_valid: bool, insufficient: bool) -> float:
        """Heuristic confidence: mean retrieval score, penalized for issues."""
        if insufficient or not documents:
            return 0.0
        mean_score = sum(d.score for d in documents) / len(documents)
        penalty = 1.0 if citations_valid else 0.8
        return round(min(mean_score * penalty, 1.0), 3)

    @staticmethod
    def _log(category: str, retrieval_count: int, start: float) -> None:
        logger.info(
            "chat turn complete",
            extra={
                "event": "chat_turn",
                "safety_category": category,
                "retrieval_count": retrieval_count,
                "latency_ms": round((time.time() - start) * 1000),
            },
        )


_service: ChatService | None = None


def get_chat_service() -> ChatService:
    global _service
    if _service is None:
        _service = ChatService()
    return _service
