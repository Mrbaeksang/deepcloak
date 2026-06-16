"""Unit tests for the StealthRetriever per-document content cap.

The retriever itself needs ``langchain_core`` (only present when LDR is
installed), but the per-document cap is a pure helper we can test in isolation.
It is what keeps a research prompt within a small local model's context window:
without it, the retriever feeds full Bypassed pages into the synthesis prompt and
a 16k-context local model overflows before it can write the report.
"""

from unittest.mock import MagicMock

from deepcloak.retriever import _cap_content, tavily_search


def test_long_content_is_capped_to_max_chars():
    assert len(_cap_content("x" * 10_000, 6000)) == 6000


def test_short_content_is_left_untouched():
    text = "only a little readable text"
    assert _cap_content(text, 6000) == text


def test_zero_or_none_disables_the_cap():
    text = "y" * 10_000
    assert _cap_content(text, 0) == text
    assert _cap_content(text, None) == text


def test_tavily_search_returns_url_title_hits():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
        ]
    }
    hits = tavily_search(mock_client, "test query", max_results=5)
    mock_client.search.assert_called_once_with(query="test query", max_results=5)
    assert hits == [
        {"url": "https://a.com", "title": "A"},
        {"url": "https://b.com", "title": "B"},
    ]


def test_tavily_search_filters_items_missing_url():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"url": "https://a.com", "title": "A"},
            {"title": "No URL"},
            {"url": "", "title": "Empty URL"},
            {"url": "https://c.com", "title": "C"},
        ]
    }
    hits = tavily_search(mock_client, "q")
    assert hits == [
        {"url": "https://a.com", "title": "A"},
        {"url": "https://c.com", "title": "C"},
    ]
