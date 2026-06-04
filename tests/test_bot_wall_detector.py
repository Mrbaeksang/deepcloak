"""Behavior tests for bot_wall_detector.classify() against committed fixtures."""

from pathlib import Path

import pytest

from deepcloak.bot_wall_detector import classify

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
