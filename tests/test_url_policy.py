"""Behavior tests for url_policy, with DNS injected."""

import pytest

from deepcloak.url_policy import blocked_reason


def _dns(*addresses):
    return lambda _host: list(addresses)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://localhost:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[fd00::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://0.0.0.0/",
    ],
)
def test_private_targets_are_blocked(url):
    assert blocked_reason(url, resolve=_dns("127.0.0.1")) is not None


def test_public_name_resolving_to_private_address_is_blocked():
    assert blocked_reason("https://rebind.test/", resolve=_dns("93.184.216.34", "10.0.0.1"))


def test_public_target_is_allowed():
    assert blocked_reason("https://example.com/a", resolve=_dns("93.184.216.34")) is None
    assert blocked_reason("https://93.184.216.34/") is None


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/", "no-scheme", "http://"])
def test_non_http_targets_are_blocked(url):
    assert blocked_reason(url) is not None


def test_unresolvable_name_is_left_to_the_fetch():
    def fail(_host):
        raise OSError("no such host")

    assert blocked_reason("https://nope.test/", resolve=fail) is None
