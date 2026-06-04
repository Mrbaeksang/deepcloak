"""Resolve runtime settings from CLI args + environment.

Pure module: ``resolve()`` takes plain mappings and returns a frozen ``Settings``.
No I/O, no imports of the heavy upstreams — so it is trivially testable.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["ConfigError", "Settings", "resolve"]


class ConfigError(Exception):
    """Raised when settings cannot be resolved (e.g. no LLM credentials)."""


# Provider auto-detection precedence: first env var present wins.
_PROVIDER_ENV: list[tuple[str, str]] = [
    ("openai", "OPENAI_API_KEY"),
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("gemini", "GEMINI_API_KEY"),
    ("openrouter", "OPENROUTER_API_KEY"),
]
_PROVIDER_KEY = dict(_PROVIDER_ENV)
# Providers that run locally and need no API key.
_KEYLESS_PROVIDERS = {"ollama", "openai-endpoint"}

_VALID_STEALTH = {"auto", "always", "off"}
_VALID_DEPTH = {"quick", "detailed", "report"}
_VALID_ENGINE = {"duckduckgo", "searxng", "auto"}

_DEFAULT_MODEL = {
    "openai": "gpt-4.1",
    "anthropic": "claude-sonnet-4-6",
    "gemini": "gemini-2.5-pro",
    "openrouter": "openai/gpt-4.1",
    "ollama": "llama3.1",
    "openai-endpoint": None,  # local OpenAI-compatible server — model is server-defined
}

# Our provider name -> the value local-deep-research expects in LDR_LLM_PROVIDER.
_LDR_PROVIDER = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "openrouter": "openai_endpoint",
    "ollama": "ollama",
    "openai-endpoint": "openai_endpoint",
}


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str | None
    api_key: str | None
    search_engine: str
    stealth_mode: str
    depth: str
    respect_robots: bool
    out: str | None
    proxy: str | None
    searxng_url: str | None
    base_url: str | None = None  # for provider "openai-endpoint" (local OpenAI-compatible)

    def to_ldr_env(self) -> dict[str, str]:
        """Map resolved settings to the LDR_* environment variables LDR reads."""
        env: dict[str, str] = {
            "LDR_LLM_PROVIDER": _LDR_PROVIDER[self.provider],
            # DeepCloak's whole point is reading full pages (and Bypassing walls to
            # do it), so we always fetch full content — never snippet-only.
            "LDR_SEARCH_SNIPPETS_ONLY": "false",
        }
        if self.model:
            env["LDR_LLM_MODEL"] = self.model
        if self.provider == "openai-endpoint":
            if self.base_url:
                env["LDR_LLM_OPENAI_ENDPOINT_URL"] = self.base_url
            # llama.cpp / vLLM ignore the key, but LDR requires a non-empty one.
            env["LDR_LLM_OPENAI_ENDPOINT_API_KEY"] = self.api_key or "local"
        # Pass the credential through under its standard name (langchain reads these).
        if self.api_key and self.provider in _PROVIDER_KEY:
            env[_PROVIDER_KEY[self.provider]] = self.api_key
        if self.search_engine == "searxng" and self.searxng_url:
            env["LDR_SEARCH_ENGINE_WEB_SEARXNG_DEFAULT_PARAMS_INSTANCE_URL"] = self.searxng_url
        return env

    def to_ldr_overrides(self) -> dict:
        """Settings as an LDR settings-snapshot override dict (the supported API path).

        Critically sets ``search.snippets_only=False`` so the research loop fetches
        full pages — which is what routes through the stealth shim and Bypasses walls.
        """
        o: dict[str, object] = {
            "llm.provider": _LDR_PROVIDER[self.provider],
            "search.snippets_only": False,
            "search.tool": self.search_engine,
        }
        if self.model:
            o["llm.model"] = self.model
        if self.provider == "openai-endpoint":
            if self.base_url:
                o["llm.openai_endpoint.url"] = self.base_url
            o["llm.openai_endpoint.api_key"] = self.api_key or "local"
        elif self.api_key and self.provider in _PROVIDER_KEY:
            o[f"llm.{self.provider}.api_key"] = self.api_key
        if self.search_engine == "searxng" and self.searxng_url:
            o["search.engine.web.searxng.default_params.instance_url"] = self.searxng_url
        return o


def _resolve_provider(cli: Mapping, env: Mapping) -> str:
    provider = cli.get("provider")
    if provider:
        return provider
    for name, key in _PROVIDER_ENV:
        if env.get(key):
            return name
    wanted = ", ".join(key for _, key in _PROVIDER_ENV)
    raise ConfigError(
        "No LLM credentials found. Set one of: "
        f"{wanted} (or pass --provider ollama for a local model)."
    )


def _validate(value: str, valid: set[str], label: str) -> str:
    if value not in valid:
        raise ConfigError(f"Invalid {label}: {value!r}. Choose one of {sorted(valid)}.")
    return value


def resolve(cli: Mapping, env: Mapping) -> Settings:
    """Resolve effective settings. Precedence: CLI flags > environment."""
    provider = _resolve_provider(cli, env)
    api_key = None
    if provider not in _KEYLESS_PROVIDERS:
        api_key = env.get(_PROVIDER_KEY.get(provider, ""))

    model = cli.get("model") or env.get("DEEPCLOAK_MODEL") or _DEFAULT_MODEL.get(provider)
    search_engine = _validate(cli.get("engine") or "duckduckgo", _VALID_ENGINE, "search engine")
    stealth_mode = _validate(cli.get("stealth") or "auto", _VALID_STEALTH, "stealth mode")
    depth = _validate(cli.get("depth") or "detailed", _VALID_DEPTH, "depth")
    searxng_url = cli.get("searxng_url") or env.get(
        "LDR_SEARCH_ENGINE_WEB_SEARXNG_DEFAULT_PARAMS_INSTANCE_URL"
    )

    base_url = cli.get("base_url") or env.get("LDR_LLM_OPENAI_ENDPOINT_URL")
    if provider == "openai-endpoint" and not base_url:
        raise ConfigError(
            "provider 'openai-endpoint' needs --base-url (e.g. http://localhost:8080/v1) "
            "or LDR_LLM_OPENAI_ENDPOINT_URL."
        )

    return Settings(
        provider=provider,
        model=model,
        api_key=api_key,
        search_engine=search_engine,
        stealth_mode=stealth_mode,
        depth=depth,
        respect_robots=bool(cli.get("respect_robots", False)),
        out=cli.get("out"),
        proxy=cli.get("proxy"),
        searxng_url=searxng_url,
        base_url=base_url,
    )
