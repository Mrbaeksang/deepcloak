"""Redirect checks in plain_get, against a real local HTTP server."""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytest.importorskip("requests")  # the fast CI job installs without dependencies

from deepcloak.stealth_downloader import plain_get
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
    with pytest.raises(RuntimeError):
        plain_get(f"{server}/loop", target_check=lambda _u: None)
