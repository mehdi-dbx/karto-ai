# KARTO Atlas V3 — Implementation Instruction Set

**Audience:** a Claude Code session with full repository access.
**Prerequisite:** V2 instruction set (`karto-v2-implementation-instructions.md`) implemented or in progress. V3 builds strictly on top of V2's modules (A1–A5, B1–B7, C1–C3, D1–D8). Nothing in V3 rolls back V2 — where V3 touches a V2 artifact, it is stated explicitly.
**Your job:** read this document, audit the repo (including V2 state), produce a phased implementation plan, list divergences and open questions, WAIT for approval, then implement phase by phase.
**Method:** every module = WHY → WHAT → HOW → EXAMPLE → TEST. Running examples: BNP Paribas (FR bank), Crédit Agricole (silent giant), Accor (hospitality cameo), Mistral AI (vendor/private).

---

## 0. What V3 is (product framing — read before any code)

V2 made the census computable (universe, maturity, momentum, money, compare, API). V3 makes it **usable by real personas and alive**:

1. **Positioning:** KARTO is a **screener / idea generator**, not a decision terminal. It starts investigations; users verify. "Use at your own caution" stated once; provenance (tier + freshness) visible always. Never imply investment advice.
2. **Personas served (five):**
   - **Investor** — hunts non-consensus thesis seeds (hype vs substance, momentum breaks)
   - **Vendor / Builder** — sells or builds AI solutions FOR companies; hunts prospects and open territory (the "contractor", not the founder)
   - **Strategist** — corporate user; "how does MY company compare"
   - **Consultant** — advises clients; needs use cases, references, playbooks
   - **Machines** — notebooks/agents via the static API (V2-C3); silent fifth guest
3. **Persona mechanism — hard rule:** persona is NEVER a wall, an account, or a separate pipeline. One data spine; persona changes only (a) which questions are grouped under which header, (b) default sort/filter of destination views, (c) the `action` wording on insight cards (B7 `persona` field). All content reachable by everyone.
4. **Navigation engine — final decision (do not reopen):** navigation by **choosing questions, never by finding pages**. No NL ask bar (forces typing + LLM), no sentence builder, no visual tree/graph navigation (rejected — browser history already provides hop-back). Specification in Module N1.
5. **Architecture invariants (inherited from V2, still absolute):** `register.csv` = source of truth; everything traceable to sources + documented rules; static-first (GitHub Pages, build-time computation, client-side JS); LLMs offline as parsers only, results committed to CSVs; every view = a self-contained URL.

---

## PHASE N — Navigation engine (highest priority; pure front-end + one JSON)

### Module N1 — Question-based navigation

**WHY:** No persona should guess a click sequence. The site must take orders, not expose a map. A menu of questions written in the user's own words, each resolving in ONE click to a filtered, sorted answer page, is the simplest complete engine: zero typing, zero LLM, zero learning curve, works offline, cannot misunderstand. The browser itself (back/forward/tabs/bookmarks) supplies all "hop-back / hop-across" behavior for free because every state is a URL — do NOT build custom history, breadcrumb trees, or graph visualizations.

**WHAT:**
1. `data/questions.json` — the question registry. Each entry:
```json
{
  "id": "silent_giants",
  "text": "Which big companies have zero AI yet?",
  "personas": ["vendor", "consultant"],
  "target": "/companies?silent_only=true&sort=size_desc",
  "params_open": ["country", "vertical"],
  "teaser_metric": "count_l0",
  "followups": ["silent_vs_peers", "whitespace_my_market", "proven_in_vertical"]
}
```
   - `target` = a fully preset deep link (all filters/sort in params).
   - `params_open` = which chips the destination exposes for refinement.
   - `teaser_metric` = key into a cook-computed stats object, rendered as a live number next to the question (optional but cheap; see N3).
   - `followups` = ordered ids of next questions (see N2).
