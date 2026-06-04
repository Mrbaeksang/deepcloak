"""Tests for `deepcloak setup` checks (cloakbrowser injected for determinism)."""

from deepcloak.setup import check_env, install_browser, run_setup


class FakeCloak:
    @staticmethod
    def ensure_binary():
        return "/home/u/.cloakbrowser/chromium/chrome"


def test_check_env_warns_when_no_key():
    warnings = check_env(env={})
    assert warnings and "OPENAI_API_KEY" in warnings[0]


def test_check_env_ok_with_key():
    assert check_env(env={"ANTHROPIC_API_KEY": "x"}) == []


def test_install_browser_reports_missing_cloakbrowser():
    ok, msg = install_browser(cb=None)
    assert ok is False
    assert "pip install deepcloak" in msg


def test_install_browser_uses_ensure_binary_when_present():
    ok, msg = install_browser(cb=FakeCloak)
    assert ok is True
    assert "ensure_binary" in msg


def test_run_setup_returns_nonzero_when_browser_missing(capsys):
    code = run_setup(cb=None)
    out = capsys.readouterr().out
    assert code == 1
    assert "Setup incomplete" in out


def test_run_setup_ok_when_browser_present(capsys):
    code = run_setup(cb=FakeCloak)
    assert code == 0
    assert "ready" in capsys.readouterr().out.lower()
