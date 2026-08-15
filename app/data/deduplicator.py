"""Exact deduplication of QA pairs via SHA256 content hashes.

Only *exact* question+answer duplicates are removed. Records with similar
questions but different answers or different source information are kept.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from app.models.documents import MedQuADRecord


@dataclass
class DedupStats:
    raw_records: int = 0
    duplicates: int = 0

    @property
    def final_records(self) -> int:
        return self.raw_records - self.duplicates

    def as_dict(self) -> dict[str, int]:
        return {
            "raw_records": self.raw_records,
            "duplicates": self.duplicates,
            "final_records": self.final_records,
        }


def deduplicate(
    records: Iterable[MedQuADRecord], stats: DedupStats | None = None
) -> Iterator[MedQuADRecord]:
    """Yield records whose content_hash has not been seen before."""
    stats = stats if stats is not None else DedupStats()
    seen: set[str] = set()
    for record in records:
        stats.raw_records += 1
        if record.content_hash in seen:
            stats.duplicates += 1
            continue
        seen.add(record.content_hash)
        yield record
