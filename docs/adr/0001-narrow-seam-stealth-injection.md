# Inject Stealth Fetch through the narrowest LDR seam, monkeypatch now + upstream PR later

`local-deep-research` instantiates its HTML downloader internally (no dependency injection), so DeepCloak cannot cleanly supply a Stealth Fetch downloader from the outside. We decided to override only the narrowest seam — `AutoHTMLDownloader._fetch_html`, the method that returns a page's raw HTML — via a startup monkeypatch (`ldr_shim.install()`). Routing through this seam runs every HTML fetch through `fetch_router` (plain → Escalate → Stealth Fetch) while LDR's own text extraction still runs on the HTML we return, so we reuse it. We pin the LDR version with `==` and will open an upstream PR adding a pluggable HTML-downloader hook so the monkeypatch can later be dropped.

## Considered Options

- **Patch `ContentFetcher._get_downloader` wholesale** — broad surface, breaks easily on upstream refactors. Rejected.
- **Block on the upstream PR before shipping** — robust but indefinite merge timeline. Rejected for v1.
- **Fork LDR** — heavy ownership, derivative optics, loses upstream improvements. Rejected (we chose a thin pip-dependency orchestrator).

## Consequences

The shim depends on internal LDR symbols, so the LDR version must stay pinned and the seam re-verified on upgrade. Once the upstream hook merges, switch `ldr_shim` from monkeypatch to the official hook and relax the pin.
