"""Resolve runtime settings from CLI args + environment + config file.

Pure module: ``resolve()`` takes plain mappings (the caller decides whether a
mapping came from ``load_config_file()``) and returns a frozen ``Settings``.
No I/O at import time, no heavy upstream imports — trivially testable.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .providers import PROVIDERS, ProviderError, ProviderSpec, detect, get

__all__ = ["ConfigError", "Settings", "resolve", "load_config_file"]


class ConfigError(Exception):
    """Raised when settings cannot be resolved (e.g. no LLM credentials)."""


# Providers that run locally and need no API key.
_KEYLESS_PROVIDERS = {name for name, s in PROVIDERS.items() if s.keyless}

_VALID_STEALTH = {"auto", "always", "off"}
_VALID_DEPTH = {"quick", "detailed", "report"}
_VALID_ENGINE = {"duckduckgo", "searxng", "youcom", "auto"}

# Which LDR settings key receives a custom base URL, per provider.
_BASE_URL_SETTING = {
    "lmstudio": "llm.lmstudio.url",
    "llamacpp": "llm.llamacpp.url",
    "openai-endpoint": "llm.openai_endpoint.url",
}


def _spec(name: str) -> ProviderSpec:
    try:
        return PROVIDERS[name]
    except KeyError:
        raise ConfigError(
            f"Unknown provider {name!r}. Choose one of {sorted(PROVIDERS)}."
        ) from None


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
    youcom_api_key: str | None = None
    base_url: str | None = None  # for provider "openai-endpoint" (local OpenAI-compatible)

    def to_ldr_env(self) -> dict[str, str]:
        """Map resolved settings to the LDR_* environment variables LDR reads."""
        spec = _spec(self.provider)
        env: dict[str, str] = {
            "LDR_LLM_PROVIDER": spec.ldr_provider,
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
        if self.api_key and spec.env_key:
            env[spec.env_key] = self.api_key
        if self.search_engine == "searxng" and self.searxng_url:
            env["LDR_SEARCH_ENGINE_WEB_SEARXNG_DEFAULT_PARAMS_INSTANCE_URL"] = self.searxng_url
        return env

    def to_ldr_overrides(self) -> dict:
        """Settings as an LDR settings-snapshot override dict (the supported API path).

        Critically sets ``search.snippets_only=False`` so the research loop fetches
        full pages — which is what routes through the stealth shim and Bypasses walls.
        """
        spec = _spec(self.provider)
        o: dict[str, object] = {
            "llm.provider": spec.ldr_provider,
            "search.snippets_only": False,
            "search.tool": self.search_engine,
        }
        if self.model:
            o["llm.model"] = self.model
        base_url_setting = _BASE_URL_SETTING.get(self.provider)
        if base_url_setting and self.base_url:
            o[base_url_setting] = self.base_url
        if self.provider == "openai-endpoint":
            o["llm.openai_endpoint.api_key"] = self.api_key or "local"
        elif self.api_key and spec.ldr_key_setting:
            o[spec.ldr_key_setting] = self.api_key
        if self.search_engine == "searxng" and self.searxng_url:
            o["search.engine.web.searxng.default_params.instance_url"] = self.searxng_url
        return o


def _resolve_provider(cli: Mapping, env: Mapping) -> str:
    provider = cli.get("provider")
    if provider:
        _spec(provider)
        return provider
    try:
        return detect(env)
    except ProviderError as exc:
        raise ConfigError(str(exc)) from None


def _validate(value: str, valid: set[str], label: str) -> str:
    if value not in valid:
        raise ConfigError(f"Invalid {label}: {value!r}. Choose one of {sorted(valid)}.")
    return value


# Keys a config file / DEEPCLOAK_* env var may set (mirrors CLI flag names).
_SETTING_KEYS = (
    "provider", "model", "depth", "engine", "stealth",
    "base_url", "searxng_url", "proxy", "out", "respect_robots",
    "youcom_api_key",
)
_BOOL_KEYS = frozenset({"respect_robots"})
_TRUTHY = {"1", "true", "yes", "on"}


def _coerce(key: str, value: object) -> object:
    if key in _BOOL_KEYS and isinstance(value, str):
        return value.strip().lower() in _TRUTHY
    return value


def _layered(cli: Mapping, env: Mapping, file: Mapping | None) -> dict:
    """Merge sources per key. Precedence: CLI flags > DEEPCLOAK_* env > file."""
    src: dict = {}
    for key in _SETTING_KEYS:
        v = cli.get(key)
        if v not in (None, False):
            src[key] = v
            continue
        e = env.get(f"DEEPCLOAK_{key.upper()}")
        if e:
            src[key] = _coerce(key, e)
            continue
        f = file.get(key) if file else None
        if f is not None:
            src[key] = f
    return src


def load_config_file(path: str | None = None) -> dict:
    """Read a deepcloak TOML config file; unknown keys are ignored.

    Defaults to ``$DEEPCLOAK_CONFIG`` or ``~/.config/deepcloak/config.toml``.
    A missing file is not an error — an empty dict is returned. A malformed
    one raises :class:`ConfigError`.
    """
    import os
    import pathlib
    import tomllib

    p = pathlib.Path(
        path or os.environ.get("DEEPCLOAK_CONFIG") or "~/.config/deepcloak/config.toml"
    ).expanduser()
    if not p.is_file():
        return {}
    try:
        with open(p, "rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"config file {p} is not valid TOML: {exc}") from None
    return {k: v for k, v in data.items() if k in _SETTING_KEYS}


def resolve(cli: Mapping, env: Mapping, file: Mapping | None = None) -> Settings:
    """Resolve effective settings. Precedence: CLI flags > environment > file."""
    src = _layered(cli, env, file)
    provider = _resolve_provider(src, env)
    spec = get(provider)
    api_key = None
    if provider not in _KEYLESS_PROVIDERS:
        api_key = env.get(spec.env_key or "")

    model = src.get("model") or spec.default_model
    search_engine = _validate(src.get("engine") or "duckduckgo", _VALID_ENGINE, "search engine")
    stealth_mode = _validate(src.get("stealth") or "auto", _VALID_STEALTH, "stealth mode")
    depth = _validate(src.get("depth") or "detailed", _VALID_DEPTH, "depth")
    searxng_url = src.get("searxng_url") or env.get(
        "LDR_SEARCH_ENGINE_WEB_SEARXNG_DEFAULT_PARAMS_INSTANCE_URL"
    )
    youcom_api_key = src.get("youcom_api_key") or env.get("YDC_API_KEY")

    base_url = src.get("base_url") or env.get("LDR_LLM_OPENAI_ENDPOINT_URL")
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
        respect_robots=bool(src.get("respect_robots", False)),
        out=src.get("out"),
        proxy=src.get("proxy"),
        searxng_url=searxng_url,
        youcom_api_key=youcom_api_key,
        base_url=base_url,
    )
