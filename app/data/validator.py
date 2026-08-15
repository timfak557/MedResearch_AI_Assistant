"""Record validation for the ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.data.parser import RawRecord

#: Answers shorter than this are flagged (not rejected) as suspicious.
SUSPICIOUS_ANSWER_LENGTH = 40
#: Questions longer than this are almost certainly extraction errors.
MAX_QUESTION_LENGTH = 2000


@dataclass
class ValidationReport:
    """Aggregate outcome of validating a stream of records."""

    total: int = 0
    valid: int = 0
    missing_question: int = 0
    missing_answer: int = 0
    suspiciously_short_answers: int = 0
    malformed: int = 0
    rejected_examples: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "valid": self.valid,
            "missing_question": self.missing_question,
            "missing_answer": self.missing_answer,
            "suspiciously_short_answers": self.suspiciously_short_answers,
            "malformed": self.malformed,
            "rejected_examples": self.rejected_examples[:20],
        }


def validate_record(record: RawRecord, report: ValidationReport) -> bool:
    """Validate one cleaned record, updating the report.

    Returns True when the record should continue through the pipeline.
    """
    report.total += 1

    question = (record.question or "").strip()
    answer = (record.answer or "").strip()

    if not question:
        report.missing_question += 1
        _example(report, record, "missing/empty question")
        return False
    if not answer:
        report.missing_answer += 1
        _example(report, record, "missing/empty answer")
        return False
    if len(question) > MAX_QUESTION_LENGTH:
        report.malformed += 1
        _example(report, record, "question too long (extraction error)")
        return False

    if len(answer) < SUSPICIOUS_ANSWER_LENGTH:
        # Flag but keep: short answers can still be medically valid.
        report.suspiciously_short_answers += 1

    report.valid += 1
    return True


def _example(report: ValidationReport, record: RawRecord, reason: str) -> None:
    if len(report.rejected_examples) < 20:
        report.rejected_examples.append(f"{record.file_path}: {reason}")
