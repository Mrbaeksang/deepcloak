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


def test_gemini_overrides_target_ldrs_native_google_provider():
    s = resolve(cli={}, env={"GEMINI_API_KEY": "g"})
    o = s.to_ldr_overrides()
    assert o["llm.provider"] == "google"
    assert o["llm.google.api_key"] == "g"


def test_openrouter_overrides_target_ldrs_native_openrouter_provider():
    s = resolve(cli={"model": "openai/gpt-4.1"}, env={"OPENROUTER_API_KEY": "or"})
    o = s.to_ldr_overrides()
    assert o["llm.provider"] == "openrouter"
    assert o["llm.openrouter.api_key"] == "or"


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
    # DeepCloak always fetches full pages (its reason to exist), never snippet-only.
    assert env["LDR_SEARCH_SNIPPETS_ONLY"] == "false"


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


def test_openai_endpoint_requires_base_url():
    with pytest.raises(ConfigError) as exc:
        resolve(cli={"provider": "openai-endpoint"}, env={})
    assert "base-url" in str(exc.value)


def test_openai_endpoint_needs_no_key_and_maps_env():
    s = resolve(
        cli={
            "provider": "openai-endpoint",
            "base_url": "http://localhost:8080/v1",
            "model": "qwen",
        },
        env={},
    )
    assert s.provider == "openai-endpoint"
    assert s.api_key is None
    env = s.to_ldr_env()
    assert env["LDR_LLM_PROVIDER"] == "openai_endpoint"
    assert env["LDR_LLM_OPENAI_ENDPOINT_URL"] == "http://localhost:8080/v1"
    assert env["LDR_LLM_OPENAI_ENDPOINT_API_KEY"]  # non-empty
    assert env["LDR_LLM_MODEL"] == "qwen"


def test_openai_endpoint_base_url_from_env():
    s = resolve(
        cli={"provider": "openai-endpoint"},
        env={"LDR_LLM_OPENAI_ENDPOINT_URL": "http://localhost:8080/v1"},
    )
    assert s.base_url == "http://localhost:8080/v1"


def test_youcom_engine_is_valid_choice():
    s = resolve(cli={"engine": "youcom"}, env={"OPENAI_API_KEY": "x"})
    assert s.search_engine == "youcom"


def test_youcom_reads_api_key_from_env():
    s = resolve(
        cli={"engine": "youcom"},
        env={"OPENAI_API_KEY": "x", "YDC_API_KEY": "you-key"},
    )
    assert s.search_engine == "youcom"
    assert s.youcom_api_key == "you-key"


def test_youcom_works_keyless_when_no_api_key():
    s = resolve(cli={"engine": "youcom"}, env={"OPENAI_API_KEY": "x"})
    assert s.search_engine == "youcom"
    assert s.youcom_api_key is None  # keyless mode


def test_youcom_engine_from_env():
    s = resolve(
        cli={},
        env={"OPENAI_API_KEY": "x", "DEEPCLOAK_ENGINE": "youcom"},
    )
    assert s.search_engine == "youcom"


def test_config_file_fills_gaps_but_never_beats_flags_or_env():
    file = {"depth": "report", "stealth": "off", "model": "from-file"}

    s = resolve(cli={}, env={"OPENAI_API_KEY": "x"}, file=file)
    assert s.depth == "report"
    assert s.stealth_mode == "off"
    assert s.model == "from-file"

    s = resolve(
        cli={"model": "from-flag"},
        env={"OPENAI_API_KEY": "x", "DEEPCLOAK_MODEL": "from-env"},
        file=file,
    )
    assert s.model == "from-flag"

    s = resolve(cli={}, env={"OPENAI_API_KEY": "x", "DEEPCLOAK_MODEL": "from-env"}, file=file)
    assert s.model == "from-env"


def test_provider_in_config_file_disables_autodetection():
    s = resolve(cli={}, env={"ANTHROPIC_API_KEY": "b"}, file={"provider": "ollama"})
    assert s.provider == "ollama"
    assert s.api_key is None


def test_respect_robots_accepted_from_env_and_file():
    s = resolve(
        cli={},
        env={"OPENAI_API_KEY": "x", "DEEPCLOAK_RESPECT_ROBOTS": "true"},
    )
    assert s.respect_robots is True
    s = resolve(cli={}, env={"OPENAI_API_KEY": "x"}, file={"respect_robots": True})
    assert s.respect_robots is True


def test_load_config_file_reads_toml_and_ignores_unknown_keys(tmp_path):
    from deepcloak.config import load_config_file

    cfg = tmp_path / "config.toml"
    cfg.write_text('provider = "ollama"\nmodel = "llama3.1"\nbogus_key = 1\n')
    loaded = load_config_file(str(cfg))
    assert loaded == {"provider": "ollama", "model": "llama3.1"}
    assert load_config_file(str(tmp_path / "missing.toml")) == {}


def test_load_config_file_rejects_malformed_toml(tmp_path):
    import pytest

    from deepcloak.config import ConfigError, load_config_file

    bad = tmp_path / "broken.toml"
    bad.write_text("not [valid toml")
    with pytest.raises(ConfigError) as exc:
        load_config_file(str(bad))
    assert "not valid TOML" in str(exc.value)
