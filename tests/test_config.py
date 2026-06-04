"""Behavior tests for config.resolve() — provider auto-detection, overrides, mapping."""

import pytest

from deepcloak.config import ConfigError, resolve


def test_autodetects_openai_from_env():
    s = resolve(cli={}, env={"OPENAI_API_KEY": "sk-x"})
    assert s.provider == "openai"
    assert s.api_key == "sk-x"


def test_provider_precedence_prefers_openai():
    s = resolve(cli={}, env={"OPENAI_API_KEY": "a", "ANTHROPIC_API_KEY": "b"})
    assert s.provider == "openai"


def test_autodetects_anthropic_when_only_key_present():
    s = resolve(cli={}, env={"ANTHROPIC_API_KEY": "b"})
    assert s.provider == "anthropic"
    assert s.api_key == "b"


def test_autodetects_gemini():
    s = resolve(cli={}, env={"GEMINI_API_KEY": "g"})
    assert s.provider == "gemini"


def test_cli_provider_overrides_env_autodetect():
    s = resolve(
        cli={"provider": "anthropic"},
        env={"OPENAI_API_KEY": "a", "ANTHROPIC_API_KEY": "b"},
    )
    assert s.provider == "anthropic"
    assert s.api_key == "b"


def test_missing_key_raises_with_helpful_message():
    with pytest.raises(ConfigError) as exc:
        resolve(cli={}, env={})
    assert "OPENAI_API_KEY" in str(exc.value)


def test_ollama_needs_no_key():
    s = resolve(cli={"provider": "ollama"}, env={})
    assert s.provider == "ollama"
    assert s.api_key is None


def test_default_search_engine_is_duckduckgo():
    s = resolve(cli={}, env={"OPENAI_API_KEY": "x"})
    assert s.search_engine == "duckduckgo"


def test_search_engine_override():
    s = resolve(cli={"engine": "searxng"}, env={"OPENAI_API_KEY": "x"})
    assert s.search_engine == "searxng"


def test_default_stealth_mode_is_auto():
    s = resolve(cli={}, env={"OPENAI_API_KEY": "x"})
    assert s.stealth_mode == "auto"


def test_stealth_mode_override():
    s = resolve(cli={"stealth": "always"}, env={"OPENAI_API_KEY": "x"})
    assert s.stealth_mode == "always"


def test_respect_robots_defaults_off():
    s = resolve(cli={}, env={"OPENAI_API_KEY": "x"})
    assert s.respect_robots is False


def test_to_ldr_env_maps_provider_model_and_key():
    s = resolve(
        cli={"provider": "anthropic", "model": "claude-sonnet-4-6"},
        env={"ANTHROPIC_API_KEY": "b"},
    )
    env = s.to_ldr_env()
    assert env["LDR_LLM_PROVIDER"] == "anthropic"
    assert env["LDR_LLM_MODEL"] == "claude-sonnet-4-6"
    assert env["ANTHROPIC_API_KEY"] == "b"


def test_to_ldr_env_includes_searxng_url_when_set():
    s = resolve(
        cli={"engine": "searxng", "searxng_url": "http://localhost:11004"},
        env={"OPENAI_API_KEY": "x"},
    )
    env = s.to_ldr_env()
    assert env["LDR_SEARCH_ENGINE_WEB_SEARXNG_DEFAULT_PARAMS_INSTANCE_URL"] == "http://localhost:11004"


def test_invalid_stealth_mode_rejected():
    with pytest.raises(ConfigError):
        resolve(cli={"stealth": "bogus"}, env={"OPENAI_API_KEY": "x"})
