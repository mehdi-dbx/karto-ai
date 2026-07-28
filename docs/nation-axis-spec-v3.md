# KARTO — Nation-State AI Axis: SPEC v3 (post second adversarial review)

Supersedes `nation-axis-spec-v2.md`. Audit trail: `nation-axis-review-brief.md` (v1) →
review 1 → `nation-axis-spec-v2.md` → review 2 → this. Verdict of review 2:
**ship-with-changes**, conditional on 5 fixes + 1 product decision.

The reviewer's meta-point, accepted: **v1's failures were design rot (schemas that
manufacture confident falsehoods); v2's are operability gaps (correct disciplines whose
defined sources can't feed them).** The fix is wiring in sources that already exist, not
redesign. v3 does that wiring and answers the held-ground calls with corrected mechanisms.

---

## 0. Disposition of review 2

| # | Finding | Ruling |
|---|---------|--------|
| F1′ | `procurement_access` has no sourcing stream → fabrication relocated to the keystone | **Concede.** Wire in a 4th stream: WTO GPA membership, USTR NTE, EU market-access reports, World Bank procurement indicators. No source → `unknown` (not a prior-driven guess). |
| F2′ | ethics: removing "balanced" mandates fabricating tails; conflates written vs practiced | **Concede mechanism.** Restore honest mode as `stated-generic`; a tail value (`state-control`/`rights-based`) **requires a non-strategy primary source** (law, enforcement action), never the strategy PDF. |
| F3′ | chokepoint: global static fact harvested as country data; my own list missed US + China | **Concede.** Move to a **hand-curated static registry** (one sourced table, incl. US & China), joined at build time, never touched by extraction. |
| F4′ | R2 allowlist mostly doesn't publish MW; `unknown` will dominate 60+/89; aggregators are a 3rd tier | **Concede.** Add `aggregator` source tier (lower trust). Accept `unknown`-dominant as honest; see F9′ for the product consequence. |
| F5′ | `appropriated` honest→unreachable; **headline $ figure was dropped** | **Concede.** Restore `funding_figure` (+provenance). `appropriated` needs primary budget instrument; else `announced`. |
| F6′ | `chip_tier` enum encodes a **rescinded** regime | **Concede.** Store the **instrument**, not a tier: `{controlling_rule_or_deal, effective_date, source}`. |
| F7′ | a URL is not evidence once the page dies/changes | **Concede.** At harvest, capture Wayback snapshot + retrieved-text hash + retrieval date. |
| F8′ | audit has no acceptance gate = measurement theater | **Concede.** Pre-commit per-class thresholds (below), before run 1. |
| F9′ | null-cascade may leave `opportunity_read` null for >half the atlas | **PRODUCT FORK — needs your call (below).** |
| F10′ | `procurement_channel_exists` near-constant; `military: prohibited` ill-defined; `source_lang` inert; low-coverage stratum should be picked post-run by null-density | **Concede all four.** |

Zero held-ground survives *as-mechanism*; both instincts survive *as-corrected*. Good — the review earned it.

---

## 1–3. Context / persona / data state

Unchanged from v2. KARTO = evidence-gated atlas; third actor = nation-state; persona =
state-agency counselor/contractor; insight = **opportunity = gap × accessibility**; 89
countries have source URLs only, nothing yet parsed.

## 4. Sourcing streams — v3 (the operability fix)

Four streams now, each with an **allowlist** so no field is filled from schema pressure:

1. **PDF** (strategy doc, pdftotext) → apparatus, sectors, ethics-as-*written*, has_strategy.
2. **News** (Serper, tier=`secondary`) → funding announcements, champion, military signals, `confirmed_active`.
3. **Infra** (allowlist: DC trackers, hyperscaler announcements, utility/grid filings, IEA; tier=`aggregator`) → compute band, sovereign-vs-hyperscaler, power. Generic news **cannot** fill these.
4. **Procurement/trade** (allowlist: WTO GPA, USTR NTE, EU market-access, World Bank; tier=`primary`) → `procurement_access`. *(NEW — kills F1′.)*

**Chokepoint registry** is NOT a stream — it's a static hand-curated table joined at build (F3′).

## 5. Schema v3

Every volatile field carries `{ value, source_url, source_date, source_tier, snapshot, text_hash }` (F7′).
`source_tier ∈ primary | secondary | aggregator` (F4′).

