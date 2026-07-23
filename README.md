# KARTO AI — Where Is AI Actually Profitable?

> **New here? Read THIS file top to bottom first. It is the baton.** It tells you what
> this project is, what's already done, where everything lives, and how to continue
> autonomously. Then read `MAP-METHODOLOGY.md` (the how) and `AGENT-MANIFESTO.md` (the
> sweep rules). Everything needed to reproduce and continue is in this folder.
>
> Last updated: 2026-07-22.

---

## 1. What this project is (in one paragraph)

An **evidence-graded map of where AI is *actually* profitable**, for a senior AI engineer.
Not a hype survey — a source-gated study. It has **two layers**:
- **DEPTH (the graded map):** 20 rows (5 horizontal functions + 15 industry verticals), each
  scored on 3 profit lenses (Buyer ROI · AI-native P&L · Labor value), with an evidence
  ladder, a "Noise Filter", and honest gaps. Lives in a **Google Doc**.
- **BREADTH (the deployment sweep):** ~1,600 real, named, source-linked AI deployments at
  major listed companies across **14 countries / 5+ languages**. Lives in a **Google Sheet**.
- **VISUALIZATION (the atlas):** a self-contained, offline zoom-cartography dashboard —
  `karto-atlas.html` — with 4 altitudes (Orbit → World → decision-Grid → company Street).
  Built from the canonical data. See §9.
- **Core finding (proven at 2,606 data points across 37 countries):** AI deployment is real &
  near-universal (**78% CONFIRMED** — 2,023/2,606); **independently-audited value proof is
  essentially absent** (only ~32% attach *any* value number, virtually none audited). Adoption ≠
  profit. The breadth sweep empirically confirms the depth map's thesis.

**Hard rule that defines the whole project (never violate):** SOURCE-ADMISSIBILITY GATE.
Only cite peer-reviewed / controlled studies / institutional reports w/ methodology /
financial disclosures / court+regulator records / company own-disclosure. **Disqualify on
sight:** SEO blogs, "2026 benchmark" listicles, vendor marketing, aggregators. Junk-only
cells read ⚪ "no credible evidence yet" — a real finding, not a failure. The user's words:
*"I refuse a sea of crap and contamination. This is a serious study."*

---

## 2. The two live deliverables (THESE ARE THE OUTPUT)

