# DeepCloak

> Local-first deep research agent that reads the whole web — even pages behind Cloudflare, Datadome, Turnstile & reCAPTCHA.

DeepCloak pairs an iterative research loop ([`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)) with a stealth browser fetch layer ([`cloakbrowser`](https://github.com/CloakHQ/CloakBrowser)). When a plain fetch hits a **Bot Wall**, DeepCloak **Escalates** that URL to a **Stealth Fetch** and **Bypasses** the wall — so your cited report isn't missing the sources other tools silently drop.

Surfaces: a CLI, an MCP server, and a Claude skill. MIT licensed.

> ⚠️ **You are responsible for what you fetch.** You must have the right to access the content. robots.txt is ignored by default; use `--respect-robots` to honor it. See [ADR-0002](docs/adr/0002-ignore-robots-by-default.md).

## Quickstart

```bash
pip install deepcloak
deepcloak setup                      # download the stealth browser
export OPENAI_API_KEY=...            # or ANTHROPIC_API_KEY / GEMINI_API_KEY
deepcloak "your research question" --depth detailed --out report.md
```

## How it works

1. Search (DuckDuckGo by default — no Docker) finds candidate URLs.
2. Each page is fetched plain first; on a detected Bot Wall it Escalates to a Stealth Fetch.
3. The research loop reads, iterates, and writes a cited report ending with a `🛡️ Bypassed N bot-walled sources` section, plus an `<report>.evidence.json` sidecar.

See [`CONTEXT.md`](CONTEXT.md) for the glossary and [`docs/adr/`](docs/adr/) for design decisions.

> A polished, multi-language README and a showcase site are tracked in issues #7 and #8.
