"""Behavior tests for the provider registry and model listing.

Listing is tested against recorded response fixtures through an injected
fetch function — no live network, no LDR import.
"""

import pytest

from deepcloak.providers import ProviderError, detect, get, list_models

OPENAI_MODELS = {
    "data": [{"id": "gpt-4.1-mini"}, {"id": "gpt-4.1"}, {"id": "gpt-4.1"}]
}
ANTHROPIC_MODELS = {"data": [{"id": "claude-sonnet-4-5"}, {"id": "claude-sonnet-4-6"}]}
GEMINI_MODELS = {
    "models": [
        {"name": "models/gemini-2.0-flash"},
        {"name": "models/gemini-2.5-pro"},
    ]
}
OLLAMA_TAGS = {"models": [{"name": "llama3.1:latest"}, {"name": "qwen2.5:7b"}]}


def fake_fetch(response):
    calls: list[tuple[str, dict]] = []

    def fetch(url: str, headers: dict | None = None) -> dict:
        calls.append((url, headers or {}))
        return response

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def test_registry_holds_the_six_supported_providers():
    for name in ("openai", "anthropic", "gemini", "openrouter", "ollama", "openai-endpoint"):
        assert get(name).name == name


def test_unknown_provider_raises_with_choices():
    with pytest.raises(ProviderError) as exc:
        get("bogus")
    assert "openrouter" in str(exc.value)


def test_detection_order_matches_documented_precedence():
    env = {"ANTHROPIC_API_KEY": "b", "OPENAI_API_KEY": "a"}
    assert detect(env) == "openai"
    assert detect({"GEMINI_API_KEY": "g"}) == "gemini"
    assert detect({"OPENROUTER_API_KEY": "o"}) == "openrouter"
    with pytest.raises(ProviderError):
        detect({})


def test_gemini_spec_maps_to_ldr_google_provider():
    spec = get("gemini")
    assert spec.ldr_provider == "google"
    assert spec.ldr_key_setting == "llm.google.api_key"
    assert spec.env_key == "GEMINI_API_KEY"


def test_openrouter_spec_is_native_not_endpoint_detour():
    spec = get("openrouter")
    assert spec.ldr_provider == "openrouter"
    assert spec.ldr_key_setting == "llm.openrouter.api_key"


def test_list_models_openai_shape_sorted_and_deduped():
    fetch = fake_fetch(OPENAI_MODELS)
    models = list_models("openai", api_key="sk-x", fetch=fetch)
    assert models == ["gpt-4.1", "gpt-4.1-mini"]
    url, headers = fetch.calls[0]
    assert url.startswith("https://api.openai.com/v1/models")
    assert headers["Authorization"] == "Bearer sk-x"


def test_list_models_anthropic_uses_versioned_headers():
    fetch = fake_fetch(ANTHROPIC_MODELS)
    models = list_models("anthropic", api_key="ak-x", fetch=fetch)
    assert models == ["claude-sonnet-4-5", "claude-sonnet-4-6"]
    _, headers = fetch.calls[0]
    assert headers["x-api-key"] == "ak-x"
    assert headers["anthropic-version"]


def test_list_models_gemini_strips_model_prefix():
    fetch = fake_fetch(GEMINI_MODELS)
    models = list_models("gemini", api_key="g-key", fetch=fetch)
    assert models == ["gemini-2.0-flash", "gemini-2.5-pro"]
    url, _ = fetch.calls[0]
    assert "key=g-key" in url


def test_list_models_ollama_tags_and_custom_base_url():
    fetch = fake_fetch(OLLAMA_TAGS)
    models = list_models("ollama", base_url="http://gpu-box:11434", fetch=fetch)
    assert models == ["llama3.1:latest", "qwen2.5:7b"]
    url, _ = fetch.calls[0]
    assert url == "http://gpu-box:11434/api/tags"


def test_list_models_openai_endpoint_needs_base_url():
    with pytest.raises(ProviderError):
        list_models("openai-endpoint", fetch=fake_fetch(OPENAI_MODELS))


def test_list_models_openai_endpoint_lists_from_base_url():
    fetch = fake_fetch(OPENAI_MODELS)
    models = list_models(
        "openai-endpoint", base_url="http://localhost:8080/v1", fetch=fetch
    )
    assert models == ["gpt-4.1", "gpt-4.1-mini"]
    url, _ = fetch.calls[0]
    assert url == "http://localhost:8080/v1/models"
