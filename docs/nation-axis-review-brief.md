# KARTO — Nation-State AI Axis: design brief for adversarial review

**You are an adversarial reviewer.** Your job is not to praise this design or refine
its wording — it is to find where it breaks, where it will fabricate, where it is
naïve about sourcing, where the "insight" is actually unfalsifiable opinion, and where
the whole premise is wrong. Assume the author is overconfident and trigger-happy (they
are). Be specific and cite the section. A finding that kills a column is worth more than
ten style notes. At the end, give a verdict: **ship / ship-with-changes / rethink.**

---

## 1. What KARTO is (context you need)

KARTO is an evidence-gated atlas of the global AI landscape, a static site. It already
has two "actor" axes:
- **Demand side** — the ~2,187 largest listed companies, each AI deployment gated to a
  real source URL. Discipline: additive, immutable keys, no LLM at build time, a claim
  with no real source is *dropped, not invented*. Absence is signal.
- **Supply side** (in progress) — AI *startups* as builders, same evidence bar.

The spine across both: **evidence-first, bounded, absence-is-signal, never fabricate —
a real source or drop the row.** This took days to earn on the demand side. Any new axis
must not poison it.

## 2. The new axis and its persona

A **third actor: the nation-state itself** — what each government *does* on AI.

The design is driven by ONE persona, and the whole value stands or falls on serving it:

> **A nation-state AI policy counselor / state-agency contractor.** They advise or sell
> into a government's AI build-out. Their goal is to understand **where a country sits on
> the geopolitical AI chessboard** in order to **uncover profit opportunities to
> accompany that country** — funded projects, implementing agencies, capability gaps they
> can fill.

The governing insight the design bets on:

> **gap = opportunity.** The profit is NOT with the leaders (US, China — self-sufficient,
> nothing to sell them). It is with the **funded-but-lacking** mid-tier (Gulf, India,
> Indonesia, Poland, Vietnam): rich ambition, thin capability, open procurement. The
> opportunity map is the *inverse* of the capability map.

## 3. Current state of the data (be skeptical of what exists vs what's claimed)

- **89 countries** already have a discovered **official source URL** for their national
  AI strategy (`docs/nation-sources.csv`). This is a *source-discovery pass only* —
  **nothing behind the links has been read, parsed, or verified.** ~99% are the
  government's own domain; a handful are OECD/AI-Watch-hosted or official translations;
  5 are "in development"; 1 (Switzerland) is a deliberate no-strategy (absence-as-signal).
- No facts, funding, compute, or posture have been extracted yet. That is the pass being
  designed here.

## 4. The proposed harvest — three streams

Per country, three sourcing streams feed one synthesis:

1. **PDF stream** — download the strategy doc, `pdftotext` (text-layer only; scanned/image
   PDFs are **flagged as extraction-failed, NOT OCR'd** — no native fallback, by choice).
   Yields: strategy content, apparatus, priority sectors, ethics-as-written.
2. **News stream** (Serper search) — real/appropriated funding, frontier-control actions,
   national champion, military use. (Rationale: many funding headlines and all "events"
   live in press, not in the strategy PDF.)
3. **Infra stream** (Serper, dedicated — NEW) — datacenter capacity (MW estimate),
   AI-capable vs legacy, sovereign vs hyperscaler, chip-access/export-control tier,
   Nvidia sovereign-AI deals, power posture. **This is not in any strategy PDF** — it
   comes from datacenter trackers, vendor announcements, export-control filings, energy
   data.

**Extraction engine:** Gemini 2.5 Flash (free tier; ~$0 for all 89), text + fixed schema
→ JSON. Runs outside the orchestrator's context. Claude audits a 5-country *sample* only,
never in the per-country loop. **Tiered depth:** important countries get deeper infra
sourcing; coverage is universal (even small states get "has domestic DC Y/N") — no country
gets a null physical layer just for being small (Morocco and Cameroon have datacenters).

## 5. The proposed record schema

**Comparable axes (structured, so they sort / filter / chart):**
- `funding` — 3-way: announced / appropriated / open-now + headline figure & currency
- `apparatus` — named AI office/authority + the *implementing* ministry (the buyer;
  distinguish spending entity vs coordinating shell)
- `compute` — domestic DC MW (est.) · AI-capable? · sovereign vs hyperscaler · chip/export
  tier · power posture
- `stack_position` — downstream consumer vs upstream chokepoint node (TSMC/ASML/memory/
  materials/design) + national champion preference
- `military_ai` — active / stated / absent / prohibited
- `ethics_stance` — permissive / balanced / precautionary / state-control
- `frontier_control_exposure` — imposes / subject-to / neutral (the export-control bucket)
- `sectors[]`, `region`, `has_strategy`

**Freeform:** `general_idea` — prose synthesis carrying the nuance the enums flatten.

**The payload:** `opportunity_read` — a **generated, explicitly-labelled inference**:
where this country's gap = a contract. The Atlas is action-oriented, not a cold database,
so this field is the point — but it is labelled inference, sitting visibly on the sourced
facts, never mixed into them.

**Provenance:** `sources[]` — every record traces to its URLs.

## 6. Non-negotiable disciplines (inherited from KARTO)

- No fabrication. Every claim → a source URL, or the field is null/flagged.
- Facts vs inference stay visibly separated. `opportunity_read` and derived enums
  (`posture`-like judgments) are labelled as the model's read, never presented as the
  country's own claim or as measured fact.
- "Synthetic / general idea" ≠ "loose." Compact, but every claim still traceable. A
  *wrong* general idea misinforms the exact decision-maker who matters — worse than none.
- LLM never runs at site build-time; this harvest is an offline data pass.

## 7. What a finished record should let the persona do

- Sort/filter to "funded + thin-domestic-compute + open procurement" → a target list.
- Read one country's `general_idea` + `opportunity_read` and know where the door is.
- Compare countries on the same axes (a posture × sovereignty matrix, a compute-gap map).
- Trust it: check any claim against `sources[]`.

---

## 8. Attack surface — where the author most wants you to dig

Do not limit yourself to these, but do not skip them:

1. **The `opportunity_read` field.** Is this defensible intelligence or laundered opinion?
   How would you falsify a bad one? Does labelling it "inference" actually protect the
   user, or is it a fig leaf on ungrounded speculation a contractor might bet money on?
2. **The infra stream.** Is per-country datacenter-MW, chip-tier, and power posture
   *actually sourceable* at 89-country scale, or is the author about to fabricate plausible
   numbers because "medium-hard" really means "not reliably available"? Where will it
   silently guess?
3. **The `funding` 3-way split** (announced/appropriated/open-now). Is this distinction
   reliably extractable, or will the model routinely misclassify a press-release headline
   as "appropriated"? What's the failure rate you'd expect?
4. **pdftotext-only, flag-failures.** How many of 89 government PDFs are image scans →
   silently null? Is flagging-and-dropping honest, or does it bias the dataset toward
   countries with modern web infrastructure (rich-country bias)?
5. **The enum flattening.** Do 4-value enums (`sovereignty: hedging`) destroy the exact
   nuance that makes the axis valuable, leaving comparables that look rigorous but aren't?
6. **The premise itself.** Is "gap = opportunity, inverse of capability map" actually true,
   or a seductive oversimplification? Counter-examples? Does the whole persona-driven framing
   push the atlas from *evidence* toward *sales-brochure*?
7. **Staleness.** Funding cycles, RFPs, export-control tiers, Nvidia deals change monthly.
   A static atlas of a fast-moving board — when is this dataset wrong-and-confident?
8. **Ethics/scope.** Is building a "where to sell into state AI / military AI programs"
   targeting tool something that should carry any guardrail, or is public-policy synthesis
   entirely benign? Flag if you think the framing invites misuse.

**Deliverable:** ranked findings (most-fatal first), each with section ref + concrete
failure scenario, then a one-word verdict: **ship / ship-with-changes / rethink.**
