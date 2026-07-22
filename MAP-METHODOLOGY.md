# AI Profitability Map — Master Context & Methodology

> **Read this first.** Single self-contained file to resume the project cold, in any
> session. Covers: (A) what the project is, (B) the environment fixes you need before
> doing anything, (C) where output goes, (D) the methodology, (E) the 2026 denominator,
> (F) status.
>
> Last updated: 2026-07-20.

---

## A. What this project is

A serious, evidence-graded **map of where AI is actually profitable**, organized by
industry vertical. Not a listicle, not a hype survey — a scored map with a citation
trail, honest evidence grades, and visible negative space.

- **User:** senior AI Engineer. Wants proof and backed sources — a *world/domain map*,
  not examples. Multi-session effort. Explicit: *"I refuse a sea of crap and
  contamination / noise. This is a serious study."*
- **Purpose:** understanding first, decision second. Being honest about what is NOT
  known is a feature.
- **Three profit lenses per cell** (kept separate — divergence is the deliverable):
  1. **Buyer ROI** — net-positive on a deploying enterprise's P&L?
  2. **AI-native P&L** — do AI-native products have *defensible* unit economics (not just revenue)?
  3. **Labor value** — measured task/worker output gain, even if not booked as profit?
- **Out of scope:** vendor/infra "picks & shovels" (chips, cloud, model margins).

---

## B. ENVIRONMENT FIX — do this before any research

### B.1 Native WebSearch is BROKEN (proven; cannot be fixed client-side)

- **Symptom:** `WebSearch` → `400 {"message":"The provided request is not valid"}` on
  *every* call, including trivial queries.
- **Root cause (proven by direct probe, not guessed):** this session runs through a
  **Databricks AI Gateway → Anthropic-on-Bedrock**. Env:
  `ANTHROPIC_BASE_URL=https://dbc-a5d4177a-49dc.cloud.databricks.com/ai-gateway/anthropic`,
  `CLAUDE_CODE_USE_GATEWAY=1`. Responses carry `msg_bdrk_` ids (= Bedrock). Anthropic's
  first-party `web_search_20250305` **server tool does not exist on Bedrock**, so the
  gateway 400s any request carrying it. Verified: identical POST returns **200 without**
  the tool, **400 with** it.
- **Not** a permissions issue (`WebSearch(*)` already allowed in settings.json). **Cannot**
  be fixed from the client — needs an admin gateway route or a direct `ANTHROPIC_API_KEY`
  (none set). Artifact to file with the platform team: *"plain messages 200, web_search
  tool 400 BAD_REQUEST, backend is Bedrock (`msg_bdrk_`), Bedrock lacks
  `web_search_20250305`."*

### B.2 The working search replacement — USE THIS INSTEAD

```bash
python3 ~/.claude/tools/websearch.py "query terms"        # 10 results (title/url/snippet)
python3 ~/.claude/tools/websearch.py -n 20 "query terms"  # N results
python3 ~/.claude/tools/websearch.py --json "query terms" # JSON output
```
- Hits DuckDuckGo HTML directly. Snippets often quote primary-source pages.
- **Always include source names in the query** to bias toward admissible domains
  (e.g. "arxiv", "NBER", "DORA", "Stanford HAI", "Census Bureau", "Federal Reserve",
  "McKinsey", "SEC 10-K").
- Pair with **WebFetch** to read the actual documents.

### B.3 Reading large PDFs (WebFetch has a ~10 MB inline limit)

```bash
curl -sL -A "Mozilla/5.0" -o /tmp/file.pdf "<url>"   # download to disk
# then use the Read tool with pages: "1-20"  (max 20 pages / request)
```
Worked for MIT NANDA 2025 and DORA 2025. If WebFetch saves a binary to disk, Read that path.

### B.4 Google auth (needed to write to the Doc)

```bash
python3 ~/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py status
# if expired:  ... google_auth.py login
```
Raw Docs API calls need header: `x-goog-user-project: <KARTO_QUOTA_PROJECT — in karto.config>`.

---

## C. DESTINATION — where output goes

### C.1 The living Google Doc
- **Title:** *"Where AI Is Actually Profitable — A Domain Map"*
- **docId:** `<KARTO_DOC_ID — in karto.config>`
- **URL:** <your Google Doc URL — see karto.config>
- **Orientation:** landscape (792×612 pt) — tables are wide.

### C.2 How to append a new row/section
```bash
# 1. Write the section as markdown to /tmp/section.md (use pipe tables — they render).
# 2. Append:
python3 ~/.vibe/marketplace/plugins/fe-google-tools/skills/google-docs/resources/markdown_to_gdocs.py \
  --input /tmp/section.md --doc-id <KARTO_DOC_ID — in karto.config>
```
- Begin sections with `<!-- pagebreak -->` for clean separation.
- **Lens-table formatting learned:** fixed column widths (Lens ~90pt / Score ~120pt /
  Basis ~435pt) + bulleted Basis cells, applied post-hoc via the Docs API
  (`updateTableColumnProperties`, then per-cell delete/insert/`createParagraphBullets`).
  Re-fetch cell indices fresh before each edit to avoid index drift.

