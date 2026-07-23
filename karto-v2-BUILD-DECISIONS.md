# KARTO V2 — locked build decisions (owner-approved)

Answers to the spec's open questions (from the owner):
1. **Routing → WAY 1: hash routing** inside the single SPA (`#/company/bnp-paribas`).
   No multi-file build. Keep the self-contained offline file.
2. **No resweep now → make do without size data.** universe has NO market_cap/revenue/
   employees. Adapt every size-dependent module (see below). Resweep later.
3. **No LLM.** A2 = regex-only. C2 = tiers 1–2 only (chips + dictionary), drop tier-3 LLM.
4. **Ship Phase 1 fast, then DO the rest — do not defer.** Grind all phases, adapting.

## Per-module adaptation to "no size data"
- **A1 universe.csv:** build from the 35 `data/universe/*.tsv` (company,CC,index,sector).
  Columns: company,cc,vertical,index,raw_sector,searched=1. NO size cols (add later).
  L0-silent = in universe, absent from register. This still fully works.
- **B1 normalized:** drop per-$B-revenue / per-10k-emp (need size). KEEP: density
  (confirmed/searched), deployments-per-company. Emit `companies[]` w/ size fields = null.
- **B2 benchmarks:** percentile by deployment count / confirmed / proof-rate — NO size needed. Full.
- **D4 silent list:** works; sort by peer-gap (median peer deployments − 0), not size.
- **B5 prospect_score:** compute from confirmed-activity + proof-absence + vendor-absence
  (no size term). Documented formula, 0–100.
- **A2 value extraction:** regex only (currency + scale counts). No LLM classify pass.
- **A3 commitments:** manual/regex from existing text; pilot = Financial Services. Small.
- **A5 freshness:** no `last_verified` col yet → backfill from `date`; staleness from that.

## Build order (spec's sequence, adapted)
P1: B3 (4-state verdict) → D8 (trust polish + meta block)
P2: A1 (universe.csv) → B1 (companies[]) → B2 (benchmarks) → D4 (silent view)
P3: A2 (regex claims) → A5 (freshness from date) → D6 (hype detector)
P4: B4 (momentum from date) → D5 (trends view)
P5: A4 (maturity L0–L4) → B6 (findings join) → D1 (company page, hash route)
P6: C1 (compare fn) → C2 (chips+dict filter) → D2 (compare view) → D3 (persona tiles)
P7: B7 (insights) → B5 (scores) → A3 (commitments) → C3 (static API, hash-JSON) → D7 (export)

Each phase committed + pushed when its tests pass. atlas.json gains a `meta` block first.
