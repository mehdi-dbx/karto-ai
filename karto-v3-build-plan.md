# KARTO V3 — Build Plan (Plumbing-First Edition)

**Audience:** Claude Code session with full repo access, V2 shipped (all 21 modules, see `karto-v2-BUILD-DECISIONS.md`).
**Companion doc:** `karto-v3-implementation-instructions.md` — contains the full module specs (WHY/WHAT/HOW/EXAMPLE/TEST). THIS document overrides its build order and adds the plumbing-first rules. Where the two conflict, this one wins.
**Owner's passes (QA of V2 views, decisions) are DONE — do not wait on them.**

---

## The strategy (owner's decision — governs everything)

**Build ALL the plumbing and design first, with empty columns where data is missing. Run the data resweep ONCE, at the very end.**

Consequences you must honor in every step:

1. **Null-tolerant by design.** Every feature that depends on not-yet-collected data (company size, commitments) must be fully wired: schema in place, cook computes what it can, UI renders with a fallback.
2. **Fallbacks visible, never hidden, never faked.** A view missing data shows its fallback PLUS a small "data pending" marker (e.g., a subtle badge/tooltip: "size data pending — sorted by peer gap"). No fabricated values, no silently dropped features. The owner must be able to QA the hollow site and see exactly what the final resweep will light up.
3. **The resweep is the finale.** One consolidated agent-driven data run at the end (Step 12), flowing through the review gate built in Step 6. After it: columns fill, sorts flip, cards populate — with ZERO code changes. If a code change is needed post-resweep, the plumbing was wrong.

---

## Step 1 — Vertical dedup

**Why:** `verticals` has near-duplicates (e.g., "Media" vs "Media / Entertainment / Gaming"; "General Manufacturing" vs "Manufacturing & Robotics" — full list in `CLASSIFICATION.md`). Step 8 (use-case taxonomy) clusters on top of verticals; building it on duplicates bakes the mess into the new spine permanently. Dedup is cheap now, expensive later.

**Do:**
1. Produce a canonical vertical list + alias map (`data/vertical_aliases.csv`: `{raw, canonical}`).
2. Apply at cook time (register stays untouched — raw labels preserved in `raw_sector`/original column; canonical used in all aggregates).
3. Recook; verify grid, histograms, country pages, API fragments all show the canonical set only.

**Test:** count of distinct verticals in `atlas.json` equals the canonical list; no aggregate references a raw duplicate; register file diff = zero.

---

## Step 2 — Unify money signals into one table

**Why:** Money signals are currently split: `claims.csv` (776 extracted claims, incl. investment-type) + an empty `commitments.csv` stub. Two files, one concept. Different grain than the register (one row per MONEY EVENT, not per deployment) justifies a separate table — but ONE table, not two.

**Do:**
1. Create `data/money.csv`: `{id, company, cc, amount, currency, unit, kind: savings_claim|revenue_claim|investment|acquisition|partnership|users_claim|vague, origin: register_extraction|dedicated_collection, horizon: one_off|multi_year|null, tier, source_url, source_phrase, register_row_id (nullable), date}`.
2. Migrate all `claims.csv` rows into it (`origin: register_extraction`); retire `claims.csv` (keep a deprecation note one release).
3. Delete the `commitments.csv` stub; dedicated collection (Step 12) will write into `money.csv` with `origin: dedicated_collection`.
4. Update cook + hype detector + company pages to read `money.csv` only. Investment-side aggregates will be near-empty for now — render per the fallback rule ("commitment data pending").

**Test:** hype detector renders identically to pre-migration for the claims side; zero data loss (row counts match); investment-side views show the pending marker, not empty-state confusion.

---

## Step 3 — Question-based navigation (core engine)

*(Full spec: companion doc, Module N1. Adapt everything to the shipped HASH ROUTING: targets like `#/companies?silent_only=true`.)*

**Why:** No persona should guess a click sequence. Navigation = choosing questions written in the user's words; one click = the answer page, pre-filtered, pre-sorted. No NL bar, no LLM, no tree — the browser (back/forward/tabs/URLs) is the history mechanism.