---

## D. METHODOLOGY

### 0. Origin — why the method exists
It was not designed on paper and trusted. It was **stress-tested by building a real cell
(Software) and watching it break.** Every rule exists because a specific failure occurred.
The core lesson:

> **Without a source-admissibility gate, a search-first approach does not discover truth —
> it ingests the "dead internet": a flood of AI-generated, confident, numeric,
> fake-authoritative SEO content.** The method is what stands between us and a map that
> looks rigorous and is entirely fabricated.

### 1. Source-admissibility gate (THE CORE RULE)
Discovery surfaces candidates; **admissibility decides what may be cited.**

✅ **Admissible (citable):** peer-reviewed; controlled experiments/RCTs; institutional
reports **with stated methodology** (MIT NANDA, DORA/Google, Stanford HAI AI Index,
McKinsey/BCG, US Census BTOS, Federal Reserve); financial disclosures / SEC filings;
first-party research with methodology; .gov / central banks.

❌ **Inadmissible — disqualify ON SIGHT, never cite even as "directional":** SEO blogs,
"2026 benchmark" content farms, AI-generated listicles, aggregators (getlatka, aistackhub,
swfte, paul-okhrem, ai2.work, ellvero, agentmarketcap, …), any unmethodologied number +
"book a demo" page.

**Consequence (accepted by the user):** cells with only inadmissible evidence read
**⚪ "no credible public evidence yet"** — a real finding, not a failure. Noise is
quarantined, never laundered into a grade.

> User's guiding quote: *"I refuse a sea of crap and contamination / noise. This is a
> serious study. Use proven solid sources (reports) and disqualify SEO junk (dead
> internet theory)."*

### 2. Discovery-first, memory-as-adversary
Never seed a cell from memory (knowledge cutoff Jan 2026 ⇒ memory is stale and biased to
famous pre-cutoff examples). Search surfaces candidates; memory is used *only to attack*
results. (Klarna + Brynjolfsson were memory-seeded — the flaw that triggered this method.)

### 3. Rigor outranks recency
A 2025 RCT beats a 2026 blog, always. Trap: recency pulls toward junk because rigorous
sources are often a year old and the newest material is mostly blogs *citing* them. Date
older admissible sources inline and justify.

### 4. Evidence ladder — rank, don't average
Sources measure different things by methods of different reliability; they can't be
averaged. Build a ladder per cell: each source with **what it actually measures**, the
finding, date, tier. **State the contradiction explicitly**; don't resolve it artificially.
Example (Software): METR RCT → wall-clock, controlled → **−19%** (experts); Brynjolfsson
QJE → issues/hr, field → **+15% / +34% novices**; DORA → self-report + delivery → gains +
rising instability.

### 5. Self-report graded & capped
METR proved self-reported productivity is **systematically inverted** (felt +20%, measured
−19%). Tiers: **HARD** (measured/RCT/financials — any verdict) > **INST** (large-n survey
w/ methodology — moderate, tag self-report) > **SOFT** (vendor/aggregator — directional
only). **Override:** self-reported productivity can never alone push Buyer ROI above 🟡.

