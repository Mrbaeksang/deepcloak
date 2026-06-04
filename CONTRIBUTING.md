# Contributing to DeepCloak

Thanks for your interest! DeepCloak is a thin orchestrator over
[`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)
and [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser). Read
[`CLAUDE.md`](CLAUDE.md) and [`CONTEXT.md`](CONTEXT.md) first — they hold the
working rules and the domain glossary. Use the glossary's terms (Bot Wall,
Stealth Fetch, Escalation, Bypass, Evidence Record) in code, tests, and issues.

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # add ,mcp for the MCP server
deepcloak setup                # download the stealth browser (for live runs)
pytest                         # run the suite
ruff check .                   # lint
```

For fast unit work you don't need the heavy upstreams: `pip install pytest ruff`
then `pip install -e . --no-deps` — the pure modules and mocked smoke tests run
without them (this is what CI does).

## Principles

- **Small, surgical changes.** Each changed line should trace to the issue.
- **Test behavior, not internals.** The pure/deep modules (`bot_wall_detector`,
  `evidence`, `fetch_router`, `config`) are unit-tested through their public
  interface; integration points are smoke-tested with fakes.
- **Respect the ADRs** in [`docs/adr/`](docs/adr/). If a change contradicts one,
  say so in the PR rather than silently overriding it.
- **Keep the stealth seam narrow.** See
  [ADR-0001](docs/adr/0001-narrow-seam-stealth-injection.md).

## Workflow

1. Grab an issue (start with `ready-for-agent` / `good first issue`).
2. Branch, implement with tests, keep `pytest` and `ruff` green.
3. Open a PR that references the issue. CI must pass.

## Responsible use

DeepCloak Bypasses bot-detection. You are responsible for having the right to
access whatever you fetch. robots.txt is ignored by default; `--respect-robots`
honors it. See [ADR-0002](docs/adr/0002-ignore-robots-by-default.md).
