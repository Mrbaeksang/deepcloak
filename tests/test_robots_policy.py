"""robots.txt decisions, with the HTTP fetch injected."""

from types import SimpleNamespace

from deepcloak.evidence import EvidenceRecord
from deepcloak.fetch_router import fetch
from deepcloak.robots_policy import make_robots_check

PUBLIC = "https://93.184.216.34"
RULES = "User-agent: *\nDisallow: /private\n"


def _get(status=200, text=RULES, calls=None):
    def get(url, timeout=None, target_check=None):
        if calls is not None:
            calls.append(url)
        return SimpleNamespace(status_code=status, text=text)

    return get


def test_rules_are_applied():
    check = make_robots_check(_get())
    assert check(f"{PUBLIC}/private/a") is False
    assert check(f"{PUBLIC}/open") is True


def test_a_rule_for_deepcloak_is_applied():
    check = make_robots_check(_get(text="User-agent: DeepCloak\nDisallow: /\n"))
    assert check(f"{PUBLIC}/open") is False


def test_missing_file_allows():
    assert make_robots_check(_get(status=404))(f"{PUBLIC}/a") is True


def test_server_error_disallows():
    assert make_robots_check(_get(status=503))(f"{PUBLIC}/a") is False


def test_network_error_disallows():
    def fail(*_a, **_k):
        raise OSError("timed out")

    assert make_robots_check(fail)(f"{PUBLIC}/a") is False


def test_file_is_read_once_per_host():
    calls = []
    check = make_robots_check(_get(calls=calls))
    check(f"{PUBLIC}/a")
    check(f"{PUBLIC}/b")
    assert calls == [f"{PUBLIC}/robots.txt"]


def test_private_host_is_not_asked():
    calls = []
    assert make_robots_check(_get(calls=calls))("http://127.0.0.1:9/a") is True
    assert calls == []


def _must_not_run(_url):
    raise AssertionError("request sent")


def test_disallowed_url_is_not_requested_and_is_recorded():
    r = fetch(f"{PUBLIC}/private/a", plain_fetch=_must_not_run, stealth_fetch=_must_not_run,
              respect_robots=True, robots_ok=make_robots_check(_get()))
    assert r.content is None
    assert "robots.txt" in r.evidence.signal
    assert r.evidence.robots_ignored is False


def test_ignoring_robots_fetches_and_records_the_override():
    plain = lambda _u: SimpleNamespace(status_code=200, headers={}, text="<p>page</p>")  # noqa: E731
    r = fetch(f"{PUBLIC}/private/a", plain_fetch=plain, stealth_fetch=_must_not_run,
              respect_robots=False)
    assert r.content == "<p>page</p>"
    assert r.evidence.robots_ignored is True
    assert EvidenceRecord.__dataclass_fields__["robots_ignored"].default is False
