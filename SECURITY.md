# Security Policy

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue.

- Email: **contact@baeksang.dev**
- Or use GitHub's [private vulnerability reporting](https://github.com/Mrbaeksang/deepcloak/security/advisories/new).

Include what you found, how to reproduce it, and the impact. We aim to acknowledge
within a few days and will credit you in the fix unless you prefer otherwise.

## Supported versions

DeepCloak is pre-1.0; fixes land on the latest release. Pin a version in production.

## Scope & responsible use

DeepCloak **Bypasses** bot-detection (Cloudflare, Datadome, Turnstile, reCAPTCHA) so a
research agent can read pages a person with a browser could read. **You are responsible
for having the right to access whatever you fetch** — don't use it to violate a site's
terms or the law. robots.txt is ignored by default; pass `--respect-robots` to honor it.

This is a thin orchestrator over [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)
and [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser); vulnerabilities in those
upstreams should also be reported to them.
