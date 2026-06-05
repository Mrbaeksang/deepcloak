"""StealthRetriever — the real integration seam.

A LangChain retriever that DeepCloak hands to local-deep-research's
``retrievers=`` API. For each search hit it fetches the *full page* through the
stealth ``fetch_router`` (plain → Escalate → Stealth Fetch), so the research
loop synthesises over Bypassed content — not snippets. Every fetch is recorded
as an Evidence Record.

LangChain is only imported here (it ships with local-deep-research), so the
pure modules and CI stay free of it.
"""

from __future__ import annotations

from typing import Any

from .fetch_router import fetch
from .stealth_downloader import plain_get, stealth_get

__all__ = ["build_stealth_retriever", "searxng_search"]


def searxng_search(base_url: str, query: str, max_results: int = 8) -> list[dict]:
    """Query a SearXNG instance and return [{url, title}] hits."""
    import requests

    r = requests.get(
        f"{base_url.rstrip('/')}/search",
        params={"q": query, "format": "json"},
        timeout=20,
        headers={"User-Agent": "deepcloak"},
    )
    r.raise_for_status()
    out: list[dict] = []
    for item in (r.json().get("results") or [])[:max_results]:
        url = item.get("url")
        if url:
            out.append({"url": url, "title": item.get("title", "")})
    return out


def _cap_content(text: str, max_chars: int | None) -> str:
    """Cap a document's text so many Bypassed pages still fit a model's context.

    A small local model (e.g. a 16k-context llama-server) overflows when the
    retriever feeds full pages into the synthesis prompt, so the report step
    never runs. ``max_chars`` of ``None``/``0`` disables the cap.
    """
    if max_chars and len(text) > max_chars:
        return text[:max_chars]
    return text


def _extract_text(html: str) -> str:
    """Best-effort readable-text extraction (reuses LDR's extractor if present)."""
    try:
        from local_deep_research.research_library.downloaders.extraction import (  # type: ignore
            extract_content,
        )

        text = extract_content(html, language="English", min_length=100)
        if text:
            return text
    except Exception:
        pass
    return html


def build_stealth_retriever(
    *,
    searxng_url: str,
    mode: str = "auto",
    max_results: int = 8,
    max_chars: int = 2000,
    evidence_log: Any = None,
    on_event: Any = None,
    respect_robots: bool = False,
    robots_ok: Any = None,
    proxy: str | None = None,
):
    """Construct a LangChain BaseRetriever backed by the stealth fetch path."""
    from functools import partial

    from langchain_core.retrievers import BaseRetriever, Document  # type: ignore

    stealth_fetch = partial(stealth_get, proxy=proxy)

    class StealthRetriever(BaseRetriever):
        model_config = {"arbitrary_types_allowed": True}

        def _get_relevant_documents(self, query: str, *, run_manager=None):  # noqa: D401
            docs = []
            for hit in searxng_search(searxng_url, query, max_results):
                url = hit["url"]
                result = fetch(
                    url,
                    mode=mode,
                    plain_fetch=plain_get,
                    stealth_fetch=stealth_fetch,
                    respect_robots=respect_robots,
                    robots_ok=robots_ok,
                )
                if evidence_log is not None:
                    evidence_log.add(result.evidence)
                if on_event is not None:
                    on_event(result.evidence)
                if result.content:
                    docs.append(
                        Document(
                            page_content=_cap_content(
                                _extract_text(result.content), max_chars
                            ),
                            metadata={"url": url, "title": hit.get("title", "")},
                        )
                    )
            return docs

    return StealthRetriever()
