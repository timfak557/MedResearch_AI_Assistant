"""Integration tests using a dedicated test collection and live services.

Requires a running Qdrant and the local embedding model. The production
collection is never touched — everything happens in ``medquad_test``.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

from app.data.chunker import chunk_record  # noqa: E402
from app.data.cleaner import clean_record  # noqa: E402
from app.data.parser import parse_file  # noqa: E402
from app.data.validator import ValidationReport, validate_record  # noqa: E402
from app.embeddings.embedding_service import get_embedding_service  # noqa: E402
from app.models.documents import MedQuADRecord  # noqa: E402
from app.vectorstore.qdrant_service import QdrantService  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from tests.conftest import TEST_COLLECTION  # noqa: E402


@pytest.fixture(scope="module")
def qdrant() -> QdrantService:
    service = QdrantService(collection=TEST_COLLECTION)
    if not service.health_check():
        pytest.skip("Qdrant not available")
    yield service
    if service.collection_exists(TEST_COLLECTION):
        service.delete_collection(TEST_COLLECTION)


@pytest.fixture(scope="module")
def ingested(qdrant, request) -> QdrantService:
    """Parse the fixture XML and ingest it into the test collection."""
    sample = parse_file(
        __import__("pathlib").Path(__file__).parents[1] / "fixtures" / "sample_document.xml"
    )
    report = ValidationReport()
    records = []
    for raw in sample:
        cleaned = clean_record(raw)
        if validate_record(cleaned, report):
            records.append(
                MedQuADRecord.create(
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
            )
    assert len(records) == 2  # empty QA pair was rejected

    chunks = [chunk for record in records for chunk in chunk_record(record)]
    embedder = get_embedding_service()
    vectors = embedder.embed_texts([c.embed_text for c in chunks])

    if qdrant.collection_exists(TEST_COLLECTION):
        qdrant.delete_collection(TEST_COLLECTION)
    qdrant.create_collection(embedder.dimension)
    inserted = qdrant.upsert_documents(chunks, vectors)
    assert inserted == len(chunks)
    return qdrant


class TestQdrantService:
    def test_health_and_count(self, ingested):
        assert ingested.health_check()
        assert ingested.count() >= 2

    def test_duplicate_insertion_prevented(self, ingested):
        """Re-upserting identical chunks must not grow the collection."""
        before = ingested.count()
        sample = parse_file(
            __import__("pathlib").Path(__file__).parents[1] / "fixtures" / "sample_document.xml"
        )
        report = ValidationReport()
        records = []
        for raw in sample:
            cleaned = clean_record(raw)
            if validate_record(cleaned, report):
                records.append(MedQuADRecord.create(
                    question=cleaned.question, answer=cleaned.answer,
                    question_type=cleaned.question_type, focus=cleaned.focus,
                    source=cleaned.source, source_url=cleaned.source_url,
                    document_id=cleaned.document_id, file_path=cleaned.file_path,
                    folder=cleaned.folder,
                ))
        chunks = [c for r in records for c in chunk_record(r)]
        embedder = get_embedding_service()
        vectors = embedder.embed_texts([c.embed_text for c in chunks])
        ingested.upsert_documents(chunks, vectors)
        assert ingested.count() == before

    def test_semantic_search_finds_relevant(self, ingested):
        embedder = get_embedding_service()
        vector = embedder.embed_query("what are the treatments for asthma")
        points = ingested.search(vector, top_k=2, score_threshold=0.3)
        assert points
        assert points[0].payload["question_type"] == "treatment"

    def test_metadata_filter(self, ingested):
        embedder = get_embedding_service()
        vector = embedder.embed_query("asthma")
        flt = QdrantService.build_filter(question_type="information")
        points = ingested.search(vector, top_k=5, query_filter=flt, score_threshold=None)
        assert points and all(
            p.payload["question_type"] == "information" for p in points
        )

    def test_get_by_id(self, ingested):
        embedder = get_embedding_service()
        vector = embedder.embed_query("asthma")
        points = ingested.search(vector, top_k=1, score_threshold=None)
        found = ingested.get_by_id(str(points[0].id))
        assert found is not None


class TestAPIIntegration:
    @pytest.fixture(scope="class")
    def client(self):
        from app.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "medresearch-api"}

    def test_ready(self, client):
        response = client.get("/ready")
        assert response.status_code in (200, 503)
        body = response.json()
        assert set(body) == {"status", "qdrant", "embedding_model", "llm_configured"}

    def test_search_endpoint(self, client):
        response = client.post(
            "/api/v1/search",
            json={"query": "What are the symptoms of cancer?", "top_k": 3},
        )
        assert response.status_code == 200
        for item in response.json()["results"]:
            assert item["score"] >= 0.45

    def test_search_validation(self, client):
        assert client.post("/api/v1/search", json={"query": ""}).status_code == 422
        assert client.post("/api/v1/search", json={"query": "ok", "top_k": 999}).status_code == 422

    def test_docs_exposed(self, client):
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
