"""Shared pytest fixtures.

Tests never touch the production Qdrant collection: integration tests use
a dedicated ``medquad_test`` collection that is created and dropped per
session.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.documents import MedQuADRecord
from app.models.retrieval import RetrievedDocument

FIXTURES = Path(__file__).parent / "fixtures"
TEST_COLLECTION = "medquad_test"


@pytest.fixture()
def sample_xml() -> Path:
    return FIXTURES / "sample_document.xml"


@pytest.fixture()
def malformed_xml() -> Path:
    return FIXTURES / "malformed.xml"


@pytest.fixture()
def sample_record() -> MedQuADRecord:
    return MedQuADRecord.create(
        question="What is (are) Asthma ?",
        answer=(
            "Asthma is a chronic lung disease that inflames and narrows the "
            "airways. Common symptoms include wheezing, chest tightness, "
            "shortness of breath, and coughing."
        ),
        question_type="information",
        focus="Asthma",
        source="TestSource",
        source_url="https://example.org/asthma",
        document_id="0000042",
        file_path="tests/fixtures/sample_document.xml",
        folder="fixtures",
    )


@pytest.fixture()
def retrieved_docs() -> list[RetrievedDocument]:
    return [
        RetrievedDocument(
            record_id=f"rec-{i}",
            chunk_id=f"chunk-{i}",
            question=f"Question {i} about asthma symptoms?",
            answer=f"Answer {i}: asthma causes wheezing and coughing.",
            source="TestSource",
            source_url="https://example.org",
            focus="Asthma",
            question_type="symptoms",
            score=0.9 - i * 0.1,
        )
        for i in range(3)
    ]


class FakeGenerator:
    """Deterministic stand-in for the paid LLM."""

    def __init__(self, answer: str = "Asthma causes wheezing [1] and coughing [2].") -> None:
        self.answer = answer
        self.calls: list[dict] = []
        self.fail = False

    def generate_answer(self, query, context, **kwargs):  # type: ignore[no-untyped-def]
        from app.core.exceptions import LLMError

        self.calls.append({"query": query, "context": context})
        if self.fail:
            raise LLMError("simulated LLM outage")
        return self.answer


@pytest.fixture()
def fake_generator() -> FakeGenerator:
    return FakeGenerator()
