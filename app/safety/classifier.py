"""Rule-based medical safety classifier.

Classifies incoming messages into safety categories before any retrieval
or generation happens. Deliberately dependency-free and fast; the category
drives guardrail behavior in :mod:`app.safety.guardrails`.

Priority order matters: emergency and self-harm outrank everything, and
prompt-injection outranks ordinary medical categories.
"""

from __future__ import annotations

import re
from enum import StrEnum


class SafetyCategory(StrEnum):
    GENERAL_MEDICAL_INFORMATION = "general_medical_information"
    MEDICAL_RESEARCH = "medical_research"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    TREATMENT_REQUEST = "treatment_request"
    MEDICATION_REQUEST = "medication_request"
    EMERGENCY = "emergency"
    SELF_HARM = "self_harm"
    UNRELATED = "unrelated"
    PROMPT_INJECTION = "prompt_injection"


_EMERGENCY = re.compile(
    r"\b(heart attack|stroke|can'?t breathe|cannot breathe|not breathing|"
    r"unconscious|unresponsive|seizure right now|severe bleeding|bleeding heavily|"
    r"overdos\w+|poison\w+|choking|anaphyla\w+|chest pain right now|"
    r"crushing chest pain|911|emergency room right now)\b",
    re.IGNORECASE,
)

_SELF_HARM = re.compile(
    r"\b(kill (?:myself|me)|suicid\w*|self[- ]harm|hurt myself|end my life|"
    r"want to die|cutting myself)\b",
    re.IGNORECASE,
)

_PROMPT_INJECTION = re.compile(
    r"(ignore (?:all|any|previous|prior|the) (?:instructions|rules|prompts?)|"
    r"disregard (?:the|your|all) (?:instructions|rules|system prompt)|"
    r"reveal (?:your|the) (?:system prompt|instructions|api key|configuration)|"
    r"show me (?:your|the) (?:system prompt|hidden prompt|api key)|"
    r"you are now|pretend (?:to be|you are)|jailbreak|"
    r"act as (?:an?|the) (?:unrestricted|uncensored)|developer mode|"
    r"print (?:your|the) (?:prompt|instructions|secrets?|api key))",
    re.IGNORECASE,
)

_DIAGNOSIS = re.compile(
    r"\b(do i have|does (?:my|this) .{0,40}mean i have|what (?:disease|condition|illness) do i have|"
    r"diagnose (?:me|my)|am i (?:sick|suffering|dying)|is this .{0,30}(?:cancer|diabetes|covid|serious)|"
    r"what'?s wrong with me|based on my symptoms)\b",
    re.IGNORECASE,
)

_MEDICATION = re.compile(
    r"\b(what (?:dose|dosage)|how (?:much|many) .{0,30}(?:mg|milligrams|pills|tablets)? ?(?:of|should i take)|"
    r"should i (?:take|stop taking|start taking|increase|decrease)|"
    r"prescribe|can i take .{0,40}(?:with|together)|double (?:my|the) dose|"
    r"stop (?:my|taking my) medicat\w+)\b",
    re.IGNORECASE,
)

_TREATMENT = re.compile(
    r"\b(how (?:do|can|should) i treat my|what should i do about my|"
    r"best treatment for my|how to cure my|treat this myself|home remedy for my)\b",
    re.IGNORECASE,
)

_RESEARCH = re.compile(
    r"\b(compare|difference between|studies|research|evidence|literature|"
    r"prevalence|incidence|epidemiolog\w+|mechanism of|pathophysiolog\w+)\b",
    re.IGNORECASE,
)

_MEDICAL_TERMS = re.compile(
    r"\b(disease|symptom\w*|treat\w*|cure\w*|cancer|diabetes|asthma|infect\w*|"
    r"syndrome|disorder|medicat\w+|virus|bacteria|gene|genetic|blood|heart|"
    r"lung|kidney|liver|brain|diagnos\w+|therap\w+|vaccine|surgery|chronic|"
    r"acute|patient|health|medical|clinical|drug|dose|prognosis|inherit\w+|"
    r"prevent\w*|screening|condition|illness|pain|injury|allerg\w+|"
    r"pathophysiolog\w+|epidemiolog\w+|"
    # common pharmacological suffixes (statins, antibiotics, etc.)
    r"\w*(?:statin|cillin|mycin|azole|prazole|formin)\w*)\b",
    re.IGNORECASE,
)


def classify(message: str) -> SafetyCategory:
    """Classify a user message into exactly one safety category."""
    text = (message or "").strip()
    if not text:
        return SafetyCategory.UNRELATED

    # Highest priority: acute risk.
    if _SELF_HARM.search(text):
        return SafetyCategory.SELF_HARM
    if _EMERGENCY.search(text):
        return SafetyCategory.EMERGENCY

    # Attacks on the system itself.
    if _PROMPT_INJECTION.search(text):
        return SafetyCategory.PROMPT_INJECTION

    # Personal medical asks that guardrails must reshape.
    if _DIAGNOSIS.search(text):
        return SafetyCategory.DIAGNOSIS_REQUEST
    if _MEDICATION.search(text):
        return SafetyCategory.MEDICATION_REQUEST
    if _TREATMENT.search(text):
        return SafetyCategory.TREATMENT_REQUEST

    # Informational medical content.
    if _MEDICAL_TERMS.search(text):
        if _RESEARCH.search(text):
            return SafetyCategory.MEDICAL_RESEARCH
        return SafetyCategory.GENERAL_MEDICAL_INFORMATION

    return SafetyCategory.UNRELATED