### 6. Scoring format per lens
Verdict (🟢 strong · 🟡 partial/conditional · 🔴 weak/unproven/negative · ⚪ no credible
evidence) + **confidence capped by best evidence tier** + evidence ladder + explicit
contradiction line + source-bias flag. Per cell also: durability/moat, three-lens
divergence verdict, and a **gap log** (what couldn't be verified).

### 7. Admissible ≠ unbiased
A source can be rigorous *and* incentivized (e.g. DORA is sound but Google/vendor-sponsored
and flipped pro-AI YoY). Admit it, attach a **"who paid / who benefits"** flag. The gate is
binary; bias is a gradient.

### 8. Triangulation & discipline
≥2 independent origins for load-bearing claims (else label single-source). Separate
**capacity claim** ("does the work of 700 agents") ≠ **headcount action** ("cut 700 jobs")
≠ **P&L result** ("$40M profit"). State correlation≠causation. End every cell with a gap
log — negative space is part of the map.

### 9. Per-cell pipeline
0 Frame sub-questions → 1 Gated discovery (4–6 orthogonal, source-named queries) →
2 Triage (disqualify junk) → 3 Denominator/counter-evidence pass → 4 Primary verification
(read in situ) → 5 Adversarial counter-search → 6 Score+tier+confidence → 7 Divergence
verdict + gap log → 8 Append to Doc.

---

## NOISE FILTER — running blocklist & contamination log

> **Purpose:** turn disqualification from a per-session judgment call into an accumulating,
> auditable record. This list IS evidence of the dead-internet problem. Append to it every
> session — never silently drop a source, log why it was dropped. When a source recurs,
> it's already pre-judged here.

### Disqualified domains seen so far (do not cite, even as "directional")
| Domain | Type | First seen | Note |
|--------|------|-----------|------|
| getlatka.com | Aggregator | Software | fabricated-adjacent metrics (source of "$60B SpaceX buys Cursor") |
| axis-intelligence.com | SEO/listicle | Software | recycled ARR/user numbers |
| idlen.io | Aggregator | Software | unsourced valuations |
| aistackhub.ai | SEO stat farm | Denominator | "87% run AI" — no methodology |
| content-site-lovat.vercel.app | AI-gen listicle | Denominator | "$301B spend" citing everyone, verifying no one |
| swfte.com | SEO stat farm | Denominator | round ROI %s, no method |
| paul-okhrem.com | Aggregator | Denominator/Support | "updated quarterly" compilation, no primary data |
| ai2.work | Vendor blog | Denominator | "pilot era over" narrative piece |
| ellvero.com | Vendor blog | Denominator | CFO-framework SEO |
| agentmarketcap.ai | Aggregator | Denominator | boardroom-talking-point recycling |
| aiquinta.ai | SEO | Denominator | AI Index "explainer", not the source |
| exceeds.ai (blog) | Vendor blog | Software | "300% 3-yr ROI", book-a-demo CTA |
| developersdigest.tech | SEO | Software | vendor-claim aggregation |
| larridin.com | SEO | Software | "benchmarks" no method |
| opsera.ai (report) | Vendor | Software | 250k-dev claim, vendor telemetry — verify before use |
| digitalbiztalk.com | SEO | Software | likely-fabricated "Anthropic study" claim |
| lorikeetcx.ai, brilo.ai, gitnux.org, digitalapplied.com, mavenagi.com | Vendor/SEO | Support | deflection/CSAT stat farms |
| mvidmar.substack.com | Blog | Support | "$60M saved" Klarna figure (contradicts admissible $40M) |
| lasoft.org | SEO | Support | Klarna reversal rewrite, no primary |
| agentmarketcap.ai | Aggregator | FinServ | "JPMorgan $2B return" upgraded net-neutral into a "return" |
| ai2.work | Vendor blog | FinServ | same JPMorgan framing, no primary |
| emerj.com, brilo.ai, imagine-works.com, ghostresearch.com | Vendor/SEO | FinServ | AI-in-banking stat/advisory farms |
| the-risk-dispatch (ghost.io) | Blog | FinServ | governance narrative, no primary data |
| artificialintelligence-news.com | Tech media | FinServ | "$18B / 30-40% ROI" recycling, no primary |
| sciencereader.com, biotech-intelligence.com, humai.blog | SEO | Healthcare | AI-drug-discovery stat/hype pages |
| sully.ai | Vendor | Healthcare | "85% of healthcare AI fails" (MIT-echo, no method) |
| nexchron.com | Vendor survey | Healthcare | NVIDIA-sponsored ROI survey |
| elicitinginsights.com | Survey marketing | Healthcare | "2X+ ROI" health-system self-report |
| aihealthcareinsight.blogspot.com | Blog | Healthcare | "diagnostic mirage" opinion, no primary |
| stealthagents.com, legalaiworld.com, legalnewsfeed.com | SEO | Legal | legal-AI stat/rewrite pages |
| aiweekly.co, finance-monthly.com | SEO/media | Legal | billable-hour rewrites, no primary |
| haqq.ai, gc.ai, vaquill.ai | Aggregator | Legal | repackage Charlotin's sanctions DB as their own |
| seonib.com, serp.systems, buildmvpfast.com, aidev.com | SEO | Sales/Mktg | "AI content SEO penalty" pages, no primary |
| shno.co, voxbooster.com, rivereditor.com, digitalapplied.com | SEO | Sales/Mktg | AI SDR/marketing "benchmark" stat farms |
| kanerika.com | Vendor blog | Sales/Mktg | McKinsey-report rewrite |
| ainvasion.com, perspectivelabs.org, greyjournal.net | SEO | Retail | recycle MIT 95% / RAND 80% without tracing |
| myaifrontdesk.com, ringly.io, opascope.com | Vendor/SEO | Retail | "$18.4B / 89% adoption" retail stat farms |
| **Note:** "RAND 80% AI projects fail" is REAL (RRA2680-1) — verify-and-keep even when a junk source cites it. | — | Retail | discipline works both ways |

### Contamination incidents caught (concrete fabrications the filter stopped)
- **"SpaceX acquires Cursor for $60B"** (getlatka/idlen tier) — almost certainly false; never entered the map.
- **Klarna "$60M saved"** (substack) vs **$40M** (admissible Klarna/PRNewswire release) — aggregators inflated the real figure; used the primary number.
- **"Anthropic study: AI coding no productivity gains"** (digitalbiztalk) — likely a mangled retelling of the METR RCT; a plausible-but-hallucinated *source*. Triangulation to a real origin failed → excluded.
- **Adoption "87%/72%/63% ROI"** round numbers — all traced to the SEO tier; the admissible figure is the Census 18% / employment-weighted 78% split.

### Red flags that trigger disqualification on sight
- A precise % with no stated sample, method, or date.
- "2026 benchmark / statistics / trends" title + listicle format.
- A "book a demo" / product CTA on the same page as the cited number.
- Numbers attributed to "McKinsey/Gartner/IDC" *without* a link to the actual report (launder-by-citation).
- Domains that are themselves AI-generated content mills (generic name + high post volume + no author/methodology).
- A number that's suspiciously rounder or larger than the admissible primary (inflation tell).

### Rule
If a claim exists **only** on disqualified domains, it does not enter the map — the cell
reads ⚪ "no credible public evidence yet." A disqualified source is never upgraded to
"directional." When in doubt, trace to primary or drop it.

---

## E. THE 2026 DENOMINATOR (default priors every cell must beat or match)

Primary-verified (Fed FEDS Note 2026-04-03; Census BTOS + working paper CES-WP-26-25;
Stanford HAI AI Index 2026; MIT NANDA 2025):

1. **Adoption is 18% OR 88% depending who you count:** 18% firm-weighted (Census BTOS,
   the typical US firm) · 78% employment-weighted (oversamples big firms) · 88% "of
   surveyed organizations" (self-selected). Famous high numbers are large-firm-biased.
   Assume the low firm-weighted number unless the vertical is large-enterprise-dominated;
   always state which denominator you mean.
2. **MIT 95/5 rule still holds in 2026:** ~95% of GenAI pilots → zero measurable P&L; ~5%
   cross the divide. No admissible source has overturned it.
3. **Any headline adoption/ROI % above ~60%** is employment-weighted, self-selected, or
   from a disqualified source until proven otherwise.
4. **Real value concentrates in low-complexity, high-volume, novice-heavy tasks;** thins
   for expert/complex work.
5. **Adoption is shallow:** only ~12% of genAI-using workers use it daily.
6. **Consumer surplus ≠ producer profit:** ~$172B/yr US consumer surplus (Stanford 2026)
   is real *user* value, NOT booked profit — the core reason the three lenses stay
   separate.

> Every cell that **beats** these priors is a genuine finding. Every cell that merely
> **matches** them is the null result — and saying so honestly is the point of this map.

---

## G. COUNTRY DEPLOYMENT SWEEP — methodology

**Goal:** enrich the map with named, evidenced AI implementations per country × vertical. A *sample*, NOT a census.

**Hard truth (settled, do not re-litigate):**
- Full census is impossible from public sources — ground truth (who runs AI) is mostly private.
- Public web captures only the ~5% notable enough to generate a filing/study/court record — biased to large, listed, English-first firms.
- We build the reachable slice, label it as a sample, and move on. Something > nothing.

**Axis = country (9):** US · China · UK · Germany · France · Japan · South Korea · India · Russia.
- Rationale: bounds the search, localizes sources, forces out non-US names, and bucket size is itself signal.

**Visibility discount (apply to every bucket):**
- Raw counts measure OUR lens, not reality. Adjust before concluding.
- US = inflated (English + SEC + dense press) → discount down.
- China / Russia / Japan = deflated (language, disclosure norms, indexing) → adjust UP.
- Germany / France / Korea / India = mid.
- A near-empty cell = low adoption OR low visibility — state which, don't assume.

**Search layer (VERIFIED 2026-07):**
- Fix for non-English = QUERY LANGUAGE, not engine. Always query in the target language.
- `~/.claude/tools/websearch.py --engine ddg` in-language = workhorse (validated: EN, FR, DE, RU/Cyrillic, CN).
- `--engine baidu` = bonus .cn depth (works). `yandex` = UNREACHABLE here (HTTP 000); use DDG-in-Russian.
- Japanese/Korean untested — verify at sweep time, don't assume.
- Pair every hit with WebFetch to read the source; big PDFs → curl-to-disk then Read.

**Evidence tiers (same gate as the graded map):**
- **P — Primary-disclosed:** company filing / earnings / official press release with a figure, regulator doc, court record.
- **I — Institutional study:** peer-reviewed / named-methodology report (often sector-level, not company).
- **S — Soft/named case study:** reputable named deployment, no hard number — tagged, kept, never promoted to a cell.
- **REJECT on sight:** vendor marketing, SEO listicles, aggregators, "book a demo" pages, unmethodologied %.

**Per agent (one per country) — contract:**
- Iterate all 20 rows. For each, run in-language gated queries.
- Return STRUCTURED rows: `company · country · vertical · use case · evidence URL · tier (P/I/S) · disclosed metric (if any)`.
- Keep a separate "candidates seen but unverified" bucket — never discard silently (feeds the Noise Filter).
- Empty cell is a valid, expected result — log it, don't pad.

**Output = separate "Deployment Register"** (own doc/tab), NOT mixed into the graded cells.
- Only tier-P entries are promotable into a graded cell, and only after verification.
- Register is explicitly labeled: sample, biased, visibility-discounted — dense for US/UK/large-cap, sparse elsewhere.

**Non-negotiables:**
- Never claim coverage/census. Always "disclosed-evidence sample."
- Never let a country sweep smuggle vendor-tier names into the graded map.
- Log every disqualified domain to the Noise Filter blocklist.

---

## F. STATUS & TAXONOMY

### Status log
- ✅ Frame, method, per-cell schema locked.
- ✅ Method hardened via Row-1 trial-by-fire (4 flaws found & fixed: recency-vs-rigor,
  admissible≠unbiased, can't-average-sources, self-report-inverted).
- ✅ **2026 Denominator** built, primary-verified (Doc section "1B").
- ✅ **Row 1 (Software)** — rebuilt to method-grade. Verdict: "amplifies pre-existing
  engineering maturity; novice value real & measured; expert value on complex code may be
  negative; enterprise ROI system-driven not tool-driven; AI-native margins unproven."
- ✅ **Row 2 (Customer Support)** — REBUILT method-grade. Evidence ladder: Brynjolfsson
  QJE + two 2026 Alibaba RCTs (arXiv 2603.29888, 2605.14830) + Gartner rehire forecast +
  Klarna. Verdict: strongest labor-value evidence in the map (2 independent RCTs, AI
  *compresses skill distribution* — lifts low performers, can degrade top performers'
  quality); buyer ROI path-dependent with a base rate against over-automation (Gartner:
  50% of AI-driven service cuts rehire by 2027); AI-native margins unverified. v1
  memory-seeded version left above it for comparison.
- ✅ **Row 3 (Financial Services)** — method-grade. Chosen as best candidate to BEAT the
  priors; instead delivered the map's sharpest counter-result. Anchor: "The Innovation
  Tax" (arXiv 2602.02607, causal, 809 banks + Fed data) — GenAI adoption *causally* cuts
  ROE −428 bps near-term (J-curve), worse for small banks (−517 bps); correlational
  "adopters more profitable" is selection bias. JPMorgan (Bloomberg/Dimon) = savings ≈
  spend (net-neutral, self-reported). New dimension: systemic "algorithmic coupling" risk.
  Verdict: Buyer ROI 🔴→🟡 (negative near-term), Labor value 🟡 (under-measured in FS),
  AI-native ⚪→🟡. High adoption ≠ booked profit — the naive "follow adoption" thesis
  falsified here.
- ✅ **Row 4 (Healthcare / Life Sciences)** — method-grade. Widest three-lens divergence in
  the map. Documentation: NEJM AI ambient-scribe RCTs (NIH-funded, no vendor money) —
  −0.36 hr/day, −0.44 burnout, no quality loss = genuine 🟢 labor value. Diagnosis: capped
  by MGB/JAMA Network Open (LLMs fail >80% of early differential dx, ~91% on final dx w/
  full info) → not unsupervised-safe. Drug discovery: Insilico rentosertib (Nature Medicine
  s41591-025-03743-2) phase-2a positive = real milestone but 0 approvals, years from P&L.
  Verdict: labor value 🟢 (docs only), buyer ROI 🟡 (docs yes / dx no / discovery deferred),
  AI-native 🟡. Proves map thesis in miniature: value real in high-volume low-stakes task,
  headline uses (dx, discovery) capped or deferred.
- ✅ **Row 5 (Legal & Professional Services)** — method-grade. Sharpest "productivity ≠
  profit" cell. Schwarcz et al. RCT (first legal-AI RCT, no vendor funding): AI raised both
  efficiency (+34–140%) AND quality on 5/6 tasks, RAG hallucinated at no-AI baseline — a
  genuine 🟢 labor value (caveat: law students not lawyers). BUT: Stanford RegLab —
  commercial legal-research tools still hallucinate 17–33% despite RAG; Charlotin DB ~1,600
  court sanctions cases; and Bloomberg/AFR — AI efficiency breaking the billable-hour model
  (Big Four repricing). Verdict: labor value 🟢, buyer ROI 🟡 (structurally conflicted —
  works at task level, erodes firm revenue + capped unsupervised research), AI-native 🟡.
  Unique failure mode: the pilot WORKS and still threatens margins.
- ✅ **Row 6 (Sales & Marketing / Content)** — method-grade. The biggest bet (50-70% of AI
  budget) and the most misplaced. Retail field-experiment (arXiv 2510.12049, revenue-
  measured, 7 RCTs, up to tens of millions of users): GenAI drove real revenue (+16.3% top
  workflow, ~$5/consumer) BUT the gains were in service & search — **advertising/marketing
  workflows showed NO detectable sales impact**. MIT IDE RCT (21,328): AI personalized video
  +9.4pt CTR, ~90% cheaper, but CTR≠revenue + novelty may fade. Verdict: buyer ROI 🟡 (real
  but not where budget goes), labor value 🟢 output/cost / 🟡 outcome, AI-native 🟡 (weakest
  moat in map — content commoditizes, channels self-saturate). Sharpest confirmation of MIT
  NANDA "investment bias": budget follows easy-to-measure, not high-return. NOTE gap: "AI
  content collapses SEO" thesis plausible but all sources disqualified — not admitted.
- ✅ **Row 7 (Retail & E-commerce)** — method-grade. The best-evidenced POSITIVE cell —
  holds the map's only rigorous causal revenue proof (the arXiv 2510.12049 study was run on
  a retail platform: +16.3% sales in service/search). Rare cell where labor value & buyer
  ROI CONVERGE (less search friction → sales). But: gains favor scale incumbents
  (Walmart/Amazon amplify existing data+distribution moats), marketing workflows show no
  lift, agentic commerce stumbling (CNBC), AI-native newcomers shut out. Added 2nd
  denominator: RAND RRA2680-1 (>80% AI projects fail — verified real, synthesis not measured
  rate). Verdict: buyer ROI 🟡 (best-proven), labor value 🟢, AI-native 🟡.
- ✅ **Row 8 (Manufacturing & Robotics)** — method-grade. First cell to land in ⚪ territory —
  the physical-world evidence profile is genuinely thinner. Split: (A) analytics AI (predictive
  maintenance) = 🟡 real ROI (~30-40% downtime reduction) but from systematic reviews of CASE
  STUDIES, not RCTs; WEF Global Lighthouse Network proof is a selection-biased showcase of top
  performers, not a base rate. (B) Humanoid robotics = ⚪ — massive capital + real engineering,
  but ZERO admissible evidence of profit/unit-economics/deployed productivity; every "50-100k
  units deployed" number came from disqualified hype sites. Verdict: buyer ROI 🟡(PdM)/⚪(robots),
  AI-native ⚪→🟡, labor value 🟡. The map's clearest hype-outruns-evidence cell.
- ✅ **Row 9 (Media / Entertainment / Gaming)** — method-grade. The other MIT-flagged
  "disrupted" sector. Genuine disruption, incumbent-captured profit, IP-fragile foundation.
  INFORMS ISR field experiment (120 pro designers): GenAI +76% novelty in IDEATION for all,
  but experts +57% TIME in implementation ("expertise fixation") — the skill-compression law
  now confirmed in a 4TH domain (creative), after coding/support/retail. Netflix Q2 2026:
  ~300 productions used gen AI (mostly post-production), savings support 10% content-spend
  growth — but NO dollar figure. IP risk unique: courts hold AI-only content uncopyrightable
  + training-data suits. Verdict: labor value 🟢(ideation/novice)/🔴(expert exec), buyer ROI
  🟡 (production cost-out, IP-capped), AI-native 🟡 (weakest-IP moat — output may be unownable).
- ✅ **Row 10 (Cybersecurity)** — method-grade. The map's only TWO-SIDED cell (AI serves both
  defenders & attackers). Defensive labor value 🟢 benchmarked (CSA: 45-61% faster SOC work,
  22-29% more accurate — single-vendor caveat; IBM/Ponemon: AI-mature orgs detect faster).
  BUT strongest primary evidence favors OFFENSE: Anthropic (n=832 threat accounts) — 67.3%
  used AI for malware, medium+risk actors 33%→56% in 6mo, AI democratizes post-compromise
  techniques to low-skill actors + near-autonomous attack chains; GTIG corroborates.
  Skill-compression law cuts BOTH ways — arms junior defenders AND script-kiddies. Verdict:
  buyer ROI 🟡 (real productivity, adversarially eroded, net-security-outcome ROI unmeasured),
  AI-native 🟡 (benchmark-inflated), labor value 🟢. Only vertical with no stable equilibrium.
