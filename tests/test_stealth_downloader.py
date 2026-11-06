"""Redirect checks in plain_get, against a real local HTTP server."""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace

import pytest

pytest.importorskip("requests")  # the fast CI job installs without dependencies

from deepcloak import __version__
from deepcloak.stealth_downloader import check_redirect_chain, guard_page, plain_get
from deepcloak.url_policy import BlockedTarget

hits: list[str] = []


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        hits.append(self.path)
        if self.path == "/start":
            self.send_response(302)
            self.send_header("Location", "/secret")
            self.end_headers()
        elif self.path == "/loop":
            self.send_response(302)
            self.send_header("Location", "/loop")
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"secret")

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    hits.clear()
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_redirect_to_blocked_target_is_not_followed(server):
    def check(url):
        return "private network target" if url.endswith("/secret") else None

    with pytest.raises(BlockedTarget):
        plain_get(f"{server}/start", target_check=check)
    assert hits == ["/start"]


def test_allowed_redirect_is_followed(server):
    resp = plain_get(f"{server}/start", target_check=lambda _u: None)
    assert resp.text == "secret"
    assert hits == ["/start", "/secret"]


def test_redirect_loop_stops(server):
    with pytest.raises(RuntimeError, match="redirects"):
        plain_get(f"{server}/loop", target_check=lambda _u: None)


def _check(url):
    return "private network target" if "secret" in url else None


def test_guard_page_aborts_only_blocked_requests():
    calls = []

    class Route:
        def __init__(self, url):
            self.request = SimpleNamespace(url=url)
            self.url = url

        def abort(self):
            calls.append(("abort", self.url))

        def continue_(self):
            calls.append(("continue", self.url))

    page = SimpleNamespace(route=lambda _pattern, handler: page.__dict__.update(handler=handler))
    guard_page(page, _check)
    page.handler(Route("https://public.test/"))
    page.handler(Route("http://secret.test/"))
    assert calls == [("continue", "https://public.test/"), ("abort", "http://secret.test/")]


def test_redirect_chain_through_blocked_target_is_refused():
    first = SimpleNamespace(url="http://secret.test/", redirected_from=None)
    final = SimpleNamespace(url="https://public.test/", redirected_from=first)
    with pytest.raises(BlockedTarget):
        check_redirect_chain(SimpleNamespace(request=final), _check)


def test_clean_redirect_chain_and_missing_response_pass():
    final = SimpleNamespace(url="https://public.test/", redirected_from=None)
    check_redirect_chain(SimpleNamespace(request=final), _check)
    check_redirect_chain(None, _check)


def test_plain_fetch_identifies_deepcloak(monkeypatch):
    seen = {}

    def fake_get(url, timeout=None, headers=None, allow_redirects=True):
        seen.update(headers)
        return SimpleNamespace(is_redirect=False)

    monkeypatch.setattr("requests.get", fake_get)
    plain_get("https://93.184.216.34/")
    assert seen["User-Agent"].startswith(f"DeepCloak/{__version__} ")
