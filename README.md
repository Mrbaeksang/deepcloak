<div align="center">

# 🛡️ DeepCloak

### Deep research that reads the *whole* web — even pages behind Cloudflare, Datadome, Turnstile & reCAPTCHA.

[![CI](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml/badge.svg)](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![MCP native](https://img.shields.io/badge/MCP-native-8A2BE2.svg)](#use-it-from-an-ai-agent-mcp)

**English** · [한국어](README.ko.md) · [简体中文](README.zh-CN.md)

</div>

---

Every other local deep-research tool stops at the first **Bot Wall**. A relevant source sits behind Cloudflare? It gets a `403`, drops the source, and quietly hands you a thinner report — and you never find out what it missed.

**DeepCloak doesn't.** When a plain fetch hits a Bot Wall, it **Escalates** that URL to a **Stealth Fetch** and **Bypasses** the wall — then tells you exactly how many sources it had to break through.

It's a thin orchestrator over two great projects: [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research) (the research loop) and [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser) (the stealth browser). Local-first, MIT, and usable as a **CLI**, an **MCP server**, and a **Claude skill**.

## ✨ Why it's different

|                              | Plain deep research | **DeepCloak** |
| ---------------------------- | :-----------------: | :-----------: |
| Reads open web               |          ✅          |       ✅       |
| Reads Cloudflare/Datadome/Turnstile/reCAPTCHA pages | ❌ (dropped silently) | ✅ **Bypassed** |
| Tells you which sources were walled | ❌ | ✅ Evidence Record |
| Local-first (no API key required) | ✅ | ✅ |
| Fast on open pages (stealth only when needed) | — | ✅ plain-first, Escalate on detection |

> **Verified live:** on `local-deep-research==1.6.11` + `cloakbrowser==0.3.31`, DeepCloak bypassed Cloudflare **Turnstile** on `nowsecure.nl` in ~5s, while an open page (`example.com`) stayed on the fast plain path (~0.1s). See [`showcase/sample/evidence.json`](showcase/sample/evidence.json).

## 🚀 Quickstart

```bash
pip install deepcloak
deepcloak setup                       # downloads the stealth browser
export OPENAI_API_KEY=...             # or ANTHROPIC_API_KEY / GEMINI_API_KEY — or --provider ollama
deepcloak "How does Cloudflare Turnstile detect bots?" --depth detailed --out report.md
```

You get `report.md` (cited, ending with a `🛡️ Bypassed N bot-walled sources` section) and a `report.md.evidence.json` sidecar.

## 🧠 How it works

```
search (DuckDuckGo, no setup) ──► candidate URLs
        │
        ▼
   for each page:  plain fetch ──► Bot Wall detected? ──no──► use it
                                         │ yes
                                         ▼
                                   Escalate → Stealth Fetch (CloakBrowser) → Bypass
        │
        ▼
research loop (local-deep-research)  ──►  cited report + Evidence Records
```

Stealth is heavy, so DeepCloak tries a cheap plain fetch first and only spins up the stealth browser when it actually detects a Bot Wall (`--stealth auto`, the default). Force it with `--stealth always` or disable it with `--stealth off`.

> **Depth matters for bypass:** `--depth detailed` / `report` fetch full pages (where Bypasses happen). `--depth quick` is snippet-based and rarely fetches full pages.

## 🤖 Use it from an AI agent (MCP)

```bash
deepcloak mcp        # stdio MCP server
```

Tools: `deep_research(query, depth)`, `quick_summary(query)`, `get_evidence(run_id)`. Or drop the bundled [`skill/SKILL.md`](skill/SKILL.md) into `~/.claude/skills/deepcloak/` to use it as a Claude skill.

## ⚙️ Configuration

| Flag | Default | Notes |
| --- | --- | --- |
| `--depth` | `detailed` | `quick` / `detailed` / `report` |
| `--engine` | `duckduckgo` | `searxng` / `auto` |
| `--stealth` | `auto` | `always` / `off` |
| `--provider` / `--model` | auto-detected | from `OPENAI_API_KEY` → `ANTHROPIC_API_KEY` → `GEMINI_API_KEY`, or `ollama` |
| `--respect-robots` | off | honor robots.txt |
| `--proxy` | — | SOCKS5 for the Stealth Fetch |

## ⚠️ Responsible use

DeepCloak Bypasses bot-detection. **You are responsible for having the right to access whatever you fetch.** robots.txt is **ignored by default**; pass `--respect-robots` to honor it ([ADR-0002](docs/adr/0002-ignore-robots-by-default.md)). Don't use it to violate sites' terms or the law.

## 📄 License & credits

MIT — see [LICENSE](LICENSE). Built on [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research) and [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser) (both MIT); see [NOTICE](NOTICE). Glossary in [CONTEXT.md](CONTEXT.md); design decisions in [docs/adr/](docs/adr/).
