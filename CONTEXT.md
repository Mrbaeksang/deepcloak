# DeepCloak

A local-first deep research tool with explicit fetch decisions and Evidence Records, including for pages behind anti-bot defenses. It pairs an iterative multi-source research loop with a stealth browser fetch layer.

## Language

**Bot Wall**:
An anti-bot defense that blocks a plain HTTP fetch — Cloudflare, Datadome, Turnstile, reCAPTCHA, or aggressive rate-limiting. Detecting one triggers an Escalation.
_Avoid_: block, captcha, firewall, WAF

**Stealth Fetch**:
Retrying a page in the stealth browser after a Bot Wall was detected. It may or may not succeed.
_Avoid_: scrape, crawl, render

**Escalation**:
The switch from a plain fetch to a Stealth Fetch for a single URL, made because a Bot Wall was detected. One Escalation is one unit of evidence.
_Avoid_: retry, fallback, upgrade

**Bypass**:
A Stealth Fetch that succeeds after an Escalation — content obtained where the plain fetch was walled, and that passes a Bot Wall re-check.
_Avoid_: crack, defeat, evade

**Evidence Record**:
The per-URL fact captured during a research run: the URL, the Bot Wall kind, whether it Escalated, whether the Bypass succeeded, the plain-fetch status, and timing. The showcase site and the report's evidence section are rendered from these.
_Avoid_: log, trace, metric

**Deep Research**:
A single user query expanded into an iterative loop of searches and reads across many sources, ending in a cited report. The unit of work a user requests.
_Avoid_: query, search, lookup