2. **Home = the question menu**, grouped by persona headers (self-identification by reading, no state, no login):
   - 💰 *I invest* → hype/momentum/blind-sector questions
   - 🔧 *I sell or build AI solutions* → silent giants / unquantified-active / open territory
   - 🏢 *I run strategy at a company* → compare / gaps vs proven
   - 📋 *I advise clients* → use cases / references / what's coming
   - Plus a small neutral group: *Just exploring* → today's signals, the atlas, what changed
3. **Canonical starting set (12 questions; owner may re-word, ids stable):**
   - investor: `all_talk_no_money` → `/signals?type=contradiction` · `quiet_accelerators` → `/signals?type=momentum_break` · `blind_sectors` → `/signals?type=blind_vertical`
   - vendor: `silent_giants` (above) · `unquantified_active` → `/companies?existence=confirmed&has_value_number=false&sort=prospect_score` · `open_territory` → `/atlas?highlight=whitespace`
   - strategist: `compare_rivals` → `/compare` (picker open, search-first) · `proven_we_lack` → `/usecases?gap_for=me` (prompts for company via picker)
   - consultant: `proven_in_sector` → `/usecases` · `references_like_client` → `/usecases?runners=filter` · `coming_next` → `/usecases?sort=diffusion`
   - exploring: `what_changed` → `/changelog`
4. **Refinement rule (mutate vs navigate):** on an answer page, filter chips MUTATE the current URL in place (replaceState) — no new history entry per chip. Clicking a question NAVIGATES (pushState/new page). This keeps browser history = question path, clean.

**HOW:**
1. Create `data/questions.json`; validate ids, targets resolve, followups reference existing ids (build-time check in cook or a lint script).
2. Home component renders groups from the registry (order: persona groups, then exploring). No hardcoded questions in JSX/HTML — registry-driven so the owner edits JSON, not code.
3. Ensure every `target` view exists and honors its params (most exist from V2: D2 compare, D4 silent list, D5 trends, B7 signals feed; `/usecases` arrives in Phase U — until then its questions render greyed "coming soon" or are omitted via a `enabled` flag).
4. Header on all pages: logo → home (the menu), nothing else mandatory. Optional slim links (Atlas, Changelog, API) — keep ≤4.

**EXAMPLE:** A Paris integrator lands, reads "🔧 I sell or build AI solutions", sees "Which big companies have zero AI yet? → **214**", clicks. Lands on `/companies?silent_only=true&sort=size_desc`. Adds chip country=FR (URL mutates, no new history entry). Crédit Agricole tops the list. Exports the brief. Total: 2 clicks + 1 chip. He never saw a sitemap.

**TEST:** Click-budget assertions on real data — vendor reaches an exportable named silent-giant list in ≤3 interactions from home; strategist reaches his-company-vs-3-rivals table in ≤2 (search-first); investor reaches a contradiction card with a company + pre-written question in ≤3. Back button after 3 questions returns through questions, not through chip states.

---

### Module N2 — Next-questions block (completes the engine)

**WHY:** The menu gets users IN; this keeps them moving without guessing. Every answer must end with offered next moves — the "waiter at every table". This is also where V2-B7's actionability rule ("no insight without an action") meets navigation: the next question IS often the action.

**WHAT:** Every answer view (signals, companies list, company page, country page, compare, use cases, changelog) renders at bottom a block: **"Next:"** + exactly 3 question links. Sources of the 3:
1. Static `followups` from the current question's registry entry (context-substituted: `{country}` etc. filled from current URL params).
2. If arrived without a question context (direct URL), fall back to the view's default followups (each view id has a default set in the registry).

**HOW:** Small resolver: current URL → matching question id (by target pattern) → followups → substitute params → render. Pure client-side, registry-driven.

**EXAMPLE:** On the France-filtered silent list, bottom shows: "Next: → What's proven in French banking? → Which of these have rivals deploying hard? → Who sells AI to French banks?" Each is one click, params pre-filled with FR.