**Do:**
1. `data/questions.json` registry: id, text, personas[], target (hash URL with all params), params_open[], teaser_metric (nullable), followups[] (question ids), enabled flag.
2. Home becomes the question menu, grouped by persona headers:
   - 💰 *I invest* — "Who's all talk, no money?" → `#/signals?type=contradiction` · "Who's quietly accelerating?" → `#/signals?type=momentum_break` · "Which sector deploys blind?" → `#/signals?type=blind_vertical`
   - 🔧 *I sell or build AI solutions* — "Which big companies have zero AI yet?" → `#/silent?sort=size_desc` (FALLBACK until Step 12: sorts by peer-gap, marker shown) · "Who runs AI but can't measure it?" → `#/companies?existence=confirmed&has_value_number=false&sort=prospect_score` · "Where's open territory?" → `#/atlas?highlight=whitespace`
   - 🏢 *I run strategy at a company* — "How do we compare to rivals?" → `#/compare` (picker open, search-first) · "What's proven in our industry that we lack?" → `#/usecases?gap=1` (disabled until Step 8)
   - 📋 *I advise clients* — "What AI works in a sector, with references?" → `#/usecases` (disabled until Step 8) · "What's coming to my client's market next?" → `#/usecases?sort=diffusion` (disabled until Step 8)
   - 🧭 *Just exploring* — "What changed recently?" → `#/changelog` (disabled until Step 10) · "Show me the atlas" → `#/` map
3. Refinement rule: on answer pages, filter chips MUTATE the current URL (replaceState, no history entry); clicking a question NAVIGATES (new history entry). History = the question path.
4. Owner may re-word question text; ids are stable. Disabled questions render greyed with "coming soon" or are hidden — owner's choice, ask in your plan.

**Test:** vendor reaches an exportable silent-giant list in ≤3 interactions from home; strategist reaches his-company-vs-rivals table in ≤2; back button after 3 questions steps through questions, not chip states; every enabled target resolves HTTP-valid on Pages.

---

## Step 4 — Next-questions block on every answer page

*(Spec: Module N2.)*

**Why:** The menu gets users in; this keeps them moving without guessing. Every answer ends with offered next moves — often the insight's ACTION expressed as navigation.

**Do:**
1. Every answer view (signals, silent, companies, company page, country, compare, hype, trends, later usecases/changelog/vendor/private) ends with a "Next:" block of exactly 3 question links.
2. Resolution: current URL → matching question id → its `followups`, with context substitution (country/vertical params carry through). Direct-URL arrivals (no question context) use per-view default followups defined in the registry.

**Test:** crawl every enabled question target — assert Next block present with 3 resolvable links; FR filter on silent list carries into its followups' targets.

---

## Step 5 — Teaser stats on the question menu

*(Spec: Module N3.)*

**Why:** "Which giants have zero AI? → **491**" — the live number sells the click and makes the daily heartbeat visible on the front door.

**Do:** cook emits `data/question_stats.json` `{question_id: value}` for questions with `teaser_metric`; home renders numbers inline; missing stat → question renders without number (never NaN/0-as-lie). Size-dependent teasers show count (available) not size-sums (pending).

**Test:** stats regenerate on cook; a register change moves the number next build.

---

## Step 6 — Staging & review gate (heartbeat foundation)

*(Spec: Module H1, gate part only — agents come in Steps 10 & 12.)*

**Why:** From here on, ALL data changes (including the final resweep) flow through one mechanism: scripts/agents PROPOSE diffs into staging; the owner APPROVES; only approved diffs touch `data/`. Building the gate before the biggest-ever data drop (Step 12) is the point.

**Do:**
1. `staging/` area: proposed CSV diffs as `pending_{table}_{date}.csv` + a manifest (source of proposal, confidence, per-row source_url).
2. Review CLI: show diffs (adds/changes/demotions) vs current data, approve/reject per row or per batch, apply approved to `data/`, log every application to `data/audit_log.csv`.
3. Path guard: build fails if anything outside the gate wrote to `data/` (checksum or git-diff check in the build script).
4. Config: auto-apply rule for low-stakes changes (e.g., `last_verified` bump with unchanged source) — OFF by default; owner flips when trusted.

