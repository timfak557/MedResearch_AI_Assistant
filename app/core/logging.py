"""Structured logging setup.

Produces JSON logs in production and human-readable logs in development.
A redaction filter guarantees API keys / authorization headers never reach
log output, and a ``request_id`` context variable ties log lines to requests.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

#: Patterns that must never appear in logs.
_REDACT_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[=:]\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(authorization\s*[=:]\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(bearer\s+)([A-Za-z0-9._\-]{8,})", re.IGNORECASE),
    # Google-style keys (AQ./AIza prefixes) and OpenAI-style keys.
    re.compile(r"\b(AQ\.[A-Za-z0-9_\-]{20,}|AIza[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9_\-]{20,})\b"),
]


def get_request_id() -> str:
    return _request_id_ctx.get()


def set_request_id(request_id: str | None = None) -> str:
    rid = request_id or uuid.uuid4().hex[:12]
    _request_id_ctx.set(rid)
    return rid


def _redact(text: str) -> str:
    for pattern in _REDACT_PATTERNS:
        text = pattern.sub(
            lambda m: (m.group(1) + "***") if m.lastindex and m.lastindex >= 2 else "***", text
        )
    return text


class RedactionFilter(logging.Filter):
    """Scrub secrets from every record before it is emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(str(record.getMessage()))
        record.args = ()
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    """Machine-parseable single-line JSON formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": round(time.time(), 3),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        for attr in ("endpoint", "latency_ms", "retrieval_latency_ms", "llm_latency_ms",
                     "retrieval_count", "safety_category", "event"):
            value = getattr(record, attr, None)
            if value is not None:
                payload[attr] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


class DevFormatter(logging.Formatter):
    """Readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", "-")
        base = f"{self.formatTime(record, '%H:%M:%S')} {record.levelname:<7} [{rid}] {record.name}: {record.getMessage()}"
        if record.exc_info and record.exc_info[0] is not None:
            base += f" ({record.exc_info[0].__name__})"
        return base


def setup_logging(level: str = "INFO", environment: str = "development") -> None:
    """Configure root logging once. Safe to call multiple times."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers.clear()

    # stderr, not stdout: the MCP stdio transport owns stdout, and mixing
    # log lines into it corrupts the JSON-RPC stream.
    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(RedactionFilter())
    handler.setFormatter(JsonFormatter() if environment == "production" else DevFormatter())
    root.addHandler(handler)

    # Quiet noisy third-party loggers; never let httpx log full URLs with keys.
    for noisy in ("httpx", "httpcore", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