**TEST:** No answer view renders without a Next block; all followup links resolve with the current context (FR carries through); dead-end audit script: crawl every question target, assert Next block present.

---

### Module N3 — Teaser stats (optional, cheap, high impact)

**WHY:** A question with a live number sells itself ("Which giants have zero AI? → **214**"). The data becomes its own ad; the menu stops feeling static.

**WHAT:** Cook emits `data/question_stats.json`: `{question_id: value}` for questions with `teaser_metric`. Home renders the number inline. Regenerated on every cook → numbers move daily (visible heartbeat on the front door).

**TEST:** Stats regenerate on cook; a register change that adds a silent company increments `count_l0` next build; missing stat renders question without number (never "NaN").

---

## PHASE U — Use-case spine (the consultant/strategist unlock)

### Module A7 — Use-case extraction & clustering

**WHY:** The use case is the atomic unit of "what should we do with AI" — and it is currently buried inside 2,606 free-text strings, organized by company/geo instead. The 6 horizontals are too coarse ("Core/Domain" spans trip planners, ADAS, and health insights — unusable as a pitch category). A named-pattern catalog inverts the register: not "what does BNP do?" but "who does claims automation, where, with what results?" It also unlocks the two highest-value strategic reads: **cross-vertical transfer** (proven in retail, absent in insurance → go first) and **diffusion tracking** (born US-tech 2022 → banks 2023 → your market: not yet — prediction with sources).

**WHAT:**
1. Offline pipeline (rerunnable, results committed):
   - Pass 1 — LLM tags each register row with a use-case pattern from a controlled, growable taxonomy (target ~60–120 patterns, e.g., `genai_travel_assistant`, `ai_claims_automation`, `hands_free_driving`, `internal_copilot`, `ai_voice_ordering`). Rows can carry 1–2 patterns.
   - Pass 2 — human/LLM review of the taxonomy itself (merge duplicates, name patterns in plain business language). Taxonomy lives in `data/usecase_taxonomy.csv`: `{pattern_id, name, description, horizontal, example_row_ids}`.
   - Output `data/usecases.csv`: `{row_id, pattern_id, confidence, source_phrase}`.
2. Cook aggregates → `atlas.json.usecases[]` per pattern: `{pattern_id, name, runners: n_companies, verticals[], countries[], first_seen, with_value_number, value_claims[] (from V2-A2, linked), maturity_mix, diffusion: [{cc_or_vertical, first_year}]}`.
3. Derived views in cook:
   - **Transfer map:** patterns proven (V2 verdict logic at pattern level) in vertical X, absent in vertical Y → `transfer_opportunities[]`.
   - **Diffusion timeline:** per pattern, ordered first_seen by country → arrival-lag estimates (label as estimates).

**HOW:** Reuse V2-A2's offline-LLM tooling. Batch, spot-check 50 rows (≥85% pattern precision before merge). Taxonomy is versioned; re-tagging on taxonomy change is a rerun, not a migration.

**EXAMPLE:** Rows "AI Trip Planner (GenAI, OpenAI-powered)" (Booking) and "'Romie' GenAI travel assistant" (Expedia) both tag `genai_travel_assistant`. Pattern card: 7 runners, 4 countries, first_seen 2023 (US), 2 value claims, absent in FR hospitality → transfer_opportunity for France, Accor top target by size.

**TEST:** Booking+Expedia converge on one pattern; every usecases.csv row carries source_phrase found in register text; no pattern with 1 runner survives review (merge or drop); transfer list recomputable from pattern×vertical presence.

### Module D9 — Use-case catalog UI

**WHY:** The spine needs a face; it is the consultant door's landing and the strategist's "what are we missing" answer.

**WHAT:** `/usecases` — catalog cards: pattern name, one-line description, runner count, verticals, value range (when claims exist), maturity mix, diffusion sparkline. Filters: vertical, country-absence ("not yet in..."), has_value_number. `/usecases/{pattern}` — detail: runners table (each = company + source + tier + freshness), value claims with source phrases, diffusion timeline, transfer suggestions, Next block (N2). Export briefing (V2-D7) wired.

