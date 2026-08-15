"""Unit tests: parser, cleaner, validator, deduplicator, chunker."""

from __future__ import annotations

from app.data.chunker import chunk_record
from app.data.cleaner import clean_record, clean_text
from app.data.deduplicator import DedupStats, deduplicate
from app.data.parser import RawRecord, parse_file
from app.data.validator import ValidationReport, validate_record
from app.models.documents import MedQuADRecord, build_searchable_text, content_hash


class TestParser:
    def test_parses_valid_document(self, sample_xml):
        records = parse_file(sample_xml)
        assert len(records) == 3  # includes the empty pair (validator rejects it later)
        first = records[0]
        assert first.question == "What is (are) Asthma ?"
        assert "chronic lung disease" in first.answer
        assert first.question_type == "information"
        assert first.focus == "Asthma"
        assert first.source == "TestSource"
        assert first.source_url == "https://example.org/asthma"
        assert first.document_id == "0000042"
        assert first.folder == "fixtures"

    def test_malformed_xml_returns_empty_not_raises(self, malformed_xml):
        assert parse_file(malformed_xml) == []

    def test_missing_file_returns_empty(self, tmp_path):
        assert parse_file(tmp_path / "nope.xml") == []


class TestCleaner:
    def test_removes_markup_and_entities(self):
        assert clean_text("Take &lt;b&gt;10 mg&lt;/b&gt; of  vitamin D3.") == "Take 10 mg of vitamin D3."

    def test_preserves_medical_content(self):
        text = "BP was 120/80 mmHg; HbA1c 6.5%. Type-2 diabetes (T2DM)."
        assert clean_text(text) == text

    def test_handles_apostrophe_entities(self):
        assert clean_text("Paget&apos;s disease") == "Paget's disease"

    def test_empty(self):
        assert clean_text("") == ""
        assert clean_text("   \n\t ") == ""

    def test_clean_record_does_not_mutate_input(self):
        raw = RawRecord(question=" q ", answer=" a ")
        cleaned = clean_record(raw)
        assert raw.question == " q " and cleaned.question == "q"


class TestValidator:
    def test_valid_record_passes(self):
        report = ValidationReport()
        ok = validate_record(RawRecord(question="What is asthma?", answer="A" * 100), report)
        assert ok and report.valid == 1

    def test_missing_answer_rejected(self):
        report = ValidationReport()
        assert not validate_record(RawRecord(question="Q?", answer=""), report)
        assert report.missing_answer == 1

    def test_missing_question_rejected(self):
        report = ValidationReport()
        assert not validate_record(RawRecord(question="", answer="An answer."), report)
        assert report.missing_question == 1

    def test_short_answer_flagged_but_kept(self):
        report = ValidationReport()
        assert validate_record(RawRecord(question="Q?", answer="Short answer."), report)
        assert report.suspiciously_short_answers == 1


class TestDeduplicator:
    def _record(self, question: str, answer: str, source: str = "S") -> MedQuADRecord:
        return MedQuADRecord.create(question=question, answer=answer, source=source)

    def test_exact_duplicates_removed(self):
        stats = DedupStats()
        records = [self._record("Q?", "A."), self._record("Q?", "A.")]
        result = list(deduplicate(records, stats))
        assert len(result) == 1 and stats.duplicates == 1

    def test_same_question_different_answer_kept(self):
        stats = DedupStats()
        records = [self._record("Q?", "Answer one."), self._record("Q?", "Answer two.")]
        assert len(list(deduplicate(records, stats))) == 2
        assert stats.duplicates == 0

    def test_stats(self):
        stats = DedupStats()
        list(deduplicate([self._record("Q?", "A."), self._record("Q?", "A.")], stats))
        assert stats.as_dict() == {"raw_records": 2, "duplicates": 1, "final_records": 1}


class TestModels:
    def test_content_hash_deterministic(self):
        assert content_hash("q", "a") == content_hash("q", "a")
        assert content_hash("q", "a") != content_hash("q", "b")

    def test_deterministic_ids(self, sample_record):
        again = MedQuADRecord.create(
            question=sample_record.question,
            answer=sample_record.answer,
            question_type=sample_record.question_type,
            focus=sample_record.focus,
            source=sample_record.source,
            source_url=sample_record.source_url,
            document_id=sample_record.document_id,
            file_path=sample_record.file_path,
            folder=sample_record.folder,
        )
        assert again.id == sample_record.id

    def test_searchable_text_format(self):
        text = build_searchable_text(
            focus="Asthma", question_type="symptoms", question="Q?", answer="A."
        )
        assert text.startswith("Medical Topic:\nAsthma\nQuestion Type:\nsymptoms")
        assert text.endswith("Answer:\nA.")


class TestChunker:
    def test_short_record_single_chunk(self, sample_record):
        chunks = chunk_record(sample_record)
        assert len(chunks) == 1
        assert chunks[0].total_chunks == 1
        assert chunks[0].chunk_text == sample_record.answer

    def test_long_record_multiple_chunks_with_metadata(self):
        long_answer = " ".join(
            f"Sentence number {i} about chronic asthma management and control." for i in range(120)
        )
        record = MedQuADRecord.create(
            question="What are the treatments for Asthma ?",
            answer=long_answer,
            focus="Asthma",
            source="TestSource",
        )
        chunks = chunk_record(record)
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == len(chunks)
            assert chunk.parent_record_id == record.id
            assert chunk.question == record.question
            assert chunk.focus == "Asthma"

    def test_never_splits_mid_word(self):
        answer = ("Pneumonoultramicroscopicsilicovolcanoconiosis " * 60).strip()
        record = MedQuADRecord.create(question="Q?", answer=answer)
        for chunk in chunk_record(record):
            for word in chunk.chunk_text.split():
                assert word == "Pneumonoultramicroscopicsilicovolcanoconiosis"

    def test_chunk_ids_deterministic(self, sample_record):
        first = chunk_record(sample_record)
        second = chunk_record(sample_record)
        assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
