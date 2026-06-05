<div align="center">

<h1>🛡️ DeepCloak</h1>

### The deep-research agent that reads the pages others can't.

**Cloudflare · Datadome · Turnstile · reCAPTCHA — it walks straight through them.**

[![CI](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml/badge.svg)](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-a855f7.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![MCP native](https://img.shields.io/badge/MCP-native-22d3ee.svg)](#-use-it-from-an-ai-agent)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-34d399.svg)](CONTRIBUTING.md)
[![GitHub stars](https://img.shields.io/github/stars/Mrbaeksang/deepcloak?style=social)](https://github.com/Mrbaeksang/deepcloak/stargazers)
[![Watch on YouTube](https://img.shields.io/badge/▶_demo-YouTube-FF0000.svg)](https://youtu.be/p5ompjDLzaI)

**English** · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

### [▶ Live demo — deepcloak.vercel.app](https://deepcloak.vercel.app)  ·  [▶ Watch on YouTube](https://youtu.be/p5ompjDLzaI)

[![DeepCloak running: it detects a Cloudflare Turnstile, escalates, and bypasses it — then writes a cited report](docs/media/demo.gif)](https://youtu.be/p5ompjDLzaI)

</div>

---

## The problem

You ask a research tool a question. Half the best sources sit behind a **Bot Wall** — Cloudflare, Datadome, a Turnstile, a reCAPTCHA. Every other tool gets a `403`, silently drops those pages, and hands you a thinner report. **You never even learn what it missed.**

## What DeepCloak does

When a plain fetch hits a Bot Wall, DeepCloak **Escalates** that one URL to a **Stealth Fetch** and **Bypasses** the wall — recovering the content other agents abandon. Then it tells you, at the bottom of every report, exactly how many walls it broke through.

It's a thin, local-first orchestrator over two great projects: [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research) (the research loop) and [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser) (the stealth browser). Use it as a **CLI**, an **MCP server**, or a **Claude skill**. MIT.

## 🌑 Why we built this

The open web is quietly closing. More of the best writing now sits behind a bot check, and AI research agents — the tools we increasingly trust to read the web *for us* — go blind at exactly those doors, without ever saying so. A report that silently skips every walled source isn't neutral; it's wrong in a way you can't see.

DeepCloak's stance is simple: **your agent should be able to read what a person with a browser can read** — and it should be honest about how it got there. So it Bypasses the wall when it has to, keeps everything local (no query or page leaves your machine), and prints an Evidence Record of every wall it crossed. Capability *and* transparency, MIT-licensed, no lock-in.

## ✨ Why it's different

|  | Plain deep research | **DeepCloak** |
| --- | :---: | :---: |
| Reads the open web | ✅ | ✅ |
| Reads Cloudflare / Datadome / Turnstile / reCAPTCHA pages | ❌ *dropped silently* | ✅ **Bypassed** |
| Tells you which sources were walled | ❌ | ✅ Evidence Record |
| Local-first (no API key required) | ✅ | ✅ |
| Fast on open pages | — | ✅ *plain-first, stealth only when needed* |

> **Verified live — not mocked.** The clip above is an **unedited screen recording** (captured with `ffmpeg`, no compositing) of a real `deepcloak` run against a **local LLM (Qwen) + SearXNG — no API key**. It Escalates on each Bot Wall and **Bypasses 8 Cloudflare/Turnstile walls** in one pass, then writes a cited report. Full clip: [`docs/media/demo-real.mp4`](docs/media/demo-real.mp4); a raw asciinema session is also kept at [`docs/media/demo.cast`](docs/media/demo.cast). Wall counts vary per run (8–20) because the open web does.

## 🚀 Quickstart

```bash
pip install deepcloak
deepcloak setup                       # one-time: downloads the stealth browser
export OPENAI_API_KEY=...             # or ANTHROPIC_API_KEY / GEMINI_API_KEY — or --provider ollama
deepcloak "How does Cloudflare Turnstile detect bots?" --depth detailed --out report.md
```

You get a cited `report.md` ending with a `🛡️ Bypassed N bot-walled sources` section, plus a `report.md.evidence.json` sidecar.

## 🧠 How it works

```
search (DuckDuckGo, no setup) ─▶ candidate URLs
        │
        ▼  for each page:
   plain fetch ─▶ Bot Wall detected? ──no──▶ use it (fast)
                        │ yes
                        ▼
                  Escalate ─▶ Stealth Fetch (CloakBrowser) ─▶ Bypass
        │
        ▼
research loop (local-deep-research) ─▶ cited report + Evidence Records
```

Stealth is heavy, so DeepCloak tries a cheap plain fetch first and only launches the stealth browser when it actually detects a Bot Wall (`--stealth auto`, the default). Use `--depth detailed`/`report` to fetch full pages where Bypasses happen.

## 🤖 Connect it to your agent (MCP)

DeepCloak runs as a stdio **MCP server** exposing `deep_research(query, depth)`, `quick_summary(query)`, and `get_evidence(run_id)`.

**Claude Code** — add to your project's `.mcp.json` (an example ships in this repo):

```json
{ "mcpServers": { "deepcloak": { "command": "deepcloak", "args": ["mcp"] } } }
```

**Codex** — add to `~/.codex/config.toml`:

```toml
[mcp_servers.deepcloak]
command = "deepcloak"
args = ["mcp"]
```

Then your agent can call `deep_research` and read bot-walled sources directly. Prefer a slash-style skill? Drop [`skill/SKILL.md`](skill/SKILL.md) into `~/.claude/skills/deepcloak/`.

## ⚙️ Configuration

| Flag | Default | Notes |
| --- | --- | --- |
| `--depth` | `detailed` | `quick` / `detailed` / `report` |
| `--engine` | `duckduckgo` | `searxng` / `auto` |
| `--stealth` | `auto` | `always` / `off` |
| `--provider` / `--model` | auto-detected | `OPENAI` → `ANTHROPIC` → `GEMINI`, or `ollama` |
| `--respect-robots` | off | honor robots.txt |
| `--proxy` | — | SOCKS5 for the Stealth Fetch |

## ⚠️ Responsible use

DeepCloak Bypasses bot-detection. **You are responsible for having the right to access whatever you fetch.** robots.txt is **ignored by default**; pass `--respect-robots` to honor it ([ADR-0002](docs/adr/0002-ignore-robots-by-default.md)). Don't use it to violate sites' terms or the law.

## 🛠️ Built on

[`local-deep-research`](https://github.com/LearningCircuit/local-deep-research) (MIT) + [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser) (MIT), via pip — no vendored code. Domain glossary in [CONTEXT.md](CONTEXT.md); design decisions in [docs/adr/](docs/adr/); contributing guide in [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

<div align="center">

**If DeepCloak read a page your last tool gave up on, drop a ⭐ — it helps others find it.**

Built by **[Mrbaeksang](https://baeksang.dev)** · [baeksang.dev](https://baeksang.dev) · [contact@baeksang.dev](mailto:contact@baeksang.dev)

[![Star History Chart](https://api.star-history.com/svg?repos=Mrbaeksang/deepcloak&type=Date)](https://star-history.com/#Mrbaeksang/deepcloak&Date)

</div>
