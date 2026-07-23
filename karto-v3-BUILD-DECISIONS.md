# KARTO V3 — locked build decisions

Plan: karto-v3-build-plan-updated-2.md (authoritative; supersedes -reviewed; wins over companion doc on build order).
Companion specs: karto-v3-implementation-instructions.md (N1-3, A7/D9, A6/D10, H1/H2, B7-r).
Strategy: plumbing-first, null-tolerant, visible fallbacks, ONE resweep finale (Step 12).

## Answers to open questions (owner handed the reviewed plan = approval)
1. **LLM policy (the blocker, now answered):** NEVER at site runtime. Allowed as a one-time
   BUILD-TIME parser: dictionary/regex first, then ONE Claude pass on the residue, outputs
   committed to CSV with a `method: regex|llm` column, reviewed via the Step 6 gate. (Steps 7, 9.)
2. **Step 1 dedup:** already done by mutating register.csv (22->20, backed up, raw_sector preserved).
   Divergence from spec (which wanted cook-time alias map, register untouched). Reconciliation:
   add data/vertical_aliases.csv as the documented {raw,canonical} map (idempotent no-op now,
   serves future dedups + the spec's record requirement). Not reverting the register.
3. **Step 2:** retrofit to full 14-col money.csv; repoint cook + hype + company pages to money.csv;
   retire claims.csv + commitments.csv (deprecation note one release).
4. **Disabled questions (Step 3):** render GREYED "coming soon" (not hidden) — shows the roadmap,
   matches the visible-fallback rule. Flip to enabled as their step ships.
5. **12 question wordings:** use the reviewed plan's draft text; ids stable.
6. **Gate auto-apply (Step 6):** OFF by default.
7. **Taxonomy seed (Step 7) / vendor dict seed (Step 9):** propose inline from real register text,
   gate before merge.
8. **Resweep (Step 12):** one orchestrated run — size enrichment (~2,468 cos) + FS commitments
   pilot + freshness — through the Step 6 gate. The finale.

## Routing translation (V3 targets -> shipped hash routing)
All targets use `#/...`. Existing V2 routes: #/silent #/compare #/trends #/hype #/insights(=signals)
#/company/{slug} #/grid #/world. New V3 routes: #/usecases #/usecase/{p} #/vendor/{slug} #/changelog
#/companies (filterable list) #/signals (alias/rename of insights w/ type+p params).

## Plan update-2 (karto-v3-build-plan-updated-2.md) — hardening for Steps 6 & 12
STEP 6 gate — hard enforcement rules to implement:
- Additive-by-default: each job declares read/write tables+columns upfront. UPDATE only declared
  columns, INSERT only declared tables. Overwrite of non-null / row delete = CONFLICT (own review
  section, never auto-applied).
- Immutable keys: row_ids + company keys permanent (money/usecases/vendors join on them). Gate CODE
  rejects any proposal touching a key.
- Dry-run cook: cook staged data in temp dir, diff atlas stats vs current; out-of-scope stat change
  fails the dry run.
- Batched apply: chunks (per-country or <=200 rows), one git commit per batch (easy revert).
STEP 12 resweep doctrine (encode in agent scripts, not just prompts):
- Register is an asset not a cache — never re-derive/re-search existing data.
- Skip-if-filled: enrichment queries only NULL cells.
- Resumable: per-batch checkpoint; crash at 1800 resumes 1801.
- Scope lock: each agent prompt states read/write contract, forbids drift.
- Delta freshness: "what's new since {last_verified}", never from zero.
- Freshness = a forever priority queue (oldest last_verified first, value/high-visibility weighted),
  fixed budget/run (~100 rows); becomes the ongoing heartbeat engine.

## Progress
- [x] Step 1 vertical dedup (done in prior task; alias-map record added here in V3)
- [ ] Step 2 money.csv unify + cook repoint
- [ ] Step 3 question nav  · [ ] 4 next-block · [ ] 5 teasers
- [ ] Step 6 staging gate
- [ ] Step 7 usecase taxonomy · [ ] 8 usecase UI
- [ ] Step 9 vendor layer
- [ ] Step 10 changelog · [ ] 11 persona templates
- [x] Step 12 resweep (finale) — use-cases 94%, FS money-in (77), size (2457); freshness=heartbeat queue built

## Step 12 plumbing-bug log (per doctrine: "if a code change is needed post-resweep, file it")
1. FS commitments counter: cook counted commitments only via register_row_id join, but
   company-level dedicated_collection rows have blank register_row_id. Fixed cook to count
   commitments by (company,cc) -> vertical. global.commitments 0 -> 77; hype money-in
   pending marker now self-clears correctly. (One code change; noted here.)
2. Silent-company size: cook read size only for register companies; silent companies (universe-only)
   hardcoded None. Fixed to read size from UNI for silent rows too. 463/491 now sized -> silent
   size-sort + size-pending marker self-clear.
3. B1 normalized metrics were never computed (columns were null so math was deferred). Wired
   compute-when-present: per_bn_revenue, per_10k_emp. 2,352 companies now carry them.
   (These were genuine plumbing misses — the plan's "zero code change" ideal wasn't fully met for
   size-dependent B1/D4; filed honestly. The marker/self-clear logic DID work as designed.)
