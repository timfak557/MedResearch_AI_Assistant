#!/usr/bin/env python3
"""Explore the raw MedQuAD XML dataset (read-only).

Recursively inspects every XML file, reports structure and quality
statistics, and writes ``data/processed/exploration_report.json``.
The raw dataset is never modified.

Usage:
    python scripts/explore_medquad.py [--data-path PATH] [--output PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from defusedxml import ElementTree as SafeET

logger = get_logger("scripts.explore_medquad")


def _text(elem) -> str:  # type: ignore[no-untyped-def]
    return " ".join("".join(elem.itertext()).split()) if elem is not None else ""


def _local(tag: object) -> str:
    """Tag name without XML namespace."""
    t = str(tag)
    return t.rsplit("}", 1)[-1] if "}" in t else t


def explore(data_path: Path) -> dict:
    xml_files = sorted(data_path.rglob("*.xml"))

    tags: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    qtypes: Counter[str] = Counter()
    topics: Counter[str] = Counter()
    question_hashes: Counter[str] = Counter()
    pair_hashes: Counter[str] = Counter()
    answer_lengths: list[int] = []
    malformed: list[str] = []
    records = 0
    missing_questions = 0
    missing_answers = 0

    for path in xml_files:
        try:
            root = SafeET.parse(str(path)).getroot()
        except Exception as exc:  # malformed XML must not stop exploration
            malformed.append(f"{path}: {type(exc).__name__}")
            continue

        for elem in root.iter():
            tags[_local(elem.tag)] += 1

        source = root.get("source") or path.parent.name
        focus_elem = root.find(".//Focus")
        focus = _text(focus_elem)
        if focus:
            topics[focus] += 1

        qa_pairs = root.findall(".//QAPair") or [root]
        for pair in qa_pairs:
            q_elem = pair.find(".//Question")
            a_elem = pair.find(".//Answer")
            question = _text(q_elem)
            answer = _text(a_elem)

            records += 1
            sources[source] += 1
            if q_elem is not None and q_elem.get("qtype"):
                qtypes[q_elem.get("qtype", "")] += 1

            if not question:
                missing_questions += 1
            else:
                question_hashes[hashlib.sha256(question.lower().encode()).hexdigest()] += 1
            if not answer:
                missing_answers += 1
            else:
                answer_lengths.append(len(answer))
                pair_hashes[
                    hashlib.sha256((question + "\n" + answer).encode()).hexdigest()
                ] += 1

    duplicate_questions = sum(c - 1 for c in question_hashes.values() if c > 1)
    duplicate_pairs = sum(c - 1 for c in pair_hashes.values() if c > 1)

    return {
        "data_path": str(data_path),
        "xml_file_count": len(xml_files),
        "record_count": records,
        "xml_tags": dict(tags.most_common()),
        "sources": dict(sources.most_common()),
        "question_types": dict(qtypes.most_common()),
        "medical_topic_count": len(topics),
        "top_medical_topics": dict(topics.most_common(25)),
        "missing_questions": missing_questions,
        "missing_answers": missing_answers,
        "duplicate_questions": duplicate_questions,
        "duplicate_qa_pairs": duplicate_pairs,
        "malformed_xml_count": len(malformed),
        "malformed_xml_files": malformed[:50],
        "answer_length": {
            "min": min(answer_lengths) if answer_lengths else 0,
            "max": max(answer_lengths) if answer_lengths else 0,
            "avg": round(statistics.mean(answer_lengths), 1) if answer_lengths else 0,
            "count_with_answer": len(answer_lengths),
        },
    }


def main() -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)

    parser = argparse.ArgumentParser(description="Explore MedQuAD XML files (read-only).")
    parser.add_argument("--data-path", type=Path, default=settings.medquad_data_path)
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/exploration_report.json")
    )
    args = parser.parse_args()

    if not args.data_path.is_dir():
        logger.error("Dataset not found at %s — run scripts/download_medquad.py first", args.data_path)
        return 1

    logger.info("Exploring %s ...", args.data_path)
    report = explore(args.data_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    logger.info(
        "Explored %d XML files, %d records (%d malformed). Report: %s",
        report["xml_file_count"], report["record_count"],
        report["malformed_xml_count"], args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
