#!/usr/bin/env python3
"""Download the MedQuAD dataset.

Usage:
    python scripts/download_medquad.py [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.exceptions import DatasetError
from app.core.logging import get_logger, setup_logging
from app.data.downloader import download_medquad

logger = get_logger("scripts.download_medquad")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the MedQuAD dataset from GitHub.")
    parser.add_argument("--force", action="store_true", help="Re-download even if present.")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)

    try:
        result = download_medquad(force=args.force)
    except DatasetError as exc:
        logger.error("Download failed: %s", exc)
        return 1

    action = "Downloaded" if result.downloaded else "Reusing existing"
    logger.info("%s dataset: %s (%d XML files)", action, result.path, result.xml_file_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
