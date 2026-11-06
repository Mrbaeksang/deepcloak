"""HostLimiter under real thread concurrency, through the retriever's fetch pool."""

import threading
import time

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
