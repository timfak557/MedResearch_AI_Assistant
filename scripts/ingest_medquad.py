#!/usr/bin/env python3
"""Ingest prepared MedQuAD chunks into Qdrant.

Usage:
    python scripts/ingest_medquad.py [--input PATH] [--batch-size N]
                                     [--limit N] [--recreate] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.exceptions import DatasetError, EmbeddingError, VectorStoreError
from app.core.logging import get_logger, setup_logging
from app.data.ingestion import ingest

logger = get_logger("scripts.ingest_medquad")


def main() -> int:
    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)

    parser = argparse.ArgumentParser(description="Ingest MedQuAD chunks into Qdrant.")
    parser.add_argument("--input", type=Path, default=None, help="Chunks JSONL path.")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--limit", type=int, default=None, help="Max chunks to ingest.")
    parser.add_argument("--recreate", action="store_true",
                        help="Delete and recreate the collection first.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be ingested without writing.")
    args = parser.parse_args()

    try:
        result = ingest(
            chunks_path=args.input,
            batch_size=args.batch_size,
            limit=args.limit,
            recreate=args.recreate,
            dry_run=args.dry_run,
        )
    except (DatasetError, EmbeddingError, VectorStoreError) as exc:
        logger.error("Ingestion failed: %s", exc)
        return 1
    if not args.dry_run:
        logger.info("Ingested %d chunks into %s (dim=%d). Manifest: %s",
                    result.chunks_ingested, result.collection,
                    result.vector_dimension, result.manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
