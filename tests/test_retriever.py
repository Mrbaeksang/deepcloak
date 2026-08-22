"""Unit tests for the StealthRetriever per-document content cap.

The retriever itself needs ``langchain_core`` (only present when LDR is
installed), but the per-document cap is a pure helper we can test in isolation.
It is what keeps a research prompt within a small local model's context window:
without it, the retriever feeds full Bypassed pages into the synthesis prompt and
a 16k-context local model overflows before it can write the report.
"""

from deepcloak.retriever import _cap_content, gather_hits


def test_long_content_is_capped_to_max_chars():
    assert len(_cap_content("x" * 10_000, 6000)) == 6000


def test_short_content_is_left_untouched():
    text = "only a little readable text"
    assert _cap_content(text, 6000) == text


def test_zero_or_none_disables_the_cap():
    text = "y" * 10_000
    assert _cap_content(text, 0) == text
    assert _cap_content(text, None) == text


def test_gather_hits_fetches_concurrently():
    import threading

    n = 4
    barrier = threading.Barrier(n)

    def do_fetch(hit):
        barrier.wait(timeout=5)  # only releases if n fetches run at once
        return hit["i"] * 10

    hits = [{"i": i} for i in range(n)]
    assert gather_hits(hits, do_fetch) == [0, 10, 20, 30]


def test_gather_hits_preserves_input_order_despite_uneven_speeds():
    import time

    def do_fetch(hit):
        if hit["i"] == 0:
            time.sleep(0.05)  # slowest hit finishes last
        return f"doc-{hit['i']}"

    hits = [{"i": i} for i in range(6)]
    assert gather_hits(hits, do_fetch) == [f"doc-{i}" for i in range(6)]


def test_gather_hits_single_hit_stays_inline():
    assert gather_hits([{"u": "x"}], lambda h: h["u"]) == ["x"]
