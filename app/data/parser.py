"""Robust, security-hardened MedQuAD XML parser.

Design principles:
- No rigid schema assumption: field names are matched case-insensitively by
  local tag name, so namespaced or differently-nested variants still parse.
- Malformed files are logged and skipped — they never abort ingestion.
- ``defusedxml`` is used so external entities / DTD tricks are disabled.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as SafeET

from app.core.logging import get_logger

logger = get_logger(__name__)

#: Case-insensitive local tag names that may hold each logical field.
_QUESTION_TAGS = {"question"}
_ANSWER_TAGS = {"answer"}
_FOCUS_TAGS = {"focus", "topic", "medicaltopic"}
_PAIR_TAGS = {"qapair", "qapairitem", "pair"}


@dataclass
class RawRecord:
    """An unprocessed QA record exactly as extracted from XML."""

    question: str = ""
    answer: str = ""
    question_type: str = ""
    focus: str = ""
    source: str = ""
    source_url: str = ""
    document_id: str = ""
    file_path: str = ""
    folder: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def _local(tag: object) -> str:
    """Local tag name, lowercased, namespace stripped."""
    t = str(tag)
    if "}" in t:
        t = t.rsplit("}", 1)[-1]
    return t.lower()


def _text(elem: Any) -> str:
    """All inner text of an element, whitespace-normalized."""
    if elem is None:
        return ""
    return " ".join("".join(elem.itertext()).split())


def _find_first(elem: Any, names: set[str]) -> Any:
    """First descendant whose local name is in ``names``."""
    for child in elem.iter():
        if _local(child.tag) in names:
            return child
    return None


def _attr(elem: Any, *candidates: str) -> str:
    """First matching attribute value, case-insensitive."""
    if elem is None:
        return ""
    lowered = {k.lower(): v for k, v in elem.attrib.items()}
    for name in candidates:
        if name.lower() in lowered:
            return str(lowered[name.lower()]).strip()
    return ""


def parse_file(path: Path) -> list[RawRecord]:
    """Parse one MedQuAD XML file into raw records.

    Returns an empty list (and logs) when the file is malformed.
    """
    try:
        root = SafeET.parse(str(path)).getroot()
    except Exception as exc:
        logger.warning("Skipping malformed XML %s: %s", path, type(exc).__name__)
        return []

    source = _attr(root, "source") or path.parent.name
    source_url = _attr(root, "url", "source_url", "href")
    document_id = _attr(root, "id", "docid", "document_id") or path.stem
    focus = _text(_find_first(root, _FOCUS_TAGS))
    folder = path.parent.name

    records: list[RawRecord] = []

    pairs = [e for e in root.iter() if _local(e.tag) in _PAIR_TAGS]
    containers = pairs if pairs else [root]

    for container in containers:
        q_elem = _find_first(container, _QUESTION_TAGS)
        a_elem = _find_first(container, _ANSWER_TAGS)
        if q_elem is None and a_elem is None:
            continue
        records.append(
            RawRecord(
                question=_text(q_elem),
                answer=_text(a_elem),
                question_type=_attr(q_elem, "qtype", "type", "question_type"),
                focus=focus,
                source=source,
                source_url=source_url,
                document_id=document_id,
                file_path=str(path),
                folder=folder,
            )
        )

    if not records:
        logger.debug("No QA records found in %s", path)
    return records


def parse_directory(data_path: Path, *, limit: int | None = None) -> Iterator[RawRecord]:
    """Stream raw records from every XML file under ``data_path``.

    Malformed files are skipped; parsing never raises for individual files.
    """
    count = 0
    for path in sorted(data_path.rglob("*.xml")):
        for record in parse_file(path):
            yield record
            count += 1
            if limit is not None and count >= limit:
                return