| Field | Values | Notes |
|-------|--------|-------|
| `has_strategy` | yes / in-dev / none | none = signal (Switzerland) |
| `funding_figure` | amount + currency + year | **restored** (F5′); provenance-bound |
| `funding_status` | announced / appropriated / unknown | `appropriated` ⇒ **primary budget instrument** or degrade to `announced` |
| `procurement_access` | open-tender / champion-gated / offset-localization / closed / unknown | fed by stream 4 only (F1′) |
| `apparatus` | office + implementing ministry (+`confirmed_active`) | machinery as *staffed/funded* (F10) |
| `compute_band` | <10MW / 10–100 / 100–1000 / GW-scale / unknown | bands; allowlist; `unknown` common & honest (F4′) |
| `compute_control` | sovereign / hyperscaler-hosted / mixed / unknown | — |
| `chip_regime` | `{rule_or_deal, effective_date, source}` freeform+date | **not an enum** (F6′) |
| `power_posture` | abundant / constrained / unknown | — |
| `chokepoint_node` | from static registry: none / <which> | build-time join, not harvested (F3′) |
| `national_champion` | name / none | — |
| `military_ai` | active / stated / not-found | `prohibited` **dropped** unless a qualifying instrument is cited (F10). **SURFACED as fact, never censored** — military AI posture is critical intelligence (drones, doctrine, lethal-autonomy stance); recorded plainly, sourced, held to the same evidence bar as every field. Only fabrication and operational how-to are out of bounds — same as everywhere. |
| `ethics_stance` | stated-generic / rights-based / permissive / state-control / not-stated | tails need **non-strategy primary source** (F2′) |
| `sectors[]`, `region`, `source_lang` | — | low-resource-lang records auto-join audit (F10) |

Freeform: `general_idea` (prose).

Payload: `opportunity_read` — must cite premise field-values+sources or emit **null**;
military/defense opportunity is stated as FACTUAL OBSERVATION when real and sourced (surfaced, not hidden, not censored); never fabricated and never framed as operational how-to. (Traceable, not guaranteed-correct — F9′ residual noted.)

## 6. Audit — with acceptance gate (F8′)

Pre-committed **before** run 1:
- Volatile field (funding, compute, procurement, chip) **>10% wrong → that column does not ship this run.**
- **Any fabricated-with-source case → pipeline bug, halt** (violates R1, the whole point).
- Stratified sample **2 top / 2 mid / 2 low-coverage**; low-coverage stratum chosen **after run 1 by null-density**, not by "small country" proxy (F10).
- Field-audited (not country-audited) for volatile columns; **every non-null `compute_band` in run 1 hand-checked**.

## 7. THE PRODUCT FORK — needs your decision (F9′)

The honest streams (F4′ compute `unknown`-dominant, F5′ `appropriated` rare, F1′ procurement
often `unknown`) mean the null-emission rule on `opportunity_read` will fire a lot. Two ways
to ship, and it's a **product decision, not a technical one**:

- **Option A — Full 89, honest sparsity.** Run all 89; `opportunity_read` is null wherever
  premises are missing. Result: a complete map where maybe half the payload cells are null.
  Honest (absence-is-signal), but the flagship field is empty for much of the atlas.
- **Option B — Scoped run 1 (~30 solid).** Run only the ~30 countries where compute +
  procurement + funding are actually sourceable (US, China, EU-majors, UK, Gulf, India,
  Japan, Korea, Canada, Australia, Singapore, Brazil…). Fuller records, real
  `opportunity_read` on every one; expand the frontier in run 2 as sources are found.

**Recommendation: B.** A 480p atlas of 30 countries with sharp, sourced opportunity reads
beats a 4K map that's half-empty in exactly the payload field the persona came for. The
other ~59 still exist as source-URL rows (the v-current CSV) — they're *listed*, just not
yet *harvested*. Expansion is additive, same as the demand-side grinds.

## 8. Non-negotiables (unchanged)

No fabrication; field-level source+snapshot or null. Facts vs inference separated;
`opportunity_read` premise-citing. "Synthetic" ≠ "loose." No LLM at build-time.

---

## 9. Build readiness

With F1′–F8′ + F10′ wired in, the design is **ship-with-changes → buildable.** Remaining
gate is the §7 fork. Once you pick A or B, the harvester is:
`nation-sources.csv → 4 allowlisted streams → Flash + schema v3 (field-provenance +
snapshot) → nation-facts.{csv,json}`, resumable, paced, ~$0, Claude audits the stratified
sample against the §6 gate. Chokepoint registry authored by hand once.
