"""Tests for `deepcloak setup` checks."""

from deepcloak.setup import check_env, install_browser, run_setup


def test_check_env_warns_when_no_key():
    warnings = check_env(env={})
    assert warnings and "OPENAI_API_KEY" in warnings[0]


def test_check_env_ok_with_key():
    assert check_env(env={"ANTHROPIC_API_KEY": "x"}) == []


def test_install_browser_reports_missing_cloakbrowser():
    # cloakbrowser is not installed in the test venv.
    ok, msg = install_browser()
    assert ok is False
    assert "pip install deepcloak" in msg


def test_run_setup_returns_nonzero_when_browser_missing(capsys):
    code = run_setup()
    out = capsys.readouterr().out
    assert code == 1
    assert "Setup incomplete" in out