**EXAMPLE:** Consultant clicks "What AI is proven in hospitality?" → catalog filtered vertical=Hospitality → `genai_travel_assistant` card (7 runners) → detail → runners filtered country=UK as references → Export → client brief with 7 sources in 4 clicks.

**TEST:** Every number on a pattern page click-traceable to rows/sources; the 4-click consultant flow passes on real data; catalog renders from atlas.json only.

---

## PHASE V — Vendor layer

### Module A6 — Vendor extraction

**WHY:** Vendors are the supply chain of the register and are already named inside `use_case` text ("OpenAI-powered", "partnership with Mistral") — invisible to computation. Extracting them unlocks: ecosystem intelligence ("Mistral powers N deployments"), competitive read for the vendor persona ("who already sells where I want to sell"), a build-vs-buy signal (in-house is a value, not a null), refinement of prospect_score (V2-B5 reserved "no vendor named" as an input), and the natural bridge to the private block (Phase P) — vendors ARE the startups.

**WHAT:** Offline pass → `data/vendors.csv`: `{row_id, vendor, vendor_type: model|cloud|platform|integrator|inhouse, source_phrase}`. Curated dictionary (~200 names: model providers, hyperscalers, data/AI platforms, major integrators) + LLM pass for misses. Cook emits: `atlas.json.vendors[]` (per vendor: deployments, verticals, countries, customer list), per-company `stack[]`, per-cell `vendors_named[]` or explicit `"none_named"`.

**HONEST LIMIT (encode in UI copy):** disclosure bias — companies name vendors selectively; "not disclosed" is a frequent, legitimate value. Never infer a vendor.

**EXAMPLE:** Booking row → `{OpenAI, model}`. Expedia "OpenAI + in-house models" → two rows, one `{inhouse}`. Ford "Latitude AI subsidiary" → `{Latitude AI, inhouse}`. Vendor page `/vendor/mistral-ai`: customers, verticals, countries — nobody else has this source-linked.

**TEST:** The three examples extract exactly as above; every row has source_phrase; build-vs-buy ratio computable per vertical; B5 prospect_score consumes vendor-absence without code change.

### Module D10 — Vendor surfaces

**WHAT:** vendor field on deployment rows (side panel, company page); `/vendor/{slug}` page (customers table, verticals, countries, Next block); "no vendor named" filter chip on `/companies` and grid cells; vendor question added to registry: "Who sells AI to [vertical]?" → `/usecases?vendor_view=1&vertical=…` or `/vendor` index.

**TEST:** Mistral page lists its register customers with sources; the vendor question resolves in one click.

---

## PHASE H — Heartbeat (daily updates, agents, changelog)

### Module H1 — Agent update pipeline

**WHY:** A census is a snapshot; a screener people return to needs a pulse. The moat ranking is: **register + heartbeat > rules > insights > UI**. A vacuumed copy of the data is stale in one cycle if the source lives. Solo-operator economics only work with agents doing collection/verification and the human arbitrating.

**WHAT:** Scripted agent workflows (Claude-agent or equivalent), each producing **proposed CSV diffs into a staging area — never writing directly to `data/`**:
1. **Discovery agent** (daily/weekly): monitors press releases, filings feeds, earnings-call mentions for universe companies → proposed new register rows (with tier, source_url, date).
2. **Verification agent:** re-checks rows whose `last_verified` (V2-A5) exceeds threshold → proposes `last_verified` bumps, corrections, or `SMOKE` demotions.
3. **Claims/commitments agent:** runs V2-A2/A3 extraction on new rows.
4. **Review gate (the dude):** a `staging/pending_*.csv` + a review script that shows diffs and applies approved ones. High-stakes changes (SMOKE demotions, value numbers) always human-approved; low-stakes (last_verified bump with unchanged source) may auto-apply after a confidence rule, config-flagged.
5. **Post-merge:** cook runs, site rebuilds, per-entity API regenerates, changelog entry emitted (H2).

