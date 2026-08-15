"""MedResearch MCP server (official MCP Python SDK).

Runs over stdio for local development:

    python -m app.mcp.server

For deployment, pass ``--transport streamable-http`` to serve Streamable
HTTP instead — the tool definitions are transport-agnostic.
"""

from __future__ import annotations

import argparse

from mcp.server.fastmcp import FastMCP

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.mcp import tools

mcp = FastMCP(
    "medresearch",
    instructions=(
        "Evidence-grounded medical information tools backed by the MedQuAD "
        "knowledge base (NIH sources). Results are educational information, "
        "not medical advice."
    ),
)


@mcp.tool()
def search_medical_knowledge(
    query: str,
    top_k: int = 5,
    source: str | None = None,
    focus: str | None = None,
    question_type: str | None = None,
) -> dict:
    """Semantic search over the MedQuAD medical knowledge base.

    Args:
        query: Medical question or keywords (1-2000 chars).
        top_k: Number of results, 1-20.
        source: Optional source filter (e.g. 'CancerGov', 'GARD').
        focus: Optional medical topic filter (e.g. 'Diabetes').
        question_type: Optional question type filter (e.g. 'symptoms').
    """
    return tools.search_medical_knowledge(query, top_k, source, focus, question_type)


@mcp.tool()
def get_medical_record(record_id: str) -> dict:
    """Fetch one full MedQuAD record (question, answer, source) by its record ID."""
    return tools.get_medical_record(record_id)


@mcp.tool()
def find_related_questions(question: str, top_k: int = 5) -> dict:
    """Find MedQuAD questions semantically related to the given question."""
    return tools.find_related_questions(question, top_k)


@mcp.tool()
def compare_medical_topics(topic_a: str, topic_b: str) -> dict:
    """Retrieve top evidence for two medical topics side by side for comparison."""
    return tools.compare_medical_topics(topic_a, topic_b)


@mcp.tool()
def list_medical_sources() -> dict:
    """List all source organizations present in the knowledge base."""
    return tools.list_medical_sources()


@mcp.tool()
def list_question_types() -> dict:
    """List all question types present in the knowledge base."""
    return tools.list_question_types()


@mcp.tool()
def get_system_statistics() -> dict:
    """Knowledge base statistics: chunk count, sources, model, Qdrant health."""
    return tools.get_system_statistics()


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)

    parser = argparse.ArgumentParser(description="MedResearch MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="stdio for local development, streamable-http for deployment.",
    )
    args = parser.parse_args()
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
