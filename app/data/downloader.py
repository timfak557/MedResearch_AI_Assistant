"""MedQuAD dataset downloader.

Clones the official MedQuAD GitHub repository safely via ``git``:
- detects whether git is installed,
- skips the download when the dataset already exists (unless forced),
- validates that XML files are actually present,
- surfaces meaningful errors for network / permission failures.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import DatasetError
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Seconds allowed for the git clone before aborting.
CLONE_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a dataset download operation."""

    path: Path
    xml_file_count: int
    downloaded: bool  # False when an existing dataset was reused


def git_available() -> bool:
    """Return True when a usable ``git`` executable is on PATH."""
    return shutil.which("git") is not None


def count_xml_files(dataset_path: Path) -> int:
    """Recursively count XML files under ``dataset_path``."""
    if not dataset_path.is_dir():
        return 0
    return sum(1 for _ in dataset_path.rglob("*.xml"))


def dataset_exists(dataset_path: Path, *, min_xml_files: int = 1) -> bool:
    """True when the dataset directory exists and contains XML files."""
    return count_xml_files(dataset_path) >= min_xml_files


def download_medquad(
    *,
    repository: str | None = None,
    dataset_path: Path | None = None,
    force: bool = False,
) -> DownloadResult:
    """Download the MedQuAD repository if needed.

    Args:
        repository: Git URL (defaults to configured MEDQUAD_REPOSITORY).
        dataset_path: Target directory (defaults to MEDQUAD_DATA_PATH).
        force: Re-download even if the dataset already exists.

    Raises:
        DatasetError: git missing, clone failure, permission problems, or
            a clone that produced no XML files.
    """
    settings = get_settings()
    repo = repository or settings.medquad_repository
    path = Path(dataset_path or settings.medquad_data_path)

    if dataset_exists(path) and not force:
        count = count_xml_files(path)
        logger.info("MedQuAD already present at %s (%d XML files); skipping download", path, count)
        return DownloadResult(path=path, xml_file_count=count, downloaded=False)

    if not git_available():
        raise DatasetError(
            "git is not installed or not on PATH",
            public_message="Git is required to download the dataset.",
        )

    if path.exists() and force:
        logger.info("--force: removing existing dataset at %s", path)
        try:
            shutil.rmtree(path)
        except PermissionError as exc:
            raise DatasetError(f"cannot remove existing dataset: {exc}") from exc

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise DatasetError(f"cannot create dataset directory: {exc}") from exc

    logger.info("Cloning %s into %s (shallow)", repo, path)
    cmd = ["git", "clone", "--depth", "1", "--single-branch", repo, str(path)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise DatasetError(f"git clone timed out after {CLONE_TIMEOUT_SECONDS}s") from exc
    except OSError as exc:  # permissions, missing binary races, etc.
        raise DatasetError(f"failed to run git: {exc}") from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()[-500:]
        raise DatasetError(
            f"git clone failed (exit {proc.returncode}): {stderr}",
            public_message="Failed to download the MedQuAD dataset.",
        )

    count = count_xml_files(path)
    if count == 0:
        raise DatasetError(
            f"clone succeeded but no XML files found under {path}",
            public_message="Downloaded dataset contains no XML files.",
        )

    logger.info("Downloaded MedQuAD: %d XML files at %s", count, path)
    return DownloadResult(path=path, xml_file_count=count, downloaded=True)
