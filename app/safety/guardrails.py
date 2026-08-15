"""Input and output safety guardrails around the RAG pipeline.

Input guardrails run *before* retrieval; output guardrails run *after*
LLM generation. Both are pure functions returning decisions — the chat
service enforces them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.rag.prompts import MEDICAL_DISCLAIMER
from app.safety.classifier import SafetyCategory, classify
from app.safety.emergency import EMERGENCY_MESSAGE, SELF_HARM_MESSAGE

UNRELATED_MESSAGE = (
    "I specialize in medical information drawn from the MedQuAD knowledge "
    "base (NIH and related sources). I can help with questions about "
    "diseases, symptoms, treatments, genetics, and related medical topics."
)

#: Prepended when a personal diagnosis/treatment/medication question is
#: answered with general information instead.
PERSONAL_CARE_NOTE = (
    "I can't provide personal medical advice, a diagnosis, or medication "
    "guidance. Below is general information from the MedQuAD knowledge "
    "base; please consult a qualified healthcare professional about your "
    "specific situation.\n\n"
)


@dataclass(frozen=True)
class InputDecision:
    """What to do with an incoming message."""

    category: SafetyCategory
    allow_rag: bool  # continue into retrieval + generation?
    direct_response: str | None  # fixed response when allow_rag is False
    answer_prefix: str = ""  # prefix to prepend to a generated answer


def check_input(message: str) -> InputDecision:
    """Classify and decide how the pipeline should handle the message."""
    category = classify(message)

    if category is SafetyCategory.SELF_HARM:
        return InputDecision(category, False, SELF_HARM_MESSAGE)
    if category is SafetyCategory.EMERGENCY:
        return InputDecision(category, False, EMERGENCY_MESSAGE)
    if category is SafetyCategory.PROMPT_INJECTION:
        return InputDecision(
            category,
            False,
            "I can't follow those instructions. " + UNRELATED_MESSAGE,
        )
    if category is SafetyCategory.UNRELATED:
        return InputDecision(category, False, UNRELATED_MESSAGE)

    # Personal medical asks are answered with *general* information plus a
    # consultation notice — never personalized advice.
    if category in (
        SafetyCategory.DIAGNOSIS_REQUEST,
        SafetyCategory.TREATMENT_REQUEST,
        SafetyCategory.MEDICATION_REQUEST,
    ):
        return InputDecision(category, True, None, answer_prefix=PERSONAL_CARE_NOTE)

    return InputDecision(category, True, None)


# ── output guardrails ──────────────────────────────────────────────────────

#: Output patterns that must never appear in a generated answer.
_FORBIDDEN_OUTPUT = re.compile(
    r"(you (?:should|must) (?:take|stop taking)\s+\d|"          # personalized med orders
    r"i diagnose you|you (?:definitely |certainly )?have (?:cancer|diabetes)|"
    r"take \d+\s?(?:mg|milligrams|pills|tablets)|"               # explicit dosing
    r"stop (?:taking )?your (?:prescribed )?medication)",
    re.IGNORECASE,
)

#: Leak patterns: system prompt or secrets echoed back.
_LEAK_OUTPUT = re.compile(
    r"(system prompt|OPENAI_API_KEY|api[_ ]key\s*[:=]|AQ\.[A-Za-z0-9_\-]{20,}|"
    r"sk-[A-Za-z0-9_\-]{20,}|AIza[A-Za-z0-9_\-]{20,})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OutputDecision:
    safe: bool
    reasons: list[str]
    final_answer: str


def check_output(answer: str, *, answer_prefix: str = "") -> OutputDecision:
    """Validate a generated answer and attach prefix + disclaimer."""
    reasons: list[str] = []
    if _FORBIDDEN_OUTPUT.search(answer):
        reasons.append("personalized medical directive detected")
    if _LEAK_OUTPUT.search(answer):
        reasons.append("potential secret or prompt leak detected")

    if reasons:
        return OutputDecision(False, reasons, "")

    final = (answer_prefix + answer).strip()
    if MEDICAL_DISCLAIMER.lower() not in final.lower():
        final = f"{final}\n\n{MEDICAL_DISCLAIMER}"
    return OutputDecision(True, [], final)
