# Changelog

All notable changes to DeepCloak are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **Interactive picker** — with several LLM credentials in the environment and a real
  terminal, `deepcloak "<query>"` asks which provider (and model, listed live) to use;
  scripts, pipes and MCP clients are never prompted.
- **Local run history** — every CLI run is saved under `~/.local/share/deepcloak/runs/`
  (report + Evidence Records + metadata); browse with `deepcloak runs`, replay with
  `deepcloak show <id>` (`--json` for everything). `$DEEPCLOAK_RUNS_DIR` relocates it.
- **Optional rich rendering** — `pip install deepcloak[rich]` upgrades the progress
  output to a live status line; plain stderr lines remain the fallback.
- Retriever now fetches search hits **in parallel** while keeping Evidence Record
  order stable — noticeably faster Deep Research on many-source queries.

### Added
- `deepcloak models [--provider X] [--base-url U]` — list a provider's models over its
  public API (OpenRouter, OpenAI, Anthropic, Gemini, Ollama, LM Studio, llama.cpp,
  any OpenAI-compatible endpoint). Also exposed as an MCP `list_models` tool.
- MCP tools accept `provider` / `model`; stored runs are capped so long-lived servers
  don't leak.
- `--json` output mode — one JSON object with the query, report, Evidence Records and
  resolved settings (API key omitted) for scripting and piping.
- Config file support: `~/.config/deepcloak/config.toml` (or `$DEEPCLOAK_CONFIG`);
  precedence CLI flags > environment > file. `lmstudio` / `llamacpp` joined as
  first-class providers.
- Live research-phase progress on stderr (LDR's `progress_callback`), next to the
  existing Evidence Record lines.

### Fixed
- `gemini` provider was broken end-to-end: DeepCloak now maps it to LDR's native
  `google` provider and writes the key to `llm.google.api_key`.
- `openrouter` credentials never reached LDR (placeholder key → 401): DeepCloak now
  routes through LDR's native `openrouter` provider instead of an `openai_endpoint`
  detour.
- Degraded runs no longer fail silently: a missing stealth shim or settings snapshot
  prints a loud warning (a run without them cannot Bypass any Bot Wall).

## [0.1.0] — 2026-06-05

First public release.

### Added
- **Deep Research that reads Bot-walled pages.** Plain fetch first; on a Bot Wall
  (Cloudflare / Datadome / Turnstile / reCAPTCHA) it Escalates one URL to a Stealth Fetch
  and Bypasses it — recovering content other agents drop.
- **StealthRetriever** — handed to `local-deep-research` via its `retrievers=` API so the
  research loop synthesises over Bypassed full pages, not snippets.
- **Evidence Records** — every fetch is recorded (Bot Wall kind, Escalation, Bypass,
  plain status, timing); reports end with a `🛡️ Bypassed N bot-walled sources` badge and a
  `*.evidence.json` sidecar.
- Three surfaces over one core: **CLI**, **MCP server** (`deep_research` / `quick_summary`
  / `get_evidence`), and a **Claude skill**.
- Local-first: works with `ollama` or any OpenAI-compatible local endpoint — no API key
  required. Default search is DuckDuckGo (keyless); SearXNG is opt-in.
- `--respect-robots` to honor robots.txt (ignored by default — see ADR-0002).
- Per-document content cap so small-context local models can finish a report.

[Unreleased]: https://github.com/Mrbaeksang/deepcloak/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Mrbaeksang/deepcloak/releases/tag/v0.1.0
