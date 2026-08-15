"""Core document models for MedQuAD records and chunks."""

from __future__ import annotations

import hashlib
import uuid

from pydantic import BaseModel, Field

#: Namespace used to derive deterministic UUIDs for records and chunks.
_MEDQUAD_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/abachaa/MedQuAD")


def content_hash(question: str, answer: str) -> str:
    """SHA256 over question + answer — used for exact deduplication."""
    return hashlib.sha256((question + answer).encode("utf-8")).hexdigest()


def deterministic_id(*parts: str) -> str:
    """Deterministic UUIDv5 derived from stable identifying parts."""
    return str(uuid.uuid5(_MEDQUAD_NAMESPACE, "|".join(parts)))


def build_searchable_text(
    *, focus: str, question_type: str, question: str, answer: str
) -> str:
    """Text representation that gets embedded (spec section 13)."""
    return (
        f"Medical Topic:\n{focus or 'Unknown'}\n"
        f"Question Type:\n{question_type or 'Unknown'}\n"
        f"Question:\n{question}\n"
        f"Answer:\n{answer}"
    )


class MedQuADRecord(BaseModel):
    """A cleaned, validated MedQuAD question-answer record."""

    id: str
    question: str
    answer: str
    question_type: str = ""
    focus: str = ""
    source: str = ""
    source_url: str = ""
    document_id: str = ""
    file_path: str = ""
    folder: str = ""
    content_hash: str = ""
    searchable_text: str = ""

    @classmethod
    def create(
        cls,
        *,
        question: str,
        answer: str,
        question_type: str = "",
        focus: str = "",
        source: str = "",
        source_url: str = "",
        document_id: str = "",
        file_path: str = "",
        folder: str = "",
    ) -> MedQuADRecord:
        """Build a record with deterministic id, hash, and searchable text."""
        chash = content_hash(question, answer)
        rid = deterministic_id(source or folder, document_id, chash)
        return cls(
            id=rid,
            question=question,
            answer=answer,
            question_type=question_type,
            focus=focus,
            source=source,
            source_url=source_url,
            document_id=document_id,
            file_path=file_path,
            folder=folder,
            content_hash=chash,
            searchable_text=build_searchable_text(
                focus=focus, question_type=question_type, question=question, answer=answer
            ),
        )


class DocumentChunk(BaseModel):
    """An embeddable chunk derived from a MedQuADRecord."""

    chunk_id: str
    parent_record_id: str
    chunk_index: int = Field(ge=0)
    total_chunks: int = Field(gt=0)
    question: str
    chunk_text: str  # the answer portion contained in this chunk
    embed_text: str  # full searchable text for this chunk (what gets embedded)
    answer: str = ""  # full answer retained for payload/display
    focus: str = ""
    source: str = ""
    source_url: str = ""
    question_type: str = ""
    document_id: str = ""
    file_path: str = ""
