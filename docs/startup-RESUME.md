# Startup axis — RESUME HERE

Pick-up note for the **startup (AI supply-side) thread only**. Not the atlas/register work.

## The three files that hold the state
- `docs/startup-sources.md` — methodology: raison d'être, the rotten-fruit independence rule, source types A–M.
- `docs/startup-sources.csv` — the ledger, 63 sources, one per row. `verdict` = scrapeability, `gate` = fit.
- `docs/startup-sources.json` — same 63 + nested `scrape:{entry,iterate,method,checked}` recipes.

## Where we stopped
- 63 sources scanned. Verdicts: **9 GREEN**, 33 YELLOW, 20 RED, 1 RED-usevariant.
- Gate (fit): 57 OK, 6 OVERKILL (investment-research firms like MAGNiTT — overkill for our need).
- **14 scrape recipes recorded.** Concrete handles found (`checked=Y`): SBIR, CORDIS, YC, Sequoia, Index, Elevate Greece, a16z, ai-startups-europe, CES. Needs-devtools (`P`): Techstars, J-Startup, Enterprise SG, Startup India, Hub71.

## What the axis IS (bounds, user-set)
- Its own entity class — **NOT** register rows. AI *builders*, not consumers.
- A startup = a **real incorporated company** (VAT, founders, capital raised). Not a Crunchbase clone, not a bedroom SaaS.
- Minimum viable fact per startup: **"AI startup X exists in country Y, does Z"** + investment if publicly disclosed.
- All countries, anti-US-bias. Targets cited: a French AI fintech, a Dutch AI marketing tool, a Japanese AI delivery startup.

## Hard rules (settled)
- Rotten-fruit rule: pay-to-list / lead-gen → REJECT (killed ai-startups.pro, ai-startups.pro).
- Paywalls excluded. reCAPTCHA circumvention refused (independent of clearance).
- "Blocked ≠ unreachable" — read the SERP snippet/index, don't fetch the wall.
- Models never fabricate: real source or drop the row.

## The unfinished decision (blocks any ingest)
**The startup gate is not designed yet.** Before ingesting anything, decide three things:
1. **Bound** — what qualifies (incorporation? min raise? AI-native test?).
2. **Evidence rule** — what proof pins a row (the demand-side analogue took days).
3. **Schema** — the startup entity's fields + how it joins the atlas.

## Cleanest first ingest when we resume
**YC `all.json`** — `https://yc-oss.github.io/api/meta.json` → `all.json`. 6085 companies, ~2416 AI-tagged, has founders/batch/country. Static, no auth, no scrape. Best "480p" reality check: pull it, filter AI, look at one real row before building anything.
