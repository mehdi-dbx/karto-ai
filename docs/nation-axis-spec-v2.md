# KARTO — Nation-State AI Axis: SPEC v2 (post-adversarial-review)

Supersedes the design in `nation-axis-review-brief.md`. That brief + the review it drew
are the audit trail; this is the revised spec. **For the next adversarial reviewer:** the
prior pass returned **rethink** and killed/rebuilt three things. Attack the *revised*
design — especially the two places the author refused to concede (§7 held-ground). Same
mandate: findings that kill a column beat style notes; rank most-fatal-first; end with
**ship / ship-with-changes / rethink.**

---

## 1. Context (unchanged)

KARTO: evidence-gated atlas. Demand axis = ~2,187 listed companies, each AI deployment
gated to a real source URL; additive, immutable keys, no LLM at build time, no-source →
dropped-not-invented, absence-is-signal. Supply axis (startups) in progress. This is the
**third actor: the nation-state.** The spine must not be poisoned.

## 2. Persona + governing insight — REVISED (was F3)

Persona unchanged: a **nation-state AI policy counselor / state-agency contractor** who
needs to place a country on the geopolitical AI chessboard to **find profit
opportunities to accompany it**.

Governing insight, corrected from the review:

> **opportunity = gap × accessibility** — NOT "gap = inverse of capability."
> The review proved the old premise half-false: the US federal government is the largest
> AI procurement market on earth (leaders are not "nothing to sell"); and funded-but-lacking
> rarely means *open* — Gulf gaps are champion-gated (G42/HUMAIN), India is L1+localization,
> Indonesia is offset-driven. So a capability gap is only an opportunity **if it is
> accessible.** Leaders = huge market × low external accessibility (a matrix cell, not an
> exclusion). This added the missing variable (`procurement_access`) the §8 filter turned on.

## 3. Data state (unchanged, honest)

89 countries have a discovered **official source URL** only (`docs/nation-sources.csv`).
**Nothing behind the links has been read/parsed/verified.** This spec is the extraction pass.

## 4. The three structural rethinks (what the review forced)

These block everything else and are built first, in order:

### R1 — Per-field provenance + per-field `as_of` (was F2 + F6, the keystone)
Provenance binds to the **field**, not the record. Every volatile claim is:
`{ value, source_url, source_date, source_tier }`.
- A field with no field-level source is **null**. No exceptions.
- `source_tier`: `primary` (gov doc, budget law, filing) | `secondary` (press/rewrite).
- This is what makes R2/R3 and all extraction auditable instead of laundered. Record-level
  `sources[]` (the old design) is abolished — it allowed a fabricated number to "trace" to
  five URLs that never contained it.

### R2 — Infra as bands + source-allowlist (was F1, the fabrication engine)
- Datacenter capacity is a **band, never a number**: `<10MW / 10–100 / 100–1000 / GW-scale / unknown`.
- `unknown` is a first-class, expected, common value.
- **Source allowlist** for compute fields: datacenter trackers (Data Center Map, Cloudscene),
  hyperscaler region announcements, utility/grid filings, IEA. A generic news hit **cannot**
  populate a compute field → `unknown`.
- `ai_capable` is NOT a boolean; it appears only as a note when a source explicitly says
  GPU/high-density.

### R3 — `procurement_access` axis (was F3, the missing variable)
New axis: `open-tender / champion-gated / offset-localization / closed / unknown`.
Without it, the persona's core filter ("funded + thin-compute + **open** procurement")
cannot be run — the old schema encoded no notion of openness.

## 5. Schema v2 (full)

Structured, comparable axes (each volatile field carries the R1 provenance object):