- **📊 [Deployment Register — the live results (view-only)](https://docs.google.com/spreadsheets/d/14BzbimaeY4tSXq6Ia8-gfYRZhUW6ZMlqUzprxgqaIkY/edit)** — the Google Sheet, publicly readable. ~1,600 named AI deployments across 14 countries. Tabs: Synthesis · Register · Findings · Universe · Noise.
- **Google Doc — the graded 20-row map** (*"Where AI Is Actually Profitable — A Domain Map"*): **private** — owner-only. (docId in local `karto.config`.)

---

## 3. Files in this folder (what each is)

| File | What it is |
|------|-----------|
| `README.md` | this baton |
| `MAP-METHODOLOGY.md` | master method + full context (depth map + sweep §G). READ 2nd. |
| `AGENT-MANIFESTO.md` | the verbatim rules a sweep agent follows. READ 3rd. |
| `SWEEP_RULES.txt` | condensed sweep rules handed to each agent (agents read this). |
| `RUN-CONTROL.md` | how the long-running sweep pauses/tracks/resumes. |
| `FINDINGS-LOG.md` | seed qualitative-findings log (per-country versions in data/findings). |
| `tools/websearch.py` | THE search tool (see §5). engines: ddg/baidu/bing; retry/backoff. |
| `data/register/register_<CC>.md` | 14 countries × deployment rows (the raw sweep output, source-linked). |
| `data/findings/findings_<CC>.md` | per-country qualitative signals. |
| `data/universe/universe_<CC>.tsv` | per-country company backbone (index constituents + sector). |
| `scripts/merge_registers_to_sheet.py` | **rebuilds the Sheet Register+Findings tabs from data/** (dedup, country-stamped from filename). |
| `scripts/build_universe_tab.py` | rebuilds the Universe tab from data/universe. |
| `scripts/sweep_stats.py` | computes aggregate stats (total rows, %CONFIRMED, by country). |
| `scripts/write_synthesis.py` | writes the Synthesis tab. |
| `scripts/make_sheet.py` / `populate_universe.py` | one-time Sheet-creation scripts (reference). |

Note: script paths inside the `.py` files point at `/tmp/register_*.md` etc. — if `/tmp` is
empty, either copy `data/register/*` → `/tmp/` first, or edit the glob path to `data/register/`.

---

## 4. CRITICAL ENVIRONMENT FACTS (or you will waste hours)

- **Native `WebSearch` tool is BROKEN here** — returns HTTP 400 on every call. Root cause:
  this session runs through a **Databricks AI Gateway → Anthropic-on-Bedrock**; Anthropic's
  `web_search` server-tool doesn't exist on Bedrock. Not fixable client-side. **Use
  `tools/websearch.py` instead** (or WebFetch). Do not burn time re-diagnosing this.
- **Google auth:** `python3 ~/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py status`
  (login if expired). All Sheets/Docs API calls need header
  `x-goog-user-project: <KARTO_QUOTA_PROJECT — in karto.config>`.
- **Big PDFs:** WebFetch caps ~10 MB → `curl -sL -o /tmp/x.pdf <url>` then Read tool (pages param).

---

## 5. THE SEARCH TOOL (`tools/websearch.py`) — hard-won lessons

```bash
python3 tools/websearch.py "query"                          # DDG (default)
python3 tools/websearch.py --engine baidu "中文 query"       # China depth
python3 tools/websearch.py --engine bing --mkt fr-FR "..."  # locale-targeted
```
- **#1 lesson: query in the TARGET LANGUAGE, not the engine.** DDG indexes Cyrillic/CJK/etc.
  fine — searching in English was the only reason non-US looked "thin." Native-language
  queries surface primary in-country sources (company IR, regulators, national press).
- **The reliable path under load: WebFetch against `https://html.duckduckgo.com/html/?q=<url-encoded native query>`.**
  The raw tool's DDG endpoint gets rate-limited/403'd under parallel load; WebFetch path holds.
- Yandex = unreachable here (HTTP 000). Baidu works but captchas after ~1 call.

---

## 6. HOW TO RESUME / CONTINUE (do this to take the baton)

**A. Rehydrate working dir (if /tmp is empty):**
```bash
cp data/register/*.md data/findings/*.md /tmp/ ; cp data/universe/*.tsv /tmp/ ; cp SWEEP_RULES.txt /tmp/
```

**B. Rebuild canonical data + publish (2 phases, single-writer, dedups):**
```bash
# PHASE 1 — build the CANONICAL table into the repo (source of truth). Commit this.
python3 scripts/merge_registers_to_sheet.py --local     # -> data/register.csv + data/findings.csv
python3 scripts/sweep_stats.py                          # sanity: total rows, %CONFIRMED, by country
# PHASE 2 — publish to Google Sheet (MANDATORY extra step; Sheet is a target, not the source)
python3 scripts/merge_registers_to_sheet.py --publish   # CSV -> Sheet Register/Findings tabs
# (no flag = do both phases)
# PHASE 3 — export the Sheet to a local, open-anywhere file (Excel/Numbers/LibreOffice)
python3 scripts/export_xlsx.py                          # -> karto-report.xlsx (all tabs, formatted)
```
**Data model:** `data/register/register_<CC>.md` = raw per-country agent output (concurrency-safe,
one writer per file). `data/register.csv` = the consolidated deduped CANONICAL table (in git —
the data survives without Google). The Sheet is a **publish target**. Agents NEVER write the CSV
or the Sheet; this script is the single consolidator/writer.

**C. To ADD or COMPLETE a country** (the method that works):
1. Build its universe: get index constituents (Wikipedia via curl+parse, NOT the WebFetch
   summarizer — it hallucinates on long lists) → `data/universe/universe_<CC>.tsv`
   (cols: company<TAB>CC<TAB>index<TAB>sector).
2. Launch ONE sweep agent per country (see agent prompt pattern in git history / prior runs),
   pointing it at its universe file + `SWEEP_RULES.txt`. **PACING IS MANDATORY:** sequential,
   ~25-40s between queries, WebFetch-DDG path, native language, checkpoint per company to
   `/tmp/register_<CC>.md`. **Run 2-3 agents MAX concurrently** — more self-DoS the shared IP.
3. When done: copy `/tmp/register_<CC>.md` → `data/register/`, re-run merge script.

**D. Known open items (user-deferred):**
- **China is 100/300 CSI** — user said "complete later." Add remaining ~200 CSI constituents
  to `data/universe/universe_CN.tsv` and resume the CN agent.
- Optional Sheet nicety: add a full-country-name column (codes ES/BR/CH/IT tripped the user up once).

---

## 7. Current state (2026-07-22)

- **DEPTH map: 20/20 rows COMPLETE** in the Doc (graded, evidence ladders, per-cell Noise Filters).
- **BREADTH sweep: 14 countries COMPLETE** — 1,628 gated source-linked rows, **1,356 CONFIRMED (83%)**:
  US 503 · JP 324 · CN 118(of 300) · KR 109 · UK 107 · IN 105 · FR 88 · IT 67 · DE 40 · ES 36
  · RU 35 · BR 31 · CH 29 · MA 28. Synthesis tab written.
- **DATA REPAIR (2026-07-22):** found + fixed column drift in 772/1,628 rows (existence token was
  trapped in `use_case`, value/tier shifted). This corrected CONFIRMED from a bug-deflated 761 to
  the true 1,356. Fixer: `scripts/fix_column_drift.py`; backup: `data/register.backup-drift-20260722.csv`.
- **The finding holds in all 14:** deployment ubiquitous & named; independent value proof absent;
  rich skeptic layer (abstainers, reversals, documented failures, legal high-stakes cluster).
- **VISUALIZATION COMPLETE:** all 4 altitudes built (`karto-atlas.html`). NOT yet human-QA'd end-to-end.

---

## 8. Hard-won behavioral notes (the user is exacting — heed these)

- **Don't overclaim.** "Reported" ≠ "documented"; a news article about X ≠ X's filing. Default
  to the lower evidence tier. State what you actually verified.
- **Don't bail / don't ask permission at every fork.** Diagnose, fix, act. Surface only genuinely
  irreversible or ambiguous decisions.
- **Walk the trail, don't theorize.** Every method rule here exists because a real trial broke the
  paper version. Trust the built+tested, flag the untested.
- **Something > Nothing > Poop.** A biased, labeled sample beats an empty page; junk beats nothing
  in neither direction — reject it.
- **Completeness over convenience.** Don't silently shrink scope to fit tooling limits.

---

## 9. THE VISUALIZATION — the KARTO Atlas dashboard

A **self-contained, offline** HTML dashboard (`karto-atlas.html`, ~1.5 MB, no CDN — D3 + fonts +
data all inlined). Warm editorial "zoom-cartography" with 4 linked altitudes:
- **A0 Orbit** — the thesis in one screen (hero 1,628 + KPIs + the honest value-proof gap bar).
- **A1 World** — map (bubble size = deployments, color = adoption density) ⇄ ranked-bar twin;
  metric toggle Density/Volume/Proof%. Click a country → A2.
- **A2 Grid** — the decision grid: 20 verticals × 6 functions. Verdict mode (proven/active/talk,
  glyph+color) ⇄ Volume mode; row/column hover emphasis; table twin. Click a cell → A3.
- **A3 Street** — slide-in panel listing every company in that cell: use-case, existence glyph,
  tier chip, value number, date, source↗.

**Design spec:** `DASHBOARD-DESIGN.md` (warm palette VALIDATED via dataviz `validate_palette.js`).

**Data pipeline (all repo-owned, regenerable):**
```bash
python3 scripts/fix_column_drift.py    # one-time repair (already applied; safe/idempotent — re-run is a noop on clean data)
python3 scripts/cook_aggregates.py     # data/register.csv -> data/atlas.json (cooked aggregates + verdicts)
python3 scripts/build_atlas.py         # data/atlas.json + vendored D3/topojson/fonts -> karto-atlas.html
```
- `data/atlas.json` = cooked aggregates (global stats, per-country, vertical×horizontal grid with
  verdicts, per-cell company drill-downs). Rebuilt from `register.csv` — never hand-edited.
- **Verdict rule** (in `cook_aggregates.py::verdict_for`): the scarce honest signal is a *quantified
  value number* (~34% of rows; tier-P is too common at 58% to discriminate). Per cell:
  `strong` = ≥40% carry a number · `active` = ≥15% · `talk` = <15% or nothing confirmed.
- Vendored offline assets in `tools/vendor/` (d3.v7, topojson-client, Archivo Narrow + Source Serif 4
  fonts) + `data/world-110m.json` (topojson land).

**Open viz items:** end-to-end human QA pass pending; parked classification debt (see
`CLASSIFICATION.md` §"Open classification debt": Food&Bev has no vertical, Agriculture near-empty).

---

## 10. V2 — decision instrument (built from `karto-v2-implementation-instructions.md`)

V2 turns the descriptive census into a decision tool. Decisions locked in
`karto-v2-BUILD-DECISIONS.md` (hash routing, no resweep, no LLM). All 7 phases shipped:
- **B3** 4-state verdict (proven/active/**unquantified**/talk) · **D8** density tooltip + methodology note
- **A1** `data/universe.csv` (2,468 searched; `build_universe.py`) · **B1** `companies[]` · **B2** peer percentiles · **D4** Silent list (`#/silent`, 491 companies)
- **A2** `data/claims.csv` (regex value-extraction; `extract_claims.py`) · **A5** freshness badges · **D6** hype detector (`#/hype`)
- **B4** momentum (deployments-by-year, labels) · **D5** trends view (`#/trends`)
- **A4** maturity L0–L4 · **B6** findings join · **D1** company pages (`#/company/{slug}`)
- **C1** compare fn · **D2** compare view (`#/compare?c=…`) · **D3** persona tiles
- **B7** insight cards · **B5** prospect/whitespace scores · **C3** static API (`api/**.json`, `build_api.py`) · **D7** markdown briefing export

**Extra build steps (run after cook):** `python3 scripts/extract_claims.py` · `python3 scripts/build_universe.py` · `python3 scripts/build_api.py`.
**Deferred (needs the resweep):** company size data (mktcap/rev/employees → unlocks size-weighted B1/B5); A3 commitments (FS pilot — schema in `data/commitments.csv`, empty); C2 NL query bar.
**Static API:** `https://mehdi-dbx.github.io/karto-ai/api/index.json` catalogs all entities; `api/company/{slug}.json` etc. (CC BY-NC).
