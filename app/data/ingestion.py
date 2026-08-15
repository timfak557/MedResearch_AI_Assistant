"""End-to-end ingestion pipeline: XML → records → chunks → Qdrant.

Two stages, matching the CLI scripts:
- :func:`prepare` : parse → clean → validate → dedup → searchable text →
  chunk → JSONL files + processing report.
- :func:`ingest`  : read chunk JSONL → embed → upsert into Qdrant +
  ingestion manifest.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import DatasetError
from app.core.logging import get_logger
from app.data.chunker import chunk_record
from app.data.cleaner import clean_record
from app.data.deduplicator import DedupStats, deduplicate
from app.data.parser import parse_directory
from app.data.validator import ValidationReport, validate_record
from app.embeddings.embedding_service import get_embedding_service
from app.models.documents import DocumentChunk, MedQuADRecord
from app.vectorstore.qdrant_service import get_qdrant_service

logger = get_logger(__name__)


@dataclass
class PrepareResult:
    records: int
    chunks: int
    report_path: Path


def prepare(
    *,
    input_path: Path | None = None,
    limit: int | None = None,
) -> PrepareResult:
    """Run parse → clean → validate → dedup → chunk, writing JSONL outputs."""
    settings = get_settings()
    data_path = Path(input_path or settings.medquad_data_path)
    if not data_path.is_dir():
        raise DatasetError(f"dataset not found at {data_path}; run download first")

    records_path = Path(settings.processed_data_path)
    chunks_path = Path(settings.chunks_data_path)
    records_path.parent.mkdir(parents=True, exist_ok=True)

    validation = ValidationReport()
    dedup_stats = DedupStats()

    def valid_records():
        for raw in parse_directory(data_path, limit=limit):
            cleaned = clean_record(raw)
            if not validate_record(cleaned, validation):
                continue
            yield MedQuADRecord.create(
                question=cleaned.question,
                answer=cleaned.answer,
                question_type=cleaned.question_type,
                focus=cleaned.focus,
                source=cleaned.source,
                source_url=cleaned.source_url,
                document_id=cleaned.document_id,
                file_path=cleaned.file_path,
                folder=cleaned.folder,
            )

    n_records = 0
    n_chunks = 0
    start = time.time()
    with records_path.open("w", encoding="utf-8") as rf, chunks_path.open("w", encoding="utf-8") as cf:
        for record in deduplicate(valid_records(), dedup_stats):
            rf.write(record.model_dump_json() + "\n")
            n_records += 1
            for chunk in chunk_record(record):
                cf.write(chunk.model_dump_json() + "\n")
                n_chunks += 1
            if n_records % 5000 == 0:
                logger.info("prepared %d records (%d chunks) ...", n_records, n_chunks)

    report = {
        "input_path": str(data_path),
        "validation": validation.as_dict(),
        "deduplication": dedup_stats.as_dict(),
        "records_written": n_records,
        "chunks_written": n_chunks,
        "records_path": str(records_path),
        "chunks_path": str(chunks_path),
        "elapsed_seconds": round(time.time() - start, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    report_path = records_path.parent / "processing_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    logger.info(
        "prepare done: %d raw → %d valid → %d unique records, %d chunks",
        validation.total, validation.valid, n_records, n_chunks,
    )
    return PrepareResult(records=n_records, chunks=n_chunks, report_path=report_path)


@dataclass
class IngestResult:
    chunks_ingested: int
    collection: str
    vector_dimension: int
    manifest_path: Path


def _dataset_hash(chunks_path: Path) -> str:
    """Stable hash over the prepared chunk file (identifies dataset version)."""
    h = hashlib.sha256()
    with chunks_path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ingest(
    *,
    chunks_path: Path | None = None,
    batch_size: int = 256,
    limit: int | None = None,
    recreate: bool = False,
    dry_run: bool = False,
) -> IngestResult:
    """Embed prepared chunks and upsert them into Qdrant."""
    settings = get_settings()
    path = Path(chunks_path or settings.chunks_data_path)
    if not path.is_file():
        raise DatasetError(f"chunks file not found at {path}; run prepare first")

    embedder = get_embedding_service()
    qdrant = get_qdrant_service()

    if dry_run:
        n = sum(1 for _ in path.open(encoding="utf-8"))
        n = min(n, limit) if limit else n
        logger.info("[dry-run] would ingest %d chunks into %s", n, qdrant.collection)
        return IngestResult(n, qdrant.collection, -1, Path("/dev/null"))

    if recreate and qdrant.collection_exists():
        logger.warning("--recreate: deleting existing collection %s", qdrant.collection)
        qdrant.delete_collection()

    dimension = embedder.dimension  # loads model, detects dim dynamically
    qdrant.create_collection(dimension)

    total = 0
    parent_ids: set[str] = set()
    batch: list[DocumentChunk] = []
    start = time.time()

    def flush(batch: list[DocumentChunk]) -> int:
        if not batch:
            return 0
        vectors = embedder.embed_texts([c.embed_text for c in batch])
        return qdrant.upsert_documents(batch, vectors, batch_size=batch_size)

    with path.open(encoding="utf-8") as f:
        for line in f:
            if limit is not None and total + len(batch) >= limit:
                break
            chunk = DocumentChunk.model_validate_json(line)
            parent_ids.add(chunk.parent_record_id)
            batch.append(chunk)
            if len(batch) >= batch_size:
                total += flush(batch)
                batch = []
                if total % (batch_size * 20) == 0:
                    rate = total / max(time.time() - start, 1e-6)
                    logger.info("ingested %d chunks (%.0f/s)", total, rate)
    total += flush(batch)

    manifest = {
        "dataset_hash": _dataset_hash(path),
        "embedding_model": embedder.model_name,
        "vector_dimension": dimension,
        "collection": qdrant.collection,
        "number_of_records": len(parent_ids),
        "number_of_chunks": total,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest_path = path.parent / "ingestion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(
        "ingest done: %d chunks (%d records) → collection %s in %.1fs",
        total, len(parent_ids), qdrant.collection, time.time() - start,
    )
    return IngestResult(total, qdrant.collection, dimension, manifest_path)
