#!/usr/bin/env python3
"""Prepare MedQuAD: parse, clean, validate, dedup, chunk → JSONL.

Usage:
    python scripts/prepare_medquad.py [--input PATH] [--limit N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.exceptions import DatasetError
from app.core.logging import get_logger, setup_logging
from app.data.ingestion import prepare

logger = get_logger("scripts.prepare_medquad")


def main() -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)

    parser = argparse.ArgumentParser(description="Prepare the MedQuAD dataset for ingestion.")
    parser.add_argument("--input", type=Path, default=None, help="Raw dataset path.")
    parser.add_argument("--limit", type=int, default=None, help="Max raw records to process.")
    args = parser.parse_args()

    try:
        result = prepare(input_path=args.input, limit=args.limit)
    except DatasetError as exc:
        logger.error("Prepare failed: %s", exc)
        return 1
    logger.info("Prepared %d records / %d chunks. Report: %s",
                result.records, result.chunks, result.report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
