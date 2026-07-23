# KARTO V3 — locked build decisions

Plan: karto-v3-build-plan-reviewed.md (wins over companion doc on build order).
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

## Progress
- [x] Step 1 vertical dedup (done in prior task; alias-map record added here in V3)
- [ ] Step 2 money.csv unify + cook repoint
- [ ] Step 3 question nav  · [ ] 4 next-block · [ ] 5 teasers
- [ ] Step 6 staging gate
- [ ] Step 7 usecase taxonomy · [ ] 8 usecase UI
- [ ] Step 9 vendor layer
- [ ] Step 10 changelog · [ ] 11 persona templates
- [ ] Step 12 resweep (finale)
