# Honor robots.txt by default, with an `--ignore-robots` opt-out

Supersedes [ADR-0002](0002-ignore-robots-by-default.md).

DeepCloak is positioned as an evidence-first research tool. It honors robots.txt by default and offers `--ignore-robots`, which is recorded in each Evidence Record. Plain requests send a `DeepCloak/<version>` User-Agent.

When robots.txt can't be read we follow RFC 9309: a 4xx response allows fetching, and a server or network error disallows it. Rules apply to Stealth Fetch as well as plain fetch, because the check runs first. A host's file is read once per run. The old `--respect-robots` flag is still accepted and does nothing.

## Consequences

Runs can read fewer sources, and an unreachable robots.txt skips that host. Skips appear in Evidence Records so the user can see what was left out. In a sample of 12 well-known sites on 2026-11-06, plain-fetch results were the same with a Chrome User-Agent and the DeepCloak one: 8 of 12 returned usable pages with each. That sample is small and may change.
