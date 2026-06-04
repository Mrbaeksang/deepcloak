# DeepCloak

Local-first **Deep Research** agent that reads the whole web — including pages behind a **Bot Wall** (Cloudflare / Datadome / Turnstile / reCAPTCHA). A thin orchestrator over `local-deep-research` (the research loop) and `cloakbrowser` (stealth fetch), shipped as a CLI, an MCP server, and a Claude skill. MIT.

See @CONTEXT.md for the domain glossary — use its terms (Bot Wall, Stealth Fetch, Escalation, Bypass, Evidence Record, Deep Research) in code, issues, and docs.

## WHAT — project shape

- Thin standalone orchestrator. We own no research loop; we depend on `local-deep-research` (pinned `==`) and `cloakbrowser` via pip. Never vendor upstream code.
- Every surface (CLI, MCP server, Claude skill) calls one core: `research_core.research(...)`. It installs the shim once, calls LDR, and attaches Evidence Records.
- Deep modules — small, stable public interface, hidden internals, tested in isolation: `bot_wall_detector`, `evidence`, `fetch_router`, `config`. Keep their interfaces narrow.

## HOW — commands

- Run research: `deepcloak "<query>" --depth quick|detailed|report`
- First-time setup (downloads stealth Chromium): `deepcloak setup`
- Start the MCP server: `deepcloak mcp`
- Test: `pytest` · Lint: `ruff check .`
- While iterating, run a single test file, not the whole suite.

## WHY — rules (earn every line)

### Working style — think first, stay surgical
- State assumptions before coding. If a requirement has two readings, surface both — don't pick silently. Push back when a simpler path exists.
- Ship the minimum that solves the task. No speculative abstractions, configurability, or error handling for impossible cases.
- Make surgical edits: change only what the task needs, match surrounding style, don't refactor untouched code. Remove only the orphans your change creates.
- Turn each task into a verifiable goal: write the test that proves it, then make it pass. Loop until green.

### Architecture
- Inject stealth through the **narrowest** LDR seam — override `_fetch_with_playwright` only. See `docs/adr/0001`. Don't widen the monkeypatch surface.
- Pin `local-deep-research` with `==`; the shim relies on internal symbols.
- robots.txt is **ignored by default**; `--respect-robots` is opt-in. See `docs/adr/0002`.
- Respect ADRs in `docs/adr/`. If a change contradicts one, stop and flag it — never silently override.

### Gotchas
- NEVER call the upstream `ldr` CLI — it's broken (`ModuleNotFoundError`). Use LDR's Python API / `ldr-mcp` paths only.
- The shim applies in-process only — every entry point must go through `research_core`, never plain LDR, or Stealth Fetch silently won't run.
- Default search is DuckDuckGo (keyless, no Docker); SearXNG is opt-in.

### Testing
- Test external behavior through public interfaces, not internals.
- Unit-test the four pure/deep modules with committed Bot Wall HTML fixtures. Smoke-test shim + core + CLI + MCP. Mirror `local-deep-research`'s fixture style.

## Agent skills

### Issue tracker
Issues live in GitHub Issues, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels
The five canonical triage roles map to identically-named labels. See `docs/agents/triage-labels.md`.

### Domain docs
Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
