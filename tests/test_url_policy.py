"""Behavior tests for url_policy, with DNS injected."""

import pytest

from deepcloak.url_policy import blocked_reason, target_policy


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


@pytest.mark.parametrize(
    "url",
    [
        "http://%31%32%37.0.0.1/",
        "http://127.0.0.1:80\\@evil.test/",
        "http://evil.test@127.0.0.1/",
        "http://0177.0.0.1/",
        "http://0x7f.1/",
        "http://2130706433/",
        "http://127.0.0.1./",
        "http://localhost./",
        "http://１２７.0.0.1/",
        "http://exa mple.test/",
        "http://[64:ff9b::7f00:1]/",
        "http://[::7f00:1]/",
        "http://[::ffff:0:7f00:1]/",
        "http://[2002:7f00:1::]/",
    ],
)
def test_host_forms_that_reach_private_targets_are_blocked(url):
    assert blocked_reason(url, resolve=_dns("127.0.0.1")) is not None


@pytest.mark.parametrize("url", ["http://[bad", "http://" + "a" * 64 + ".com/", "http://a..com/"])
def test_malformed_urls_are_blocked_without_raising(url):
    assert blocked_reason(url) is not None


def test_resolver_unicode_error_is_blocked_without_raising():
    def fail(_host):
        raise UnicodeError("label too long")

    assert blocked_reason("https://long.test/", resolve=fail) == "invalid URL"


def test_public_embedded_ipv4_is_allowed():
    assert blocked_reason("http://[64:ff9b::5db8:d822]/") is None


def test_allow_private_keeps_other_rules():
    policy = target_policy(allow_private_urls=True)
    assert policy("http://127.0.0.1:8080/") is None
    assert policy("http://192.168.1.1/") is None
    assert policy("file:///etc/passwd") is not None
    assert policy("http://[bad") is not None
    assert target_policy()("http://127.0.0.1:8080/") is not None
