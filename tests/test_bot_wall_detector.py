"""Behavior tests for bot_wall_detector.classify() against committed fixtures."""

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepcloak.bot_wall_detector import classify, classify_html, from_response

FIXTURES = Path(__file__).parent / "fixtures" / "botwalls"


def _body(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "fixture,expected_kind",
    [
        ("cloudflare_challenge.html", "cloudflare"),
        ("datadome.html", "datadome"),
        ("turnstile.html", "turnstile"),
        ("recaptcha.html", "recaptcha"),
    ],
)
def test_detects_vendor_walls_from_body(fixture, expected_kind):
    wall = classify(status_code=200, headers={}, body=_body(fixture))
    assert wall is not None
    assert wall.kind == expected_kind
    assert wall.signal  # a human-readable reason is recorded for evidence


def test_normal_page_is_not_a_wall():
    assert classify(status_code=200, headers={"cf-ray": "abc"}, body=_body("normal.html")) is None


def test_cf_ray_header_alone_is_not_a_wall():
    # Cloudflare-fronted normal sites carry cf-ray — must not false-positive.
    assert classify(status_code=200, headers={"CF-RAY": "123"}, body="<html>ok</html>") is None


def test_429_is_rate_limit():
    wall = classify(status_code=429, headers={}, body="")
    assert wall is not None and wall.kind == "rate_limit"


def test_403_is_blocked():
    wall = classify(status_code=403, headers={}, body="Forbidden")
    assert wall is not None and wall.kind == "blocked"


def test_503_with_cloudflare_is_cloudflare():
    wall = classify(status_code=503, headers={"cf-ray": "x"}, body="error")
    assert wall is not None and wall.kind == "cloudflare"


def test_cf_mitigated_header_is_cloudflare():
    wall = classify(status_code=200, headers={"cf-mitigated": "challenge"}, body="<html></html>")
    assert wall is not None and wall.kind == "cloudflare"


def test_from_response_helper():
    from deepcloak.bot_wall_detector import from_response

    class Resp:
        status_code = 429
        headers = {"Retry-After": "60"}
        text = ""

    wall = from_response(Resp())
    assert wall is not None and wall.kind == "rate_limit"


@pytest.mark.parametrize(
    "name", ["cloudflare_challenge.html", "datadome.html", "recaptcha.html", "turnstile.html"]
)
def test_classify_html_flags_challenge_pages(name):
    html = _body(name)
    assert classify_html(html) is not None


def test_classify_html_passes_normal_page():
    html = _body("normal.html")
    assert classify_html(html) is None


def test_classify_html_passes_long_page_with_a_widget():
    html = (FIXTURES.parent / "pages/article_about_bot_walls.html").read_text(encoding="utf-8")
    assert classify(200, {}, html) is not None  # the plain detector would still escalate
    assert classify_html(html) is None


@pytest.mark.parametrize(
    "markup", ["<script>" * 20_000, "<" * 400_000, "<a " * 100_000], ids=["script", "lt", "attr"]
)
def test_classify_html_stays_fast_on_hostile_markup(markup):
    start = time.monotonic()
    classify_html("just a moment" + markup)
    assert time.monotonic() - start < 2


def test_script_text_does_not_count_as_readable():
    html = "<title>just a moment</title><script>" + "x" * 5000 + "</script>"
    assert classify_html(html) is not None


def test_long_successful_page_with_widget_is_not_a_wall():
    body = (FIXTURES.parent / "pages/article_about_bot_walls.html").read_text(encoding="utf-8")
    assert from_response(SimpleNamespace(status_code=200, headers={}, text=body)) is None


def test_blocked_status_is_a_wall_even_with_long_text():
    body = "<p>" + "text " * 1000 + "</p>"
    assert from_response(SimpleNamespace(status_code=403, headers={}, text=body)) is not None
