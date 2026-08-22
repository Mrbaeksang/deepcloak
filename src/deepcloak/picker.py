"""Zero-dependency interactive provider/model picker.

Used only when a human is on the other end (TTY) and the environment holds
more than one LLM credential, so scripts and MCP clients never get prompted.
I/O is injectable — ``input_fn``/``echo``/``fetch`` — keeping it testable.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from .providers import PROVIDERS, ProviderError, ProviderSpec, get, list_models

__all__ = ["candidates", "ask_choice", "pick_provider_and_model"]


def candidates(env: Mapping) -> list[ProviderSpec]:
    """Providers whose credential env var is present, in detection order."""
    return [s for s in PROVIDERS.values() if s.env_key and env.get(s.env_key)]


def ask_choice(
    title: str,
    options: list[tuple[str, str]],
    *,
    input_fn: Callable[[str], str] = input,
    echo: Callable[[str], None] = print,
) -> str | None:
    """Render a numbered menu of ``(value, label)`` pairs; return the value.

    Returns None on EOF/Ctrl-C or an out-of-range answer — callers fall back
    to their default instead of dying.
    """
    if not options:
        return None
    echo(title)
    for i, (_, label) in enumerate(options, 1):
        echo(f"  {i}. {label}")
    try:
        raw = input_fn(f"Choose [1-{len(options)}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    try:
        idx = int(raw)
    except ValueError:
        return None
    if not 1 <= idx <= len(options):
        return None
    return options[idx - 1][0]


def pick_provider_and_model(
    env: Mapping,
    *,
    input_fn: Callable[[str], str] = input,
    echo: Callable[[str], None] = print,
    timeout: float = 8.0,
    fetch: Callable[[str, Mapping[str, str] | None], dict] | None = None,
) -> tuple[str, str | None] | None:
    """Ask which credentialed provider + model to use; None when there's nothing to ask."""
    specs = candidates(env)
    if len(specs) <= 1:
        return None

    def _label(s: ProviderSpec) -> str:
        return f"{s.name} — default {s.default_model}" if s.default_model else s.name

    provider = ask_choice(
        "Multiple LLM credentials found — pick a provider:",
        [(s.name, _label(s)) for s in specs],
        input_fn=input_fn,
        echo=echo,
    )
    if provider is None:
        return None
    spec = get(provider)
    api_key = env.get(spec.env_key) if spec.env_key else None

    try:
        models = list_models(provider, api_key=api_key, timeout=timeout, fetch=fetch)
    except ProviderError:
        models = []

    if not models:
        # No public directory (or offline): take a manual id, empty = default.
        try:
            raw = input_fn(f"Model id [{spec.default_model or '-'}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            raw = ""
        return provider, raw or spec.default_model

    options: list[tuple[str, str]] = []
    if spec.default_model:
        options.append((spec.default_model, f"(provider default) {spec.default_model}"))
    options.extend((m, m) for m in models)
    model = ask_choice(f"Models from {provider}:", options, input_fn=input_fn, echo=echo)
    return provider, model if model is not None else spec.default_model