**Test:** a synthetic staged diff round-trips (propose → approve → applied → audit-logged); an unapproved direct write to `data/` fails the build.

---

## Step 7 — Use-case extraction & taxonomy

*(Spec: Module A7. Runs on EXISTING register text — no resweep needed.)*

**Why:** The use case is the atomic unit of "what should we do with AI", currently buried in 2,606 free-text strings. Six horizontals are too coarse ("Core/Domain" spans trip planners, ADAS, health insights). A named-pattern catalog inverts the register: "who does claims automation, where, with what results" — and unlocks cross-vertical transfer + diffusion timelines.

**Do:**
1. Propose a seed taxonomy (~40–80 patterns) FROM the real register text; submit to owner for review before tagging (this is one of your plan's open questions).
2. Offline tagging pass (LLM allowed offline, results committed): `data/usecases.csv` `{row_id, pattern_id, confidence, source_phrase}`; taxonomy in `data/usecase_taxonomy.csv`.
3. Cook: `usecases[]` aggregates (runners, verticals, countries, first_seen, value links from money.csv, maturity mix) + `transfer_opportunities[]` (proven in vertical X, absent in Y) + diffusion orderings (per pattern, first_seen by country — labeled estimates).
4. Spot-check 50 tagged rows; ≥85% precision before merge (through the Step 6 gate).

**Test:** Booking "AI Trip Planner" and Expedia "Romie" converge on one pattern; every usecases.csv row's source_phrase found verbatim in register text; no single-runner pattern survives review.

---

## Step 8 — Use-case catalog UI

*(Spec: Module D9.)*

**Do:** `#/usecases` catalog (cards: name, runner count, verticals, value range when present, diffusion sparkline; filters: vertical, "not yet in {country}", has_value_number) + `#/usecase/{pattern}` detail (runners table with source+tier+freshness, money rows, diffusion timeline, transfer suggestions, Next block, export). **Then flip the Step 3 disabled questions to enabled.**

**Test:** consultant flow — home → "What AI works in hospitality?" → pattern → UK runners as references → export — in ≤4 clicks on real data; every number traceable.

---

## Step 9 — Vendor layer

*(Spec: Modules A6 + D10. Runs on EXISTING text — no resweep needed.)*

**Why:** Vendors are named inside `use_case` strings ("OpenAI-powered", "partnership with Mistral") and currently invisible. Unlocks ecosystem intel, the build-vs-buy signal, sharper prospect_score (vendor-absence term), and the bridge for the future private block.

**Do:**
1. Curated vendor dictionary (~200 names; propose seed in your plan) + offline pass → `data/vendors.csv` `{row_id, vendor, vendor_type: model|cloud|platform|integrator|inhouse, source_phrase}`. **`inhouse` is a value** (build-vs-buy), "not disclosed" is a legitimate frequent outcome — never infer.
2. Cook: `vendors[]` (per vendor: deployments, verticals, countries, customers), per-company `stack[]`, per-cell `vendors_named[]/none_named`; feed vendor-absence into prospect_score.
3. UI: vendor chips on deployment rows; `#/vendor/{slug}` pages (customers, verticals, Next block); "no vendor named" filter; add registry question "Who sells AI to {vertical}?" → vendor index.

**Test:** Booking→{OpenAI, model}; Expedia→ two rows incl. {inhouse}; Ford "Latitude AI subsidiary"→{Latitude AI, inhouse}; Mistral page lists its register customers with sources.

---

## Step 10 — Changelog & since-last-visit

*(Spec: Module H2.)*

**Why:** The heartbeat must be visible — return-visit driver for every persona and the proof the dataset is alive.

**Do:**
1. Cook diffs current vs previous atlas state (keep a compact prior-state file) → `data/changelog.json`: typed entries (`new_deployment | maturity_change | first_value_number | gone_quiet | new_silent | verdict_change`) with entity links + sources.
2. `#/changelog` view (dated, filterable by type/country/vertical, Next block). Enable the "What changed recently?" question.
3. Client-side "since your last visit" strip on home via localStorage timestamp — links into filtered changelog. No accounts, no server.

**Test:** deterministic diff (same two states → same entries); every entry links entity + source; strip appears only on revisit; first paint unaffected.

---

## Step 11 — Persona action templates on insight cards

*(Spec: Module B7-r.)*

**Why:** Same finding, different verb per persona: vendor = "bid window", investor = "verify then position", strategist = "board answer", consultant = "client brief". Screener positioning caps the investor bar at "worth an hour of DD", never "wire money".

**Do:**
1. Template table (JSON beside the insight rules): rule_type × persona → action string with slots (`{company}`, `{n}`, `{peer_median}`...). Cover existing rule types + add `blind_vertical` rule (vertical with deployments ≥ threshold and zero value numbers).
2. `#/signals?p={persona}` renders that persona's wording; persona chips on the feed re-rank + re-word, never hide.
3. Money-dependent templates (contradiction cards' commitment side) render with the pending marker until Step 12.

**Test:** every rule×relevant-persona pair has a template; no card renders with an empty action; the same card shows different action text under different `p=` params.

---

## Step 12 — THE RESWEEP (the finale — everything lights up)

**Why:** All plumbing above is wired and QA'd hollow. One consolidated data run now fills it — through the Step 6 gate — and the design completes with zero code changes.

**Do (one orchestrated run, three workloads):**
1. **Size enrichment** — mktcap / revenue / employees / ticker for ~2,468 universe companies from public sources (agent run, ~2–3h, like the country sweeps). → unlocks: B1 normalized metrics (per-$B, per-10k-emp), B5 prospect_score size term, silent-list true size sort, size-aware teaser stats, "big companies" question's real meaning.
2. **Financial-Services commitments pilot** — dedicated collection of money-committed events (invest/acquire/partner) for the FS vertical → `money.csv` with `origin: dedicated_collection`. → unlocks: hype detector's money-in axis, investor contradiction cards at full strength.
3. **Freshness pass** — `last_verified` bumps / corrections / SMOKE demotions where sources changed (verification agent).
All three: agents PROPOSE into staging → owner reviews via the Step 6 CLI → apply → cook → rebuild → changelog auto-records the drop.

**Post-resweep assertions (the plumbing proof):**
- Silent list flips to size sort; pending markers disappear on their own (marker logic keys off data presence, not flags).
- Hype detector shows both axes for FS; contradiction cards populate.
- ZERO code commits required between "resweep applied" and "features live". If one is needed, file it as a plumbing bug, fix, and note it in BUILD-DECISIONS.

---

## Explicitly OUT of scope (decided — do not build)

- NL ask bar / any runtime LLM; sentence builders; visual tree/graph navigation; custom history mechanisms (browser history is the mechanism)
- Accounts, watchlists, alerts, any server-side state
- Private/startup block (separate universe/register — next version, after this plan completes; its bridge point, the vendor layer, ships in Step 9)
- Real-time freshness (cadence = builds, not minutes)

## Standing rules for every step

- Register = source of truth; every number traceable to a source or a documented rule; static-first; LLMs offline-only as parsers with committed outputs.
- All data mutations from Step 6 onward go through the gate. No exceptions, including your own scripts.
- Each step ends: committed, pushed, Pages-verified, decisions appended to `karto-v3-BUILD-DECISIONS.md`.
- Doc examples are illustrative — verify against real data (as you correctly did in V2).

## Your first deliverable (before any code)

1. Repo audit vs this plan: map each step to concrete files/functions; flag divergences (esp. hash-routing translations of all question targets, current state of claims.csv/verticals).
2. Per-step effort estimates + the tests above as runnable checks.
3. Open questions for the owner, at minimum: disabled-questions rendering (greyed vs hidden); final wording of the 12 questions; taxonomy seed (propose ~40 patterns from real register text); vendor dictionary seed; auto-apply rule default for the gate; resweep source list for size data.

Then WAIT for plan approval. Build strictly in step order — each step shippable before the next begins.
