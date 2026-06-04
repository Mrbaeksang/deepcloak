"""`deepcloak setup` — download the stealth browser and check the environment."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping

__all__ = ["run_setup", "check_env", "install_browser"]

_KEY_VARS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY")


def check_env(env: Mapping[str, str] | None = None) -> list[str]:
    """Return a list of warnings about the environment (empty == all good)."""
    env = os.environ if env is None else env
    warnings: list[str] = []
    if not any(env.get(k) for k in _KEY_VARS):
        warnings.append(
            "No LLM API key found — set one of "
            + ", ".join(_KEY_VARS)
            + " (or use --provider ollama for a local model)."
        )
    return warnings


def _playwright_install() -> bool:
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False


_UNSET = object()


def install_browser(cb: object = _UNSET) -> tuple[bool, str]:
    """Best-effort: ensure the stealth browser binary is available.

    ``cb`` is the cloakbrowser module; pass ``None`` to simulate it missing.
    """
    if cb is _UNSET:
        try:
            import cloakbrowser as cb  # type: ignore
        except ImportError:
            cb = None
    if cb is None:
        return False, "cloakbrowser is not installed — run `pip install deepcloak`."

    # cloakbrowser manages its own stealth Chromium via ensure_binary()/download().
    for fname in ("ensure_binary", "download", "install"):
        fn = getattr(cb, fname, None)
        if callable(fn):
            try:
                path = fn()
                where = f" ({path})" if isinstance(path, str) else ""
                return True, f"Stealth browser ready via cloakbrowser.{fname}(){where}."
            except Exception:
                continue
    if _playwright_install():
        return True, "Stealth browser (Chromium) installed via Playwright."
    return True, "cloakbrowser present; could not confirm the browser download — try manually."


def run_setup(cb: object = _UNSET) -> int:
    ok, msg = install_browser(cb)
    print(msg)
    for warning in check_env():
        print(f"warning: {warning}")
    print("DeepCloak is ready." if ok else "Setup incomplete — see the message above.")
    return 0 if ok else 1
