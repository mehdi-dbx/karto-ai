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
- **Core finding (proven at 1,628 data points):** AI deployment is real & near-universal
  (89% CONFIRMED); **independently-audited value proof is essentially absent** (US: 0 across
  503). Adoption ≠ profit. The breadth sweep empirically confirms the depth map's thesis.

**Hard rule that defines the whole project (never violate):** SOURCE-ADMISSIBILITY GATE.
Only cite peer-reviewed / controlled studies / institutional reports w/ methodology /
financial disclosures / court+regulator records / company own-disclosure. **Disqualify on
sight:** SEO blogs, "2026 benchmark" listicles, vendor marketing, aggregators. Junk-only
cells read ⚪ "no credible evidence yet" — a real finding, not a failure. The user's words:
*"I refuse a sea of crap and contamination. This is a serious study."*

---

## 2. The two live deliverables (THESE ARE THE OUTPUT)

- **Google Doc — the graded 20-row map:** *"Where AI Is Actually Profitable — A Domain Map"*
  docId `<KARTO_DOC_ID — in karto.config>`
  <your Google Doc URL — see karto.config>
- **Google Sheet — the deployment register:** *"AI Deployment Register — Country Sweep"*
  sheetId `<KARTO_SHEET_ID — in karto.config>`
  <your Google Sheet URL — see karto.config>
  Tabs: **Synthesis · Register · Findings · Noise · Progress · Universe**

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
- **BREADTH sweep: 14 countries COMPLETE** — 1,628 gated source-linked rows, 1,448 CONFIRMED (89%):
  US 503 · JP 317 · CN 118(of 300) · KR 109 · UK 107 · IN 105 · FR 88 · IT 67 · DE 40 · ES 36
  · RU 35 · BR 31 · CH 29 · MA 28. Synthesis tab written.
- **The finding holds in all 14:** deployment ubiquitous & named; independent value proof absent;
  rich skeptic layer (abstainers, reversals, documented failures, legal high-stakes cluster).

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
