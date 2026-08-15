"""Question-aware chunking of MedQuAD records.

Rules (spec section 14):
- If the whole searchable record fits within the chunk size → one chunk.
- Otherwise the *answer* is split into semantic chunks (paragraph → sentence
  → word boundaries; never mid-word), each repeating the record metadata so
  every chunk is independently meaningful and retrievable.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from app.core.config import get_settings
from app.models.documents import (
    DocumentChunk,
    MedQuADRecord,
    build_searchable_text,
    deterministic_id,
)

#: Sentence boundary candidates, best first.
_BOUNDARY_HINTS = [". ", "! ", "? ", "; ", ", ", " "]


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text on natural boundaries; never inside a word."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Look for the latest natural boundary inside the window.
            window = text[start:end]
            cut = -1
            for hint in _BOUNDARY_HINTS:
                idx = window.rfind(hint)
                if idx > chunk_size // 2:  # keep chunks reasonably full
                    cut = idx + len(hint)
                    break
            if cut > 0:
                end = start + cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        # Step forward with overlap, snapped back to a word boundary.
        next_start = max(end - overlap, start + 1)
        while next_start > 0 and next_start < len(text) and not text[next_start - 1].isspace():
            next_start -= 1
        start = next_start
    return chunks


def chunk_record(
    record: MedQuADRecord,
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """Chunk one record according to the question-aware rules."""
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

    def make_chunk(text: str, index: int, total: int) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=deterministic_id(record.id, str(index)),
            parent_record_id=record.id,
            chunk_index=index,
            total_chunks=total,
            question=record.question,
            chunk_text=text,
            embed_text=build_searchable_text(
                focus=record.focus,
                question_type=record.question_type,
                question=record.question,
                answer=text,
            ),
            answer=record.answer,
            focus=record.focus,
            source=record.source,
            source_url=record.source_url,
            question_type=record.question_type,
            document_id=record.document_id,
            file_path=record.file_path,
        )

    # Short record → single chunk containing the full answer.
    if len(record.searchable_text) <= size:
        return [make_chunk(record.answer, 0, 1)]

    pieces = _split_text(record.answer, size, overlap)
    total = len(pieces)
    return [make_chunk(piece, i, total) for i, piece in enumerate(pieces)]


def chunk_records(
    records: Iterable[MedQuADRecord],
    *,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> Iterator[DocumentChunk]:
    """Stream chunks for many records."""
    for record in records:
        yield from chunk_record(record, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