| Field | Values | Notes |
|---|---|---|
| `funding` | announced / appropriated / unknown | `appropriated` requires a **primary** budget-instrument source or it degrades to `announced` (was F4) |
| `procurement_channel_exists` | yes / no / unknown | durable replacement for the perished `open-now` (F4) |
| `procurement_access` | open-tender / champion-gated / offset-localization / closed / unknown | NEW (R3/F3) |
| `apparatus` | named office + implementing ministry | + `confirmed_active` sub-flag from news stream — machinery *as staffed/funded*, not just as designed (F10) |
| `compute` | MW **band** · sovereign-vs-hyperscaler · `chip_tier` · power posture | bands + allowlist (R2); `chip_tier` re-anchored to *current* export regime + dated (F6) |
| `chokepoint_node` | none / \<which\> | replaces `stack_position`; boolean+detail (§7 held-ground) |
| `national_champion` | name / none | dictates direct-sale vs partner-with-champion |
| `military_ai` | active / stated / not-found / prohibited | `not-found` (never "absent"); **barred from opportunity leads** (F5/F9) |
| `ethics_stance` | rights-based / permissive / state-control / not-stated | "balanced" REMOVED — no mush bucket (§7 held-ground) |
| `frontier_control_exposure` | imposes / subject-to / neutral | dated (F6) |
| `sectors[]`, `region`, `has_strategy`, `source_lang` | — | `source_lang` + machine-translation flag (F10 language bias) |

Freeform: `general_idea` — prose synthesis.

Payload: `opportunity_read` — **must cite the specific field-values + sources it rests on**
("because funding=appropriated [src], compute=<10MW [src], procurement_access=open-tender
[src]"). If it cannot name its premises with sources, it emits **null** (was F7).
**Barred** from generating sell-into leads for `military_ai` and state-surveillance (F9).

## 6. Harvest + audit — REVISED

- Three streams unchanged in kind (PDF / news / infra) but **infra is allowlisted** (R2)
  and **news is tier-tagged** (R1).
- pdftotext-only, flag failures (kept — scanned-PDF risk is low per review; the real bias
  is **English-publishing states**, now recorded via `source_lang`, F10).
- Extraction: Gemini 2.5 Flash, fixed schema, ~$0 free tier, outside orchestrator context.
- **Audit (was F8):** stratified — 2 top-tier + 2 mid + 2 low-coverage countries; audit
  **fields not countries** for volatile columns; **every non-null compute band in run 1 is
  checked** (fabrication pools there per R2).

## 7. Held ground — the two the author refused to delete (attack these first)

The reviewer recommended deleting both for low entropy. The author kept them, sharpened.
**Reviewer: is this stubbornness or is it right?**

- **`ethics_stance` kept, "balanced" removed.** Argument: the field's *mode* is useless
  (every strategy says "responsible & human-centric") but its *tails* are first-order
  geopolitics (China/Gulf state-control vs EU rights-based). Removing the mush value forces
  a discriminating call. Claim: a low-entropy field whose rare values are decisive is a
  flag, not dead weight. **Counter-attack invited:** does forcing the call just push the
  model to fabricate a tail where the truth is "balanced"?
- **`stack_position` → `chokepoint_node` flag.** Argument: ~80/89 are `none`, but the ~9
  node-holders (TSMC-Taiwan, ASML-NL, memory-Korea, materials-Japan, design-Israel) are the
  highest-signal cells on the board and feed the dependency read the opportunity model needs.
  Collapsed to boolean+detail so it costs one word for the 80 and flags the 9.
  **Counter-attack invited:** is "who holds a chokepoint" already common knowledge that adds
  nothing per-country, i.e. a global fact masquerading as a country field?

## 8. Non-negotiables (unchanged)

No fabrication; field-level source or null. Facts vs inference visibly separated;
`opportunity_read` labelled + premise-citing. "Synthetic" ≠ "loose." No LLM at site
build-time.

## 9. What changed from v1, in one table (for the reviewer's orientation)

| Finding | v1 | v2 |
|---|---|---|
| F1 | raw MW number, any source | bands + source allowlist; `unknown` common |
| F2 | record-level `sources[]` | per-field `{value,url,date,tier}`; no source → null |
| F3 | gap = inverse-capability | opportunity = gap × **accessibility**; new `procurement_access` |
| F4 | announced/appropriated/open-now | announced/appropriated(+primary)/unknown; `open-now`→`procurement_channel_exists` |
| F5 | `military_ai: absent` | `not-found`; barred from opportunity leads |
| F6 | no staleness | per-field `as_of`; chip_tier re-anchored |
| F7 | labelled inference | premise-citing or null; military/surveillance barred |
| F8 | 5-country audit | stratified 2/2/2 + full compute-band audit |
| F10 | ethics/stack as-is | `ethics` de-mushed; `stack`→`chokepoint_node`; `source_lang` added |

**Deliverable for next reviewer:** ranked findings on THIS spec (esp. §7), section refs,
concrete failure scenarios, verdict: **ship / ship-with-changes / rethink.**
