"""LLM answer generation via an OpenAI-compatible chat API.

The model name, base URL, and API key all come from configuration — nothing
is hard-coded. Transient errors are retried with exponential backoff, and
prompts are never written to logs.
"""

from __future__ import annotations

import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, LLMError
from app.core.logging import get_logger
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt

logger = get_logger(__name__)

_TRANSIENT = (APIConnectionError, APITimeoutError, RateLimitError)


class LLMGenerator:
    """Generates grounded answers from retrieved context."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        settings = get_settings()
        if not settings.llm_configured:
            raise ConfigurationError(
                "LLM not configured: set OPENAI_API_KEY and OPENAI_MODEL",
                public_message="The language model is not configured.",
            )
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                base_url=settings.openai_base_url or None,
                timeout=settings.llm_timeout_seconds,
                max_retries=0,  # tenacity handles retries
            )
        return self._client

    @retry(
        retry=retry_if_exception_type(_TRANSIENT),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        reraise=True,
    )
    def _chat(self, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        settings = get_settings()
        client = self._get_client()
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMError("LLM returned an empty response")
        return content.strip()

    def generate_answer(
        self,
        query: str,
        context: str,
        *,
        conversation_summary: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a grounded answer. Raises LLMError on failure.

        An empty context is a caller bug — the chat service short-circuits
        insufficient context before calling the LLM.
        """
        settings = get_settings()
        if not context.strip():
            raise LLMError(
                "generate_answer called with empty context",
                public_message="No evidence available to answer from.",
            )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(query, context, conversation_summary)},
        ]

        start = time.time()
        try:
            answer = self._chat(
                messages,
                temperature if temperature is not None else settings.llm_temperature,
                max_tokens or settings.llm_max_tokens,
            )
        except _TRANSIENT as exc:
            raise LLMError(f"LLM transient failure after retries: {type(exc).__name__}") from exc
        except APIStatusError as exc:
            raise LLMError(f"LLM API error: status={exc.status_code}") from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"LLM unexpected failure: {type(exc).__name__}") from exc

        latency_ms = round((time.time() - start) * 1000)
        # Structured logging: latency + sizes only, never prompt/answer content.
        logger.info(
            "llm generation complete",
            extra={"event": "llm_generation", "llm_latency_ms": latency_ms},
        )
        return answer


_generator: LLMGenerator | None = None


def get_generator() -> LLMGenerator:
    global _generator
    if _generator is None:
        _generator = LLMGenerator()
    return _generator
