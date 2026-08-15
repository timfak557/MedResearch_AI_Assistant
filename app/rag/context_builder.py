"""Builds the numbered evidence context handed to the LLM.

Higher-scoring documents come first, duplicate evidence is dropped, and the
configured context character budget is never exceeded.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.models.retrieval import RetrievedDocument


def _format_source(index: int, doc: RetrievedDocument) -> str:
    return (
        f"[SOURCE {index}]\n"
        f"Question:\n{doc.question}\n"
        f"Medical Topic:\n{doc.focus or 'Unknown'}\n"
        f"Question Type:\n{doc.question_type or 'Unknown'}\n"
        f"Source:\n{doc.source or 'Unknown'}\n"
        f"Source URL:\n{doc.source_url or 'N/A'}\n"
        f"Answer:\n{doc.answer}\n"
    )


def build_context(
    documents: list[RetrievedDocument],
    *,
    max_chars: int | None = None,
) -> tuple[str, list[RetrievedDocument]]:
    """Return (context_text, documents_actually_included).

    The returned document list is what citation validation must be checked
    against — sources dropped for budget reasons cannot be cited.
    """
    settings = get_settings()
    budget = max_chars or settings.max_context_chars

    ordered = sorted(documents, key=lambda d: d.score, reverse=True)

    included: list[RetrievedDocument] = []
    blocks: list[str] = []
    seen_answers: set[str] = set()
    used = 0

    for doc in ordered:
        # Drop duplicate evidence (same answer text already included).
        answer_key = doc.answer.strip().lower()[:500]
        if answer_key in seen_answers:
            continue

        block = _format_source(len(included) + 1, doc)
        if used + len(block) > budget:
            if not included:
                # Always include at least one (truncated) source.
                truncated = block[: budget - 100].rsplit(" ", 1)[0] + " …"
                blocks.append(truncated)
                included.append(doc)
                used = len(truncated)
            break
        blocks.append(block)
        included.append(doc)
        seen_answers.add(answer_key)
        used += len(block)

    return "\n".join(blocks), included
