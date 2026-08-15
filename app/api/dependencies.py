"""FastAPI dependencies — thin accessors over the shared service layer."""

from __future__ import annotations

from app.services.chat_service import ChatService, get_chat_service
from app.services.search_service import SearchService, get_search_service


def search_service() -> SearchService:
    return get_search_service()


def chat_service() -> ChatService:
    return get_chat_service()