- ✅ **Row 11 (Back-office Ops: finance/HR/procurement)** — method-grade. The LAST horizontal
  function. Best FIT to the denominator's "high-volume/low-complexity/rules-based" prior — and
  MIT's "underfunded, highest-ROI" area. Reality is more conditional: real payback with the
  clearest cost-attribution in the map (finance close, AP, reconciliation) BUT EY: 30-50% of
  RPA/automation projects fail; MIT's "highest-ROI" claim is directional, never quantified.
  HR sub-domain is a rare NEGATIVE-value cell: Stanford study (4M applications, 156 employers)
  found clear racial disparities in AI hiring screening → legal liability, not value. Verdict:
  buyer ROI 🟡 (real-when-it-lands, ~half fail), labor value 🟢 (clerical) / 🔴 (HR screening),
  AI-native 🟡 (RPA being cannibalized by agentic). "Best-kept secret" overstates it.
- ✅ **Row 12 (Insurance)** — method-grade. Sharpest efficiency-vs-liability tension in the map.
  Data-native → real AI operational value (Lemonade Q1 2026: +71% rev, loss ratio −19pp,
  AI-attributed) BUT best-disclosed AI-native insurer STILL unprofitable (−$35.8M net loss,
  profit projected not achieved) — the honest AI-native template. Claims automation generating
  LANDMARK litigation: Estate of Lokken v. UnitedHealth (class action advancing; Senate found
  post-acute denial rate DOUBLED after nH Predict) + Cigna PxDx batch denials → NAIC + state
  human-in-loop laws re-inserting humans, capping ROI. Verdict: buyer ROI 🟡 (real, legally
  fenced), AI-native 🟡 (best-disclosed, loss-making), labor value 🟡/🔴 (throughput yes,
  unsupervised denial harmful). 2nd negative-value sub-domain after HR hiring.
