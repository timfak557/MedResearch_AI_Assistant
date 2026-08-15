"""In-memory conversation store with TTL expiration and query rewriting.

Design constraints (spec section 25):
- Previous AI answers are NEVER used as medical evidence — history is kept
  only to rewrite follow-up questions into standalone queries.
- Every medical question triggers a fresh retrieval.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.exceptions import ConversationError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Conversation:
    id: str
    turns: list[Turn] = field(default_factory=list)
    last_active: float = field(default_factory=time.time)


#: Pronouns / referring phrases that signal a follow-up question.
_FOLLOWUP_RE = re.compile(
    r"\b(it|its|this|that|these|those|they|them|the (?:same|condition|disease|disorder))\b",
    re.IGNORECASE,
)
#: Very short questions are usually follow-ups ("And treatment?").
_SHORT_QUESTION_WORDS = 3


class ConversationService:
    """Thread-safe in-memory conversation manager."""

    def __init__(self, *, max_turns: int | None = None, ttl_seconds: int | None = None) -> None:
        settings = get_settings()
        self.max_turns = max_turns or settings.conversation_max_turns
        self.ttl_seconds = ttl_seconds or settings.conversation_ttl_seconds
        self._store: dict[str, Conversation] = {}
        self._lock = threading.Lock()

    # ── lifecycle ──────────────────────────────────────────────────────────
    def create(self) -> Conversation:
        conversation = Conversation(id=str(uuid.uuid4()))
        with self._lock:
            self._store[conversation.id] = conversation
        return conversation

    def get_or_create(self, conversation_id: str | None) -> Conversation:
        self._expire_stale()
        if conversation_id is None:
            return self.create()
        with self._lock:
            conversation = self._store.get(conversation_id)
        if conversation is None:
            # Unknown/expired ID → start fresh rather than failing the chat.
            return self.create()
        return conversation

    def clear(self, conversation_id: str) -> None:
        """Delete a conversation. Raises ConversationError when unknown."""
        with self._lock:
            if conversation_id not in self._store:
                raise ConversationError(f"conversation {conversation_id} not found")
            del self._store[conversation_id]

    def _expire_stale(self) -> None:
        cutoff = time.time() - self.ttl_seconds
        with self._lock:
            stale = [cid for cid, c in self._store.items() if c.last_active < cutoff]
            for cid in stale:
                del self._store[cid]
        if stale:
            logger.info("expired %d stale conversations", len(stale))

    # ── history ────────────────────────────────────────────────────────────
    def add_turn(self, conversation: Conversation, role: str, content: str) -> None:
        conversation.turns.append(Turn(role=role, content=content))
        conversation.last_active = time.time()
        # Keep at most max_turns user+assistant exchange pairs.
        max_len = self.max_turns * 2
        if len(conversation.turns) > max_len:
            del conversation.turns[: len(conversation.turns) - max_len]

    def summary(self, conversation: Conversation, *, max_chars: int = 1500) -> str:
        """Compact plain-text history (context for query rewriting only)."""
        lines = [f"{t.role}: {t.content[:300]}" for t in conversation.turns]
        text = "\n".join(lines)
        return text[-max_chars:]

    # ── query rewriting ────────────────────────────────────────────────────
    def rewrite_query(self, conversation: Conversation, query: str) -> str:
        """Rewrite a follow-up question into a standalone retrieval query.

        Heuristic, dependency-free approach: when the new question refers
        back (pronouns / very short), append the most recent medical topic
        mentioned by the user so retrieval has the missing subject.
        """
        query = query.strip()
        if not conversation.turns:
            return query

        is_followup = bool(_FOLLOWUP_RE.search(query)) or (
            len(query.split()) <= _SHORT_QUESTION_WORDS
        )
        if not is_followup:
            return query

        last_user_topic = self._last_topic(conversation)
        if not last_user_topic:
            return query

        # Replace a lone referring pronoun with the topic when possible.
        rewritten = _FOLLOWUP_RE.sub(last_user_topic, query, count=1)
        if rewritten == query:
            rewritten = f"{query} (regarding {last_user_topic})"
        logger.debug("rewrote follow-up query using topic %r", last_user_topic)
        return rewritten

    @staticmethod
    def _last_topic(conversation: Conversation) -> str:
        """Best-effort extraction of the last medical topic the user asked about."""
        stop = {
            "what", "is", "are", "the", "a", "an", "of", "for", "how", "does",
            "do", "can", "who", "when", "where", "why", "tell", "me", "about",
            "symptoms", "treatment", "causes", "risk", "factors",
        }
        for turn in reversed(conversation.turns):
            if turn.role != "user":
                continue
            words = re.findall(r"[A-Za-z][A-Za-z'\-]+", turn.content)
            content_words = [w for w in words if w.lower() not in stop]
            if content_words:
                return " ".join(content_words[-4:])
        return ""


_service: ConversationService | None = None


def get_conversation_service() -> ConversationService:
    global _service
    if _service is None:
        _service = ConversationService()
    return _service
