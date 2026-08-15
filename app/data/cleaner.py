"""Conservative text cleaning for medical QA records.

Removes markup and encoding artifacts while preserving medical meaning:
terminology, numbers, abbreviations, and clinically relevant punctuation
are never altered.
"""

from __future__ import annotations

import html
import re
import unicodedata

from app.data.parser import RawRecord

#: Any remaining XML/HTML tags (parser already extracts text, this is a belt-and-braces pass).
_TAG_RE = re.compile(r"<[^>]{1,200}>")
#: Control characters (keep \n and \t handling to whitespace collapse).
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
#: Collapse runs of whitespace.
_WS_RE = re.compile(r"\s+")

#: Common mojibake sequences from mixed encodings.
_ENCODING_FIXES = {
    "â": "'",
    "â": "'",
    "â": '"',
    "â": '"',
    "â": "-",
    "â": "-",
    "Â ": " ",
    "﻿": "",
}


def clean_text(text: str) -> str:
    """Clean one text field without altering medical content."""
    if not text:
        return ""
    # Decode HTML entities (possibly double-encoded, e.g. &amp;apos;).
    text = html.unescape(html.unescape(text))
    for bad, good in _ENCODING_FIXES.items():
        text = text.replace(bad, good)
    text = unicodedata.normalize("NFC", text)
    text = _TAG_RE.sub(" ", text)
    text = _CONTROL_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return text.strip()


def clean_record(record: RawRecord) -> RawRecord:
    """Return a cleaned copy of a raw record (raw input is not mutated)."""
    return RawRecord(
        question=clean_text(record.question),
        answer=clean_text(record.answer),
        question_type=clean_text(record.question_type).lower(),
        focus=clean_text(record.focus),
        source=clean_text(record.source),
        source_url=record.source_url.strip(),
        document_id=record.document_id.strip(),
        file_path=record.file_path,
        folder=record.folder,
        extra=dict(record.extra),
    )
