# Sample data (real, from live runs)

Captured on `local-deep-research==1.6.11` + `cloakbrowser==0.3.31`, local Qwen3.6 + SearXNG.

- **`evidence.json`** — a real Bot Wall bypass demo: a Stealth Fetch **Bypassed** Cloudflare
  Turnstile on `nowsecure.nl` (~5s), while `example.com` stayed on the fast plain path
  (~0.1s). This is the escalation policy working: stealth only when a wall is detected.
- **`report.md`** — a sample cited report produced by a full research run
  ("How does Cloudflare Turnstile detect bots?") via the local LLM.

These are two separate demos (the report ran in `quick` depth, which is snippet-based and
doesn't fetch full pages — so its own evidence is empty; use `detailed`/`report` for
bypass-bearing runs). The static showcase site (issue #9) will render a single canonical
run that produces both together.
