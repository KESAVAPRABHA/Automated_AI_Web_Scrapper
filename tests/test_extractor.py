"""Tests for ai/extractor.py (mocks the LLM so no API key needed)."""
import json
import pytest
from unittest.mock import MagicMock, patch


SAMPLE_PAGE_TEXT = """
CEO: Jane Doe
CTO: John Smith
Founded: 2015
Location: San Francisco, CA
"""

GOOD_JSON = json.dumps({"CEO": "Jane Doe", "CTO": "John Smith"})
FENCED_JSON = f"```json\n{GOOD_JSON}\n```"
BAD_JSON = "Sorry, I cannot extract that."


def _make_extractor(llm_return: str):
    """Return an AIExtractor whose LLM always returns *llm_return*."""
    with patch("ai.extractor.ChatGoogleGenerativeAI") as MockLLM, \
         patch("ai.extractor.GOOGLE_API_KEY", "fake-key"):
        mock_instance = MagicMock()
        MockLLM.return_value = mock_instance

        from ai.extractor import AIExtractor
        extractor = AIExtractor.__new__(AIExtractor)

        # Stub the chain to return llm_return directly
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = llm_return
        extractor._extraction_chain = mock_chain
        extractor._chat_chain = mock_chain
        return extractor


def test_extract_valid_json():
    """extract() parses clean JSON correctly."""
    extractor = _make_extractor(GOOD_JSON)
    result = extractor.extract(SAMPLE_PAGE_TEXT, ["CEO", "CTO"])
    assert result["CEO"] == "Jane Doe"
    assert result["CTO"] == "John Smith"


def test_extract_strips_markdown_fences():
    """extract() handles ```json ... ``` fences from the LLM."""
    extractor = _make_extractor(FENCED_JSON)
    result = extractor.extract(SAMPLE_PAGE_TEXT, ["CEO", "CTO"])
    assert result["CEO"] == "Jane Doe"


def test_extract_fallback_on_bad_json():
    """extract() returns {field: None} when JSON cannot be parsed."""
    extractor = _make_extractor(BAD_JSON)
    result = extractor.extract(SAMPLE_PAGE_TEXT, ["CEO", "CTO"])
    assert result == {"CEO": None, "CTO": None}


def test_chat_extract_returns_answer_and_data():
    """chat_extract() always returns 'answer' and 'data' keys."""
    payload = json.dumps({"answer": "Yes, there are openings.", "data": [{"role": "Frontend Engineer"}]})
    extractor = _make_extractor(payload)
    pages = [{"url": "https://acme.com", "text": "We are hiring frontend engineers."}]
    result = extractor.chat_extract("Any frontend openings?", pages, "https://acme.com")
    assert "answer" in result
    assert "data" in result
    assert isinstance(result["data"], list)


def test_chat_extract_plain_text_fallback():
    """chat_extract() wraps plain-text LLM output in answer key."""
    extractor = _make_extractor("We are hiring engineers.")
    pages = [{"url": "https://acme.com", "text": "We are hiring."}]
    result = extractor.chat_extract("Any openings?", pages, "https://acme.com")
    assert "answer" in result
    assert result["data"] == []
