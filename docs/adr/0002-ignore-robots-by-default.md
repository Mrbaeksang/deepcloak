# Ignore robots.txt by default, with a `--respect-robots` opt-in

DeepCloak ignores robots.txt by default and offers `--respect-robots` as an opt-in mode. The README places legal responsibility on the user ("you must have the right to access the content you fetch; you are liable for your use"). robots.txt is a crawl *policy*; a Bot Wall is bot *detection*. We frame DeepCloak as defeating detection on content the user is entitled to read, not as a license to ignore access policy — but the default favors capability.

## Consequences

This default carries reputational and legal risk — the tool can be labeled abuse tooling and reported, and a user-liability disclaimer is a weak legal shield. Accepted as a deliberate trade-off for the project's capability-first, viral positioning. A `--respect-robots` mode and a default self-protective per-domain rate limit (distinct from robots) mitigate the worst outcomes.
