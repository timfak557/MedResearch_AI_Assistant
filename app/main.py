"""MedResearch AI Assistant — FastAPI application."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, health, search
from app.core.config import get_settings
from app.core.exceptions import MedResearchError
from app.core.logging import get_logger, set_request_id, setup_logging
from app.core.security import SECURE_HEADERS, sanitize_error_message

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)
    logger.info("MedResearch API starting (environment=%s)", settings.environment)
    yield
    logger.info("MedResearch API shutting down")


app = FastAPI(
    title="MedResearch AI Assistant API",
    description=(
        "Evidence-grounded medical information and research assistant built on "
        "the MedQuAD dataset. Answers are generated only from retrieved "
        "evidence, carry citations, and pass medical safety guardrails.\n\n"
        "**This service provides educational information only — it does not "
        "diagnose, prescribe, or replace professional medical advice.**"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Request ID, latency logging, and secure headers on every response."""
    rid = set_request_id(request.headers.get("X-Request-ID"))
    start = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    docs_page = request.url.path.startswith(("/docs", "/redoc", "/openapi.json"))
    for header, value in SECURE_HEADERS.items():
        if docs_page and header in ("Content-Security-Policy", "X-Frame-Options"):
            continue
        response.headers.setdefault(header, value)
    logger.info(
        "request complete",
        extra={
            "event": "http_request",
            "endpoint": f"{request.method} {request.url.path}",
            "latency_ms": round((time.time() - start) * 1000),
        },
    )
    return response


@app.exception_handler(MedResearchError)
async def medresearch_error_handler(request: Request, exc: MedResearchError) -> JSONResponse:
    """Map domain errors to sanitized HTTP responses (no stack traces)."""
    logger.warning("domain error on %s: %s", request.url.path, exc)
    from app.core.logging import get_request_id

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.public_message, "request_id": get_request_id()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled error on %s: %s", request.url.path, type(exc).__name__, exc_info=exc)
    from app.core.logging import get_request_id

    return JSONResponse(
        status_code=500,
        content={"error": sanitize_error_message(exc), "request_id": get_request_id()},
    )


app.include_router(health.router)
app.include_router(search.router)
app.include_router(chat.router)