- ✅ **Row 13 (Education)** — method-grade. STRONGEST + most balanced HARD evidence of any cell
  (RCTs both directions + clean disclosed winner/loser). Learning value 🟢 & RCT-proven: Kestin
  Nature RCT (AI tutor >2× learning in less time), Nigeria World Bank RCT (+0.23 SD = 1.5-2 yrs
  schooling in 6 wks, ultra cost-effective) — BUT strictly conditional on pedagogy/supervision;
  turns 🔴 (cognitive debt) unscaffolded per MIT "Your Brain on ChatGPT" (preprint, n=54,
  caveated). AI-native P&L Darwinian: Duolingo profitable ($43M NI) vs Chegg annihilated
  (~$14B→penny). Verdict: buyer ROI 🟡 (learning ROI strong, institutional P&L murky), labor
  value 🟢/🔴 (scaffolded vs shortcut), AI-native 🟡 (real but knife-edge). Reversibility caveat
  = METR expert-atrophy pattern now in LEARNERS.
- ✅ **Row 14 (Government / Public Sector)** — method-grade. Cleanest evidence base in the map
  (almost all primary: gov trials, GAO audits, investigative journalism — least junk). Stark
  two-tier result: INTERNAL efficiency real (UK M365 Copilot trial, 20k civil servants,
  ~2wk/yr saved — but self-reported; GAO confirms internal uses) vs CITIZEN-FACING high-stakes
  = clearest negative-value zone in the map (Amsterdam "Smart Check": €535K + Deloitte +
  responsible-AI best practice, still discriminatory + no better than caseworkers, halted;
  Dutch childcare scandal: 35,000 families falsely accused, government resigned 2021). Verdict:
  buyer/public-value ROI 🟡 (internal) / 🔴 (high-stakes adjudication), labor value 🟢 (staff,
  self-reported), AI-native ⚪ N/A. Denominator's "low-stakes/high-volume good, high-stakes/
  complex harmful" law at its highest human cost. NOTE: least-contaminated cell — authoritative
  institutions publishing directly = thin dead-internet layer.
