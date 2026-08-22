"""Provider registry — the single source of truth for LLM providers.

One frozen spec per provider: how its credential is detected, what
local-deep-research calls it, where the credential lands in LDR's settings,
and how to list its models over each provider's *public* HTTP API. No LDR
internals are touched (ADR-0001's only seam stays ``_fetch_html``).

Pure module: data plus thin listing functions. ``requests`` is imported
lazily inside the real fetch so tests inject a fake transport instead.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

__all__ = [
    "ProviderError",
    "ProviderSpec",
    "PROVIDERS",
    "get",
    "detect",
    "list_models",
]


class ProviderError(Exception):
    """Raised for unknown providers or failed model listing."""


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    env_key: str | None  # credential env var; None when no credential exists
    keyless: bool  # runs locally / needs no API key to research
    default_model: str | None
    ldr_provider: str  # value local-deep-research expects in llm.provider
    ldr_key_setting: str | None  # settings key holding the credential in LDR
    models_kind: str  # response shape: openai | anthropic | gemini | ollama
    models_url: str | None = None  # absolute listing URL; None => derive from base_url
    default_base_url: str | None = None  # for local OpenAI-compatible servers


# Detection order matters: first env var present wins.
PROVIDERS: dict[str, ProviderSpec] = {
    spec.name: spec
    for spec in (
        ProviderSpec(
            name="openai",
            env_key="OPENAI_API_KEY",
            keyless=False,
            default_model="gpt-4.1",
            ldr_provider="openai",
            ldr_key_setting="llm.openai.api_key",
            models_kind="openai",
            models_url="https://api.openai.com/v1/models",
        ),
        ProviderSpec(
            name="anthropic",
            env_key="ANTHROPIC_API_KEY",
            keyless=False,
            default_model="claude-sonnet-4-6",
            ldr_provider="anthropic",
            ldr_key_setting="llm.anthropic.api_key",
            models_kind="anthropic",
            models_url="https://api.anthropic.com/v1/models",
        ),
        ProviderSpec(
            name="gemini",
            env_key="GEMINI_API_KEY",
            keyless=False,
            default_model="gemini-2.5-pro",
            # LDR has no "gemini"; its GoogleProvider serves Gemini.
            ldr_provider="google",
            ldr_key_setting="llm.google.api_key",
            models_kind="gemini",
            models_url="https://generativelanguage.googleapis.com/v1beta/models",
        ),
        ProviderSpec(
            name="openrouter",
            env_key="OPENROUTER_API_KEY",
            keyless=False,
            default_model="openai/gpt-4.1",
            # Native provider — never route it through openai_endpoint.
            ldr_provider="openrouter",
            ldr_key_setting="llm.openrouter.api_key",
            models_kind="openai",
            models_url="https://openrouter.ai/api/v1/models",
        ),
        ProviderSpec(
            name="ollama",
            env_key=None,
            keyless=True,
            default_model="llama3.1",
            ldr_provider="ollama",
            ldr_key_setting=None,
            models_kind="ollama",
            default_base_url="http://localhost:11434",
        ),
        ProviderSpec(
            name="lmstudio",
            env_key=None,
            keyless=True,
            default_model=None,  # server-defined
            ldr_provider="lmstudio",
            ldr_key_setting=None,
            models_kind="openai",
            default_base_url="http://localhost:1234/v1",
        ),
        ProviderSpec(
            name="llamacpp",
            env_key=None,
            keyless=True,
            default_model=None,  # server-defined
            ldr_provider="llamacpp",
            ldr_key_setting=None,
            models_kind="openai",
            default_base_url="http://localhost:8080/v1",
        ),
        ProviderSpec(
            name="openai-endpoint",
            env_key=None,
            keyless=True,
            default_model=None,  # server-defined
            ldr_provider="openai_endpoint",
            ldr_key_setting=None,
            models_kind="openai",
        ),
    )
}


def get(name: str) -> ProviderSpec:
    try:
        return PROVIDERS[name]
    except KeyError:
        raise ProviderError(
            f"Unknown provider {name!r}. Choose one of {sorted(PROVIDERS)}."
        ) from None


def detect(env: Mapping) -> str:
    """Auto-detect a provider from credentials present in ``env``."""
    for spec in PROVIDERS.values():
        if spec.env_key and env.get(spec.env_key):
            return spec.name
    wanted = ", ".join(s.env_key for s in PROVIDERS.values() if s.env_key)
    raise ProviderError(
        "No LLM credentials found. Set one of: "
        f"{wanted} (or pass --provider ollama for a local model)."
    )


def _fetch_json(url: str, headers: Mapping[str, str] | None, timeout: float = 20.0) -> dict:
    import requests

    r = requests.get(url, headers=dict(headers or {}), timeout=timeout)
    r.raise_for_status()
    return r.json()


def _models_url(spec: ProviderSpec, base_url: str | None) -> str:
    if spec.models_kind == "ollama":
        base = (base_url or spec.default_base_url or "").rstrip("/")
        if not base:
            raise ProviderError(f"provider {spec.name!r} needs a base URL to list models")
        return f"{base}/api/tags"
    if spec.models_url:
        return spec.models_url
    base = base_url or spec.default_base_url
    if not base:
        raise ProviderError(f"provider {spec.name!r} needs a base URL to list models")
    base = base.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return f"{base}/models"


def _headers_and_url(spec: ProviderSpec, api_key: str | None, url: str) -> tuple[str, dict]:
    if spec.models_kind == "anthropic":
        if not api_key:
            raise ProviderError("listing anthropic models needs ANTHROPIC_API_KEY")
        return url, {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    if spec.models_kind == "gemini":
        if not api_key:
            raise ProviderError("listing gemini models needs GEMINI_API_KEY")
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}key={api_key}", {}
    # OpenAI-compatible listings work without auth (OpenRouter's directory is
    # public; local servers ignore keys).
    return url, {"Authorization": f"Bearer {api_key}"} if api_key else (url, {})


def _parse_ids(spec: ProviderSpec, body: dict) -> list[str]:
    if spec.models_kind in ("openai", "anthropic"):
        ids = [m.get("id") for m in body.get("data") or []]
    elif spec.models_kind == "gemini":
        ids = [
            (m.get("name") or "").removeprefix("models/") for m in body.get("models") or []
        ]
    elif spec.models_kind == "ollama":
        ids = [m.get("name") for m in body.get("models") or []]
    else:  # pragma: no cover - kinds are registry-defined
        raise ProviderError(f"unsupported models kind {spec.models_kind!r}")
    return sorted({i for i in ids if i})


def list_models(
    provider: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 20.0,
    fetch: Callable[[str, Mapping[str, str] | None], dict] | None = None,
) -> list[str]:
    """List a provider's model ids, sorted. Network errors become ProviderError."""
    spec = get(provider)
    do_fetch = fetch or (lambda url, headers: _fetch_json(url, headers, timeout))
    url, headers = _headers_and_url(spec, api_key, _models_url(spec, base_url))
    try:
        body = do_fetch(url, headers)
    except Exception as exc:
        raise ProviderError(f"could not list models for {spec.name}: {exc}") from exc
    return _parse_ids(spec, body)