**HOW:** Design the staging format + review CLI first; agents are prompts + fetch scripts around it. Start with ONE vertical (Financial Services) at daily cadence as the pilot before widening — same pilot-first pattern as V2-A3.

**EXAMPLE:** Discovery agent finds SocGen press release "deploys GenAI assistant for advisors" → staged row {SocGen, FR, FinServ, Core/Domain, tier P, url, 2026-07}. Review CLI shows it; owner approves; next build: SocGen momentum flips, changelog says so, `quiet_accelerators` question's teaser increments.

**TEST:** No agent writes to `data/` directly (enforce via path checks); every applied diff traceable to an approval record; pilot vertical shows ≥1 successful full loop (discover → approve → cook → changelog).

### Module H2 — Changelog page & "since last visit"

**WHY:** The heartbeat must be visible — it is the return-visit driver for every persona and the proof the dataset is alive.

**WHAT:**
1. Cook diffs current vs previous `atlas.json` (keep last N versions or a compact state file) → `data/changelog.json`: dated entries typed as `new_deployment | level_change | first_value_number | gone_quiet | new_silent | verdict_change`, each with entity links + sources.
2. `/changelog` — dated list, filter by type/country/vertical, Next block included. This is the `what_changed` question's target.
3. **Since-last-visit strip (client-side only):** store last-visit timestamp in localStorage; on home, render "Since your visit: 3 changes in your areas" linking into changelog filtered. No accounts, no server state.

**EXAMPLE:** "2026-07-24 — SocGen: first Core/Domain deployment (source) · Energy vertical: first value number ever (source) · 2 new silent giants entered universe." Investor reads it as signal; vendor as bid windows.

**TEST:** Every changelog entry links entity + source; diff is deterministic (same two versions → same entries); localStorage strip appears only on revisit and never blocks first paint.

---

## PHASE P — Private & startup block (own room, not a mixin)

### Module P1 — Private universe & register

**WHY:** The disruption half of every strategic question lives in private companies — and for the vendor persona, private AI companies are the competition map. But listed-company denominators, absence-signals, and tier definitions do NOT transfer: silence means nothing for a startup, and there are no filings. Therefore: **own block** — separate bounded universe, separate register, adapted evidence ladder, its own denominators. Never pooled into listed percentiles.

**WHAT:**
1. `data/universe_private.csv` — a NAMED closed set, boundary stated openly (owner picks: e.g., "global unicorn list" or "top-500 funded AI companies" or per-country scale-up indexes): `{company, country, category, last_round, total_raised_usd, employees_est, founded, source_url}`.
2. `data/register_private.csv` — same 11-column shape as the main register, plus `evidence_kind`.
3. **Adapted tier ladder (document in methodology):** P-equivalent = the company's own disclosures AND funding events (a round IS money-committed disclosure: PitchBook/Crunchbase/press-release-of-round); I = third-party press; S = smoke. **No L0/absence signal in this block** — silence ≠ inactivity for private cos; the concept is explicitly not computed.
4. Cook → `atlas.json.private{}` — separate keys, separate rollups; NEVER merged into `companies[]`, `benchmarks`, or country percentiles.
5. **The bridge (highest-value join):** private companies matched against the vendor layer (A6) — `private.as_vendors[]`: which private cos appear as suppliers to the listed universe. This is where the two worlds legitimately meet.

**EXAMPLE:** Mistral AI: in `universe_private` (FR, foundation models, Series B, $X raised) AND in vendors.csv as supplier on BNP + others → its page shows both faces: funding trajectory (private register) and customer footprint (vendor layer). A vendor-persona user sizing the French market sees his private competitors and their listed customers on one screen.

**TEST:** Zero private rows leak into listed percentiles/denominators (assert in cook); boundary of the set stated on every private view; Mistral's two-face page renders from the join; funding-event rows carry source_url 100%.

