"""Citation extraction and validation.

Sources are numbered [1]..[N] in the order they appear in the context.
The final answer may only cite numbers that exist; anything else is a
fabricated citation and is reported.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.models.retrieval import RetrievedDocument

#: Well-formed citation markers: [1], [12] (optionally comma lists like [1, 2]).
_CITATION_RE = re.compile(r"\[(\d{1,3}(?:\s*,\s*\d{1,3})*)\]")
#: Malformed citation shapes we can detect, e.g. [source 1], [1a], [], [ref].
_MALFORMED_RE = re.compile(r"\[(?!\d{1,3}(?:\s*,\s*\d{1,3})*\])[^\[\]]{0,30}\]")
#: Sentences containing these cues make a "major claim" needing a citation.
_CLAIM_CUES = re.compile(
    r"\b(symptom|treat|cure|cause|risk|diagnos|therap|medic|disease|disorder|"
    r"syndrome|cancer|infect|prevent|dose|dosage|drug|patient|clinical|"
    r"studies|research)\w*\b",
    re.IGNORECASE,
)


class Citation(BaseModel):
    """A resolved citation in the final answer."""

    id: int
    record_id: str
    question: str
    source: str = ""
    source_url: str = ""
    focus: str = ""
    score: float = 0.0


class CitationValidation(BaseModel):
    """Structured result of validating an answer's citations."""

    valid: bool
    citations: list[Citation]
    cited_ids: list[int]
    invalid_ids: list[int]
    malformed: list[str]
    duplicate_ids: list[int]
    uncited_claim_sentences: list[str]


def extract_citation_ids(answer: str) -> list[int]:
    """All citation IDs referenced in the answer, in order of appearance."""
    ids: list[int] = []
    for match in _CITATION_RE.finditer(answer):
        for part in match.group(1).split(","):
            ids.append(int(part.strip()))
    return ids


def validate_citations(
    answer: str, sources: list[RetrievedDocument]
) -> CitationValidation:
    """Validate every citation in ``answer`` against the retrieved sources."""
    valid_range = range(1, len(sources) + 1)
    cited = extract_citation_ids(answer)

    invalid = sorted({cid for cid in cited if cid not in valid_range})
    malformed = [m.group(0) for m in _MALFORMED_RE.finditer(answer)]

    seen: set[int] = set()
    duplicates: list[int] = []
    for cid in cited:
        if cid in seen and cid not in duplicates:
            duplicates.append(cid)
        seen.add(cid)

    # Best-effort detection of major medical claims lacking any citation.
    uncited: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        s = sentence.strip()
        if not s or s.lower().startswith("disclaimer"):
            continue
        if _CLAIM_CUES.search(s) and not _CITATION_RE.search(s):
            uncited.append(s[:200])

    citations = [
        Citation(
            id=i,
            record_id=doc.record_id,
            question=doc.question,
            source=doc.source,
            source_url=doc.source_url,
            focus=doc.focus,
            score=doc.score,
        )
        for i, doc in enumerate(sources, start=1)
        if i in seen
    ]

    return CitationValidation(
        valid=not invalid and not malformed,
        citations=citations,
        cited_ids=sorted(seen),
        invalid_ids=invalid,
        malformed=malformed,
        duplicate_ids=duplicates,
        uncited_claim_sentences=uncited[:10],
    )
