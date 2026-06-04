"""DeepCloak command-line interface."""

from __future__ import annotations

import argparse
import sys

from . import __version__

__all__ = ["main", "build_parser"]

_SUBCOMMANDS = ("setup", "mcp")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="deepcloak",
        description="Deep research that reads bot-walled pages.",
        epilog="Subcommands: 'deepcloak setup' (install stealth browser), "
        "'deepcloak mcp' (run MCP server).",
    )
    p.add_argument("--version", action="version", version=f"deepcloak {__version__}")
    p.add_argument("query", nargs="?", help="The research question.")
    p.add_argument("--depth", choices=["quick", "detailed", "report"], default="detailed")
    p.add_argument("--engine", choices=["duckduckgo", "searxng", "auto"], default=None)
    p.add_argument("--searxng-url", dest="searxng_url", default=None,
                   help="SearXNG instance URL (for --engine searxng)")
    p.add_argument("--stealth", choices=["auto", "always", "off"], default=None)
    p.add_argument("--respect-robots", action="store_true", dest="respect_robots")
    p.add_argument("--proxy", default=None)
    p.add_argument("--provider", default=None,
                   help="openai/anthropic/gemini/ollama/openai-endpoint")
    p.add_argument("--model", default=None)
    p.add_argument("--base-url", dest="base_url", default=None,
                   help="OpenAI-compatible URL (for openai-endpoint provider)")
    p.add_argument("--out", default=None, help="Write the report to this file.")
    return p


def _cli_dict(args: argparse.Namespace) -> dict:
    keys = ("depth", "engine", "stealth", "respect_robots", "proxy",
            "provider", "model", "base_url", "searxng_url", "out")
    return {k: getattr(args, k) for k in keys if getattr(args, k) not in (None, False)}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)

    # Subcommands are dispatched manually so the default `deepcloak "<query>"`
    # form doesn't collide with an argparse subparser positional.
    if argv and argv[0] == "setup":
        from .setup import run_setup

        return run_setup()
    if argv and argv[0] == "mcp":
        from .mcp_server import serve

        serve()
        return 0

    args = build_parser().parse_args(argv)
    if not args.query:
        build_parser().print_help()
        return 2

    from .research_core import research

    try:
        result = research(args.query, cli=_cli_dict(args), verbose=True)
    except Exception as exc:  # surface a clean message, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(result.report)
        sidecar = f"{args.out}.evidence.json"
        with open(sidecar, "w", encoding="utf-8") as fh:
            fh.write(result.evidence_json)
        print(f"wrote {args.out} (+ {sidecar})")
    else:
        print(result.report)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
