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

DeepCloak can retry a blocked page in a stealth browser so a research agent can read a page a person with a browser could read. **You are responsible for having the right to access whatever you fetch**, so don't use it to violate a site's terms or the law. robots.txt is honored by default; `--ignore-robots` overrides it and is recorded in each Evidence Record.

This is a thin orchestrator over [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)
and [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser); vulnerabilities in those
upstreams should also be reported to them.

## Private network targets

By default DeepCloak refuses localhost, private and link-local addresses and non-http(s) URLs, including on plain-fetch redirects and browser subresources. `--allow-private-urls` allows the addresses only. Known limits: the browser can still send a request to a private address reached through an HTTP redirect, although its response is discarded and not recorded as a Bypass, and a DNS answer that changes between the check and the fetch is not caught.
