---
name: deepcloak
description: Deep research that reads the whole web, including pages behind a Bot Wall (Cloudflare, Datadome, Turnstile, reCAPTCHA). Use when the user asks for a researched, cited answer — especially on topics where sources are likely paywalled, rate-limited, or bot-protected, or when an ordinary search/research tool returned thin or blocked results.
---

# DeepCloak

Run a Deep Research that Bypasses Bot Walls and returns a cited report plus an Evidence Record of which sources required a Bypass.

## How to run it

**Prefer the MCP tools** (the server applies the stealth shim in-process):

- `deep_research(query, depth)` — `depth` is `quick` | `detailed` | `report`. Returns a cited markdown report ending with a `🛡️ Bypassed N bot-walled sources` section.
- `quick_summary(query)` — a fast, shallow answer.
- `get_evidence(run_id)` — the Evidence Records (JSON) of a prior run; pass `"last"` for the latest.

If the MCP server is not connected, **fall back to the CLI**:

```bash
deepcloak "<query>" --depth detailed --out report.md
```

The report is printed (or written to `--out`, with a `<out>.evidence.json` sidecar).

## Notes

- Needs one LLM key (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`) or `--provider ollama`. Run `deepcloak setup` once to install the stealth browser.
- Default search is DuckDuckGo (no setup). robots.txt is ignored by default; pass `--respect-robots` to honor it. The user is responsible for having the right to access the content.
- When you report results, mention how many sources were Bypassed — it tells the user the report covered walled content other tools would have dropped.
