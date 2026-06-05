# Changelog

All notable changes to DeepCloak are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project uses [SemVer](https://semver.org/).

## [Unreleased]

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
