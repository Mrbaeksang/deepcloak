"""DeepCloak command-line interface."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import load_config_file
from .picker import pick_provider_and_model
from .providers import ProviderError, detect, get, list_models

__all__ = ["main", "build_parser"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="deepcloak",
        description="Deep research that reads bot-walled pages.",
        epilog="Subcommands: 'deepcloak setup' (install stealth browser), "
        "'deepcloak mcp' (run MCP server), 'deepcloak models' (list a provider's models).",
    )
    p.add_argument("--version", action="version", version=f"deepcloak {__version__}")
    p.add_argument("query", nargs="?", help="The research question.")
    p.add_argument("--depth", choices=["quick", "detailed", "report"], default="detailed")
    p.add_argument("--engine", choices=["duckduckgo", "searxng", "youcom", "auto"], default=None)
    p.add_argument("--searxng-url", dest="searxng_url", default=None,
                   help="SearXNG instance URL (for --engine searxng)")
    p.add_argument("--stealth", choices=["auto", "always", "off"], default=None)
    p.add_argument("--respect-robots", action="store_true", dest="respect_robots")
    p.add_argument("--proxy", default=None)
    p.add_argument("--provider", default=None,
                   help="openai/anthropic/gemini/openrouter/ollama/lmstudio/"
                        "llamacpp/openai-endpoint")
    p.add_argument("--model", default=None)
    p.add_argument("--base-url", dest="base_url", default=None,
                   help="OpenAI-compatible URL (for openai-endpoint provider)")
    p.add_argument("--out", default=None, help="Write the report to this file.")
    p.add_argument("--json", action="store_true",
                   help="Print the full result (query/report/evidence/settings) as JSON "
                        "to stdout instead of the report text.")
    return p


def _result_json(result, query: str) -> str:
    """Serialize a Result for scripting. The API key is omitted entirely."""
    import json

    s = result.settings
    return json.dumps(
        {
            "query": query,
            "report": result.report,
            "evidence": result.evidence,
            "settings": {
                "provider": s.provider,
                "model": s.model,
                "depth": s.depth,
                "search_engine": s.search_engine,
                "stealth_mode": s.stealth_mode,
            },
        },
        indent=2,
        ensure_ascii=False,
    )


def _run_models(argv: list[str]) -> int:
    """`deepcloak models` — list a provider's model ids, one per line."""
    import os

    p = argparse.ArgumentParser(
        prog="deepcloak models",
        description="List the models a provider offers (public model APIs).",
    )
    p.add_argument("--provider", default=None,
                   help="defaults to auto-detection from environment credentials")
    p.add_argument("--base-url", dest="base_url", default=None,
                   help="endpoint URL for local OpenAI-compatible providers")
    p.add_argument("--timeout", type=float, default=20.0,
                   help="seconds to wait for the provider's model list")
    args = p.parse_args(argv)

    try:
        name = args.provider or detect(dict(os.environ))
        spec = get(name)
        api_key = os.environ.get(spec.env_key) if spec.env_key else None
        for model in list_models(name, api_key=api_key, base_url=args.base_url,
                                 timeout=args.timeout):
            print(model)
        return 0
    except ProviderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _run_runs(argv: list[str]) -> int:
    """`deepcloak runs` — list saved research runs, newest first."""
    p = argparse.ArgumentParser(
        prog="deepcloak runs",
        description="List saved research runs from the local history.",
    )
    p.add_argument("--limit", type=int, default=25, help="how many to show")
    args = p.parse_args(argv)

    from .history import list_runs

    for r in list_runs()[: args.limit]:
        provider = r.get("provider") or "-"
        model = r.get("model") or "-"
        query = (r["query"] or "-")[:70]
        print(f"{r['id']}  {provider}/{model}  {query}")
    return 0


def _run_show(argv: list[str]) -> int:
    """`deepcloak show <id>` — print a saved run's report."""
    import json

    p = argparse.ArgumentParser(
        prog="deepcloak show", description="Print a saved run's report."
    )
    p.add_argument("run_id", help="run id (unique prefix works)")
    p.add_argument("--json", action="store_true", help="print meta+report+evidence as JSON")
    args = p.parse_args(argv)

    from .history import load_run

    got = load_run(args.run_id)
    if got is None:
        print(f"error: no saved run matches {args.run_id!r}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(got, ensure_ascii=False, indent=2))
    else:
        print(got["report"])
    return 0


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
    if argv and argv[0] == "models":
        return _run_models(argv[1:])
    if argv and argv[0] == "runs":
        return _run_runs(argv[1:])
    if argv and argv[0] == "show":
        return _run_show(argv[1:])

    args = build_parser().parse_args(argv)
    if not args.query:
        build_parser().print_help()
        return 2

    from .research_core import research

    cli_opts = _cli_dict(args)

    # A human at a terminal with several credentials gets asked; scripts,
    # pipes and MCP clients never do.
    if (
        sys.stdin.isatty()
        and sys.stdout.isatty()
        and not cli_opts.get("provider")
        and not cli_opts.get("model")
        and not load_config_file().get("provider")
    ):
        import os

        picked = pick_provider_and_model(dict(os.environ))
        if picked:
            provider, model = picked
            cli_opts["provider"] = provider
            if model:
                cli_opts["model"] = model

    try:
        result = research(args.query, cli=cli_opts, verbose=True)
    except Exception as exc:  # surface a clean message, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Keep the run locally (report + Evidence Records) for `deepcloak runs/show`.
    try:
        from .history import save_run

        s = result.settings
        save_run(
            query=args.query,
            report=result.report,
            evidence_json=result.evidence_json,
            provider=s.provider,
            model=s.model,
            depth=s.depth,
        )
    except Exception as exc:
        print(f"warning: could not save run history: {exc}", file=sys.stderr)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(result.report)
        sidecar = f"{args.out}.evidence.json"
        with open(sidecar, "w", encoding="utf-8") as fh:
            fh.write(result.evidence_json)
        print(f"wrote {args.out} (+ {sidecar})", file=sys.stderr)
    if args.json or not args.out:
        # --json prints the machine-readable result; with no --out the report
        # itself goes to stdout as before.
        if args.json:
            print(_result_json(result, args.query))
        else:
            print(result.report)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
