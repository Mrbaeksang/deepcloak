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

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .fetch_router import fetch
from .stealth_downloader import plain_get, stealth_get

__all__ = ["build_stealth_retriever", "searxng_search", "youcom_search", "gather_hits"]


def gather_hits(hits: list, do_fetch: Callable, max_workers: int = 8) -> list:
    """Fetch hits concurrently (thread pool), returning results in input order.

    ``pool.map`` preserves order, so Evidence Records and documents keep a
    stable sequence regardless of which fetch finishes first.
    """
    if len(hits) <= 1:
        return [do_fetch(h) for h in hits]
    with ThreadPoolExecutor(max_workers=min(max_workers, len(hits))) as pool:
        return list(pool.map(do_fetch, hits))


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


def youcom_search(api_key: str | None, query: str, max_results: int = 8) -> list[dict]:
    """Query the You.com Search API and return [{url, title}] hits.

    Works with or without an API key. Without a key the keyless free profile
    is used (basic search only). With ``YDC_API_KEY`` the authenticated API
    returns richer results with higher rate limits.
    """
    import requests

    headers = {
        "User-Agent": "deepcloak/0.1.0",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["X-API-Key"] = api_key

    # The You.com Search API accepts POST with a JSON body.
    payload = {
        "query": query,
        "num_search_results": min(max_results, 20),
    }
    try:
        r = requests.post(
            "https://api.ydc-index.io/v1/search",
            json=payload,
            headers=headers,
            timeout=20,
        )
        # 402 (x402 Payment Required) from the keyless path means the free
        # quota is exhausted — fall back gracefully to an empty result set.
        if r.status_code == 402:
            return []
        r.raise_for_status()
    except requests.RequestException:
        return []

    data = r.json()
    out: list[dict] = []
    for hit in (data.get("hits") or [])[:max_results]:
        url = hit.get("url")
        if url:
            out.append({"url": url, "title": hit.get("title", "")})
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
    search_fn: Callable | None = None,
    evidence_log: Any = None,
    on_event: Any = None,
    respect_robots: bool = False,
    robots_ok: Any = None,
    proxy: str | None = None,
):
    """Construct a LangChain BaseRetriever backed by the stealth fetch path.

    ``search_fn`` defaults to ``searxng_search`` bound to ``searxng_url``.
    Pass a different callable (e.g. ``youcom_search``) to use an alternative
    search backend while keeping the same stealth-fetch pipeline.
    """
    from functools import partial

    from langchain_core.retrievers import BaseRetriever, Document  # type: ignore

    stealth_fetch = partial(stealth_get, proxy=proxy)
    do_search = search_fn or (lambda q, m: searxng_search(searxng_url, q, m))

    class StealthRetriever(BaseRetriever):
        model_config = {"arbitrary_types_allowed": True}

        def _process_hit(self, hit: dict):
            """Fetch one search hit through the stealth path; no side effects."""
            url = hit["url"]
            result = fetch(
                url,
                mode=mode,
                plain_fetch=plain_get,
                stealth_fetch=stealth_fetch,
                respect_robots=respect_robots,
                robots_ok=robots_ok,
            )
            doc = None
            if result.content:
                doc = Document(
                    page_content=_cap_content(
                        _extract_text(result.content), max_chars
                    ),
                    metadata={"url": url, "title": hit.get("title", "")},
                )
            return result.evidence, doc

        def _get_relevant_documents(self, query: str, *, run_manager=None):  # noqa: D401
            hits = do_search(query, max_results)
            outcomes = gather_hits(hits, self._process_hit)
            docs = []
            # Record and report in input order so Evidence sequences are stable.
            for evidence, doc in outcomes:
                if evidence_log is not None:
                    evidence_log.add(evidence)
                if on_event is not None:
                    on_event(evidence)
                if doc is not None:
                    docs.append(doc)
            return docs

    return StealthRetriever()