### Module D11 — Private block UI

**WHAT:** `/private` index (the set, filterable, boundary statement on top); `/private/{slug}` pages; "Private/Startups" section on relevant vertical/country pages clearly visually separated (own background/label — a different room in the house); vendor pages show private-status badge when applicable; new questions in the registry: "Which startups sell AI to [vertical]?" / "Who are the funded AI companies in [country]?"

**TEST:** Visual separation audit (no private card renders inside a listed ranking); the two new questions resolve in one click; disclaimer/boundary present on all private views.

---

## PHASE R — Persona finishing (action templates & signals feed types)

### Module B7-r — Action templates per persona (revision of V2-B7)

**WHY:** V2 shipped the insight engine with a `persona` field; V3's persona set fixes its vocabulary. Same card, different verb: consultant wants "outreach opener", investor wants "verify then position", vendor wants "bid window", strategist wants "board answer". The QA bar also splits: consultant-grade = "pasteable into a client email"; investor-grade = "worth an hour of DD" (NOT "worth wiring money" — screener positioning).

**WHAT:** For each B7 rule type × persona, one action template string (JSON, next to the rule definitions):
- `silent_giant` → vendor: "Outreach: their {n} closest rivals disclose {m} deployments — sources attached." / consultant: same, phrased as client-gap brief / investor: "Laggard flag — check capex language next filing."
- `contradiction` → investor: "Earnings-call question: '{generated_q}'" / strategist: "Credibility benchmark vs your own claims."
- `momentum_break` → vendor: "Budget likely unlocked at {company} — bid window." / investor: "Trajectory change — verify catalyst."
- `whitespace` → vendor/consultant: "Greenfield: {k} foreign proof-cases as references (attached)."
- `blind_vertical` (new rule: vertical with deployments>threshold and zero value numbers) → investor: "Sector deploys blind — measurement/tooling thesis." / vendor: "Whole-vertical services opportunity."

**TEST:** Every rule×relevant-persona pair has a template; cards on `/signals?p=X` render X's wording; no card ships with an empty action (V2 invariant re-asserted).

---

## Build order & dependencies

```
Phase N: N1 → N2 → N3            (navigation engine first — everything lands in it;
                                   /usecases questions flagged disabled until U)
Phase U: A7 → D9                  (use-case spine; unlocks consultant/strategist questions)
Phase V: A6 → D10                 (vendor layer; feeds B5, P1 bridge)
Phase H: H1 (pilot vertical) → H2 (heartbeat + changelog; H2 can ship on manual
                                   updates before H1 automates them)
Phase R: B7-r                     (small; can run parallel to H)
Phase P: P1 → D11                 (private block last — depends on A6 bridge and a
                                   stable heartbeat to keep two registers alive)
```
Each phase ends shippable. N alone already transforms the product.

## Out of scope for V3 (decided, do not build)

- NL ask bar / LLM-at-runtime navigation (may return as an optional accelerator in a later version, on top of the same question targets — nothing in N1 blocks it)
- Visual tree/graph navigation, custom history, breadcrumb trees — browser history is the mechanism
- Accounts, watchlists, alerts, server-side anything
- Real-time / news-speed freshness (screener cadence = daily builds, not minutes)
- Pooling private and listed populations in any shared metric

## Your first deliverable (before any code)

1. **Repo + V2 audit:** confirm V2 module states; map every V3 module to concrete files/functions in THIS codebase; list divergences from this doc's assumptions.
2. **Phased plan** with effort estimates and the TEST criteria above translated into runnable checks (including the click-budget assertions of N1 and the leak-assertions of P1).
3. **Open questions for the owner**, at minimum: final wording of the 12 questions; taxonomy seed for A7 (propose 40 patterns from the real register for review); vendor dictionary seed for A6; the named boundary set for P1; agent cadence + auto-apply confidence rule for H1; whether N3 teaser stats ship in v3.0 or v3.1.

Then wait for approval before implementing.