- ✅ **Row 15 (Logistics & Supply Chain)** — method-grade. Near-replay of Manufacturing:
  frontier-vs-base-rate. Amazon (disclosed, primary): 1M robots + DeepFleet AI ~10% fleet
  travel-time cut, millions of labor-hours targeted — real frontier cost-out. BUT Gartner
  (Apr+May 2026): "AI is NOT driving supply-chain operating-model transformation"; 56% cite
  legacy-integration barrier, 50% talent gap; BCG: few translate APS/AI investment into gains.
  Org/integration constraint again, not the tool. Verdict: buyer ROI 🟡 (frontier yes/median
  no), labor value 🟡, AI-native ⚪→🟡. Excluded junk-tier Amazon "25-40% picking / $0.30/pkg"
  figures (not in Amazon disclosure); used verified 10% travel-time.
- ✅ **Row 16 (Energy & Utilities)** — method-grade. MIT's lowest-adoption sector; evidence
  confirms thin realized value + a striking INVERSION: the hardest measured AI-energy fact is
  that AI CONSUMES energy, not optimizes it. IEA "Energy and AI": data-centre electricity
  415 TWh (2024) → 945 TWh (2030), AI the driver, US AI > all heavy industry. Grid-optimization
  benefits framed by IEA as POTENTIAL not realized; no admissible deployment ROI (all "utility
  AI savings" claims were disqualified vendor/SEO); adoption gated by regulation + legacy infra
  (MDPI). Verdict: buyer ROI ⚪→🟡, AI-native ⚪, labor value ⚪→🟡. The "AI is more a load than a
  lever" cell — energy is the vertical AI most STRESSES rather than optimizes.
- ✅ **Row 17 (Agriculture)** — method-grade. Frontier-vs-base-rate again, but with an unusually
  STRONG disclosed frontier point: John Deere See & Spray — 5M acres (2025), ~50% herbicide
  reduction (~31M gallons saved), +2 bu/acre yield, computer-vision targeted spraying. Real
  physical-world ROI — but requires Deere-scale machinery, so bifurcated by capital. World Bank
  (w/ Gates/Microsoft): smallholders grow ⅓ of world's food but AI value for them "largely
  aspirational" — digital-divide risk. Verdict: buyer ROI 🟡 (large farms) / ⚪ (smallholders),
  labor value 🟡, AI-native ⚪→🟡. Anchored Deere's ~50% (junk inflated to 77-90%).
- ✅ **Row 18 (Telecom)** — method-grade. Data-rich vertical; efficiency real, revenue
  aspirational, value-capture trap. GSMA Intelligence (119-operator survey): 2025 telecom AI was
  PRIMARILY internal cost-optimization (chatbots, predictive maintenance, network energy ~30%
  AI-RAN reduction); operators only NOW shifting toward revenue (monetisation = emerging, not
  achieved). McKinsey: telcos historically "built the digital economy without sharing rewards" —
  AI value may again flow to equipment vendors (Ericsson/Nokia/NVIDIA), not operators. Binding
  constraint = legacy OSS/BSS. Verdict: buyer ROI 🟡 (opex yes/revenue no), labor value 🟡
  (inherits Support cell), AI-native ⚪→🟡. Distinctive = value-capture problem.
- ✅ **Row 19 (Real Estate & Construction)** — method-grade. The cell where the STRONGEST
  evidence is a FAILURE, not a win. Zillow Offers iBuying collapse: ~$881M losses, 25% layoffs,
  product wound down — and the precise lesson: the Zestimate was ACCURATE (1.9% median error);
  what failed was acting mechanically on the model through a housing regime shift without
  treating uncertainty as a throttle (Opendoor survived via human-in-loop + wider spreads).
  Positive evidence thin: AVMs old/commoditized (accuracy claims all junk-tier, excluded);
  construction = least-digitized major industry, AI mostly method-papers. Verdict: buyer ROI
  🔴→🟡, AI-native 🔴→⚪, labor value 🟡. Cross-cutting: high-stakes autonomous decisioning fails
  (joins Insurance claims, Government welfare).
- ✅ **Row 20 (Travel & Hospitality)** — method-grade. FINAL ROW — map complete. Recapitulates
  the central split: operator-side AI real & among better-disclosed signals (Expedia Q1 2026:
  rev $3.43B +14.7%, operating income swung to +$251M, AI credited for conversion/servicing/
  marketing — but no isolated AI $ figure); consumer-facing genAI trip-planning trust-capped
  (Wiley experiments n=1,004: hallucinations reduce intention-to-follow via lowered accuracy/
  trust). Verdict: buyer ROI 🟡→🟢 (operator) / capped (consumer), labor value 🟢, AI-native 🟡.
  Value in the plumbing (pricing/conversion/servicing), incumbent-captured.

**🎉 ALL 20 ROWS COMPLETE (5 functions + 15 verticals). Map done. Next: SYNTHESIS section.**

### CROSS-CUTTING FINDING (emerging across cells)
The **skill-compression law**: AI lifts novices/low performers and often *slows or degrades
experts*, confirmed by independent HARD studies in 4 domains — coding (METR −19% experts),
support (Alibaba RCT, Brynjolfsson +34% novices), retail (less-experienced consumers gain
most), creative (INFORMS experts +57% time). This is the map's most robust cross-vertical
result.

### Row taxonomy
**Horizontal functions** (tracked separately to avoid double-counting): Software/code ·
Customer support · Sales/marketing/content · Back-office ops · Cybersecurity.
**Verticals:** Financial services · Insurance · Legal & professional services · Healthcare
& life sciences · Media/entertainment/gaming · Retail & e-commerce · Manufacturing &
robotics · Education · Government/public sector · Energy & utilities · Logistics & supply
chain · Agriculture · Telecom · Real estate & construction · Travel & hospitality.

### Key admissible sources already located
- MIT NANDA *State of AI in Business 2025* (95/5 rule) — PDF read in full.
- DORA 2025 *State of AI-assisted Software Development* (Google, n≈5,000) — `/tmp/dora2025.pdf`.
- METR RCT — arXiv 2507.09089 (−19% for experts on complex tasks).
- Brynjolfsson, Li & Raymond — NBER w31161 / QJE 140(2) (+15%, +34% novices, n=5,172).
- Stanford HAI AI Index 2026 — hai.stanford.edu/ai-index/2026-ai-index-report/economy.
- US Census BTOS + working paper CES-WP-26-25; Federal Reserve FEDS Note 2026-04-03.

### Suggested next moves
1. Rebuild Row 2 (Support) to method-grade — consolidate before expanding, OR
2. Start **Financial services** — Census/Stanford show highest firm-level adoption, best
   candidate to actually *beat* the grim denominator priors.

---
*Companion memory (cross-session pointer): `~/.claude/projects/-Users-mehdi-lamrani-code-code-karto/memory/ai-profitability-map-project.md` and `websearch-broken-gateway-workaround.md`.*


<!-- SWEEP OUTPUT: Google Sheet 'AI Deployment Register — Country Sweep' -->
<!-- SHEET_ID: <KARTO_SHEET_ID — in karto.config> -->
<!-- URL: <your Google Sheet URL — see karto.config> -->
<!-- Tabs: Register / Findings / Noise / Progress. Agents write local register_<CC>.md; I merge → Sheet (single writer). -->
