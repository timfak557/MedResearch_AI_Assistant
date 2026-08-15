"""Unit tests for MCP tools with a mocked search service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.mcp import tools


class TestMCPTools:
    def _mock_service(self, retrieved_docs):
        service = MagicMock()
        service.search_medical_knowledge.return_value = retrieved_docs
        service.list_sources.return_value = ["CancerGov", "GARD"]
        service.list_question_types.return_value = ["symptoms", "treatment"]
        service.statistics.return_value = {"total_chunks": 42, "qdrant_healthy": True}
        return service

    def test_search_tool(self, retrieved_docs):
        with patch.object(tools, "get_search_service", return_value=self._mock_service(retrieved_docs)):
            result = tools.search_medical_knowledge("asthma symptoms", top_k=3)
        assert len(result["results"]) == 3
        assert result["results"][0]["record_id"] == "rec-0"
        assert "score" in result["results"][0]

    def test_search_tool_invalid_input_returns_error(self):
        result = tools.search_medical_knowledge("")
        assert "error" in result

    def test_find_related_questions(self, retrieved_docs):
        with patch.object(tools, "get_search_service", return_value=self._mock_service(retrieved_docs)):
            result = tools.find_related_questions("what is asthma", top_k=3)
        assert len(result["related_questions"]) == 3
        assert "answer" not in result["related_questions"][0]  # related = questions only

    def test_compare_topics(self, retrieved_docs):
        with patch.object(tools, "get_search_service", return_value=self._mock_service(retrieved_docs)):
            result = tools.compare_medical_topics("asthma", "copd")
        assert result["topic_a"]["evidence"] and result["topic_b"]["evidence"]

    def test_list_tools(self, retrieved_docs):
        with patch.object(tools, "get_search_service", return_value=self._mock_service(retrieved_docs)):
            assert tools.list_medical_sources()["sources"] == ["CancerGov", "GARD"]
            assert tools.list_question_types()["question_types"] == ["symptoms", "treatment"]
            assert tools.get_system_statistics()["total_chunks"] == 42

    def test_get_medical_record_requires_id(self):
        assert "error" in tools.get_medical_record("")

    def test_unexpected_error_sanitized(self):
        broken = MagicMock()
        broken.search_medical_knowledge.side_effect = RuntimeError("secret internal detail")
        with patch.object(tools, "get_search_service", return_value=broken):
            result = tools.search_medical_knowledge("asthma")
        assert result == {"error": "Tool execution failed."}
