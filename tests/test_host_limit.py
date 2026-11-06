"""HostLimiter under real thread concurrency, through the retriever's fetch pool."""

import threading
import time
from types import SimpleNamespace

import pytest

from deepcloak.host_limit import HostLimiter
from deepcloak.retriever import gather_hits


class _Tracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.active: dict[str, int] = {}
        self.peak: dict[str, int] = {}
        self.overall = 0
        self.peak_overall = 0

    def enter(self, host):
        with self.lock:
            self.active[host] = self.active.get(host, 0) + 1
            self.peak[host] = max(self.peak.get(host, 0), self.active[host])
            self.overall += 1
            self.peak_overall = max(self.peak_overall, self.overall)

    def leave(self, host):
        with self.lock:
            self.active[host] -= 1
            self.overall -= 1


def _fetcher(limiter, tracker, fail=()):
    def do_fetch(hit):
        host = hit["url"].split("/")[2]
        with limiter.slot(hit["url"]):
            tracker.enter(host)
            try:
                time.sleep(0.03)
                if hit["url"] in fail:
                    raise RuntimeError("boom")
                return hit["url"]
            finally:
                tracker.leave(host)

    return do_fetch


def test_one_host_gets_at_most_two_concurrent_requests_and_keeps_order():
    tracker = _Tracker()
    hits = [{"url": f"https://a.test/{i}"} for i in range(8)]
    out = gather_hits(hits, _fetcher(HostLimiter(), tracker))
    assert tracker.peak["a.test"] == 2
    assert out == [h["url"] for h in hits]


def test_different_hosts_still_run_in_parallel():
    tracker = _Tracker()
    hits = [{"url": f"https://h{i}.test/"} for i in range(8)]
    gather_hits(hits, _fetcher(HostLimiter(), tracker))
    assert tracker.peak_overall > 2


def test_host_names_are_case_insensitive():
    tracker = _Tracker()
    hits = [{"url": f"https://{h}/{i}"} for i, h in enumerate(["A.test", "a.TEST", "a.test"] * 2)]
    limiter = HostLimiter()

    def do_fetch(hit):
        with limiter.slot(hit["url"]):
            tracker.enter("a")
            time.sleep(0.03)
            tracker.leave("a")

    gather_hits(hits, do_fetch)
    assert tracker.peak["a"] == 2


def test_failed_request_releases_its_slot():
    limiter = HostLimiter(max_per_host=1)
    with pytest.raises(RuntimeError):
        with limiter.slot("https://a.test/1"):
            raise RuntimeError("boom")
    acquired = threading.Event()

    def next_request():
        with limiter.slot("https://a.test/2"):
            acquired.set()

    thread = threading.Thread(target=next_request, daemon=True)
    thread.start()
    assert acquired.wait(timeout=2)


def test_failing_fetch_does_not_block_the_rest():
    tracker = _Tracker()
    urls = [f"https://a.test/{i}" for i in range(4)]
    done = []
    fetcher = _fetcher(HostLimiter(), tracker, fail={urls[0]})

    def do_fetch(hit):
        try:
            done.append(fetcher(hit))
        except RuntimeError:
            done.append("failed")

    gather_hits([{"url": u} for u in urls], do_fetch)
    assert sorted(done) == sorted(["failed", *urls[1:]])


def test_malformed_url_does_not_raise():
    with HostLimiter().slot("http://[bad"):
        pass


def test_trailing_dot_shares_the_host_slot():
    limiter = HostLimiter(max_per_host=1)
    entered = threading.Event()

    def second():
        with limiter.slot("https://a.test./"):
            entered.set()

    with limiter.slot("https://a.test/"):
        thread = threading.Thread(target=second, daemon=True)
        thread.start()
        assert not entered.wait(timeout=0.2)
    assert entered.wait(timeout=2)


def test_shim_limits_concurrent_fetches_per_host():
    from deepcloak.evidence import EvidenceLog
    from deepcloak.ldr_shim import install

    class Downloader:
        pass

    tracker = _Tracker()

    def plain(_url):
        tracker.enter("93.184.216.34")
        time.sleep(0.03)
        tracker.leave("93.184.216.34")
        return SimpleNamespace(status_code=200, headers={}, text="<p>ok</p>")

    cls = install(evidence_log=EvidenceLog(), target_cls=Downloader, plain_fetch=plain,
                  stealth_fetch=lambda _u: "<p>ok</p>")
    urls = [f"https://93.184.216.34/{i}" for i in range(8)]
    gather_hits(urls, lambda u: cls._fetch_html(Downloader(), u))
    assert tracker.peak["93.184.216.34"] == 2


def test_retriever_limits_concurrent_fetches_per_host(monkeypatch):
    pytest.importorskip("langchain_core")
    from deepcloak import retriever

    tracker = _Tracker()

    def plain(_url, target_check=None):
        tracker.enter("93.184.216.34")
        time.sleep(0.03)
        tracker.leave("93.184.216.34")
        return SimpleNamespace(status_code=200, headers={}, text="<p>ok</p>")

    monkeypatch.setattr(retriever, "plain_get", plain)
    monkeypatch.setattr(
        retriever,
        "searxng_search",
        lambda *_a, **_k: [{"url": f"https://93.184.216.34/{i}", "title": ""} for i in range(8)],
    )
    retriever.build_stealth_retriever(searxng_url="http://search.test").invoke("q")
    assert tracker.peak["93.184.216.34"] == 2
