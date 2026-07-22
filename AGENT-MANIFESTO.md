# Agent Manifesto — AI Deployment Sweep

Single instruction set every sweep agent follows verbatim. Country-agent = one country, walks all 20 rows.

## 0. Mission
- Find **named, real AI implementations** in your assigned country, per vertical.
- You build a **sample, not a census.** Most deployments are private/invisible — do not pretend otherwise.
- **Something > Nothing > Poop.** Keep real activity even if unproven. Reject smoke. Never pad.

## 1. The two questions (ask both, per candidate)
- **EXISTENCE — is a serious entity demonstrably doing it?**
  - CONFIRMED = the company's own disclosure / filing / press release / named deployment → **KEEP**
  - CLAIMED = third party says so, no primary confirmation → keep, tag CLAIMED
  - SMOKE = vendor marketing / SEO / aggregator / "book a demo" → **REJECT on sight**
- **VALUE — is there a number, and what kind?**
  - default assumption: **self-claimed** (a company press number is marketing, not proof)
  - independent/audited measure = **rare (~never)** → if you hit one, **flag it by hand**, loudly
  - no number = fine, log as "activity, value unproven"

## 2. The 3-filter (run in your head BEFORE recording anything)
1. **Reachable?** Did you actually open the source? If untested, say untested.
2. **Relevant to THIS question?** (who profitably deploys — not "AI exists generally," not a failure/lawsuit unless the row is about harm)
3. **What tier, honestly?** Default LOW. "Reported" ≠ "documented." A news article about X ≠ X's filing.
- If a candidate fails any filter → drop it or bucket it as unverified. Do not launder it upward.

## 3. Search (verified — do not improvise)
- **Query in the TARGET LANGUAGE.** English-only = blind to non-US. This is the #1 rule.
- `python3 ~/.claude/tools/websearch.py --engine ddg "<native-language query>"` = workhorse (works EN/FR/DE/RU/CN).
- China: also `--engine baidu`. Russia: DDG-in-Russian (Yandex is unreachable, don't try).
- Every kept hit → **WebFetch the source** to confirm it's real. Big PDF → curl to /tmp then Read.

### 3a. ENUMERATE from stock indices FIRST (primary method — beats generic queries)
- Start from your country's index = the real large-cap universe → query company names DIRECTLY (`"<CompanyName> IA/AI <native: results/annual report>"`). This kills SEO bias and makes coverage systematic, not luck-based.
- SCOPE = ALL indices, ALL countries — the FULL constituent list, not a subset. (Do not shrink to a "trial subset" — that was a wrong assumption, corrected.)
- Countries (10): US→S&P 500 · China→CSI 300 + Hang Seng · UK→FTSE 100 · France→CAC40 (+SBF120) · Germany→DAX40 · Japan→Nikkei 225 · Korea→KOSPI 100 · India→Nifty 50 (+Next 50) · Russia→MOEX · Morocco→MASI 20.
- Add more indices/countries as needed; verticals also flex (add/split as data demands).
- **QUEUED FOR END (add after the first 10 complete):** Spain→IBEX 35 · Italy→FTSE MIB · Switzerland→SMI (query DE+FR+EN, multilingual) · Brazil→IBOVESPA (Portuguese). All Latin-script → DDG-WebFetch path, no new engine.
- Each constituent has a known sector → free company→vertical mapping.
- **Gaps are data:** if most index firms show no findable AI disclosure, THAT is the finding (low disclosure/adoption) — now measurable, not invisible.
- **Caveat:** indices = large-caps only. Miss SMEs / private / startups (much AI-native activity). Backbone, not whole picture.

### 3b. Generic queries SECOND (catch the long tail)
- Then run `<vertical> <native "AI results / annual report">` + a skeptic variant, to catch non-index and AI-native players the index misses.

## 4. Reject list (SMOKE — never cite, log to Noise Filter)
- vendor blogs, "2026 statistics/benchmark" listicles, aggregators, SEO stat farms, unmethodologied % + CTA.
- If a claim exists ONLY on these → it does not exist for us. Cell = empty.

## 5. Output — structured rows ONLY (no prose)
Per finding:
`company | country | vertical | use case (1 line) | evidence URL | existence (CONFIRMED/CLAIMED) | value (self-claimed figure or NONE) | tier (P/I/S)`
- **P** = primary disclosure/filing · **I** = institutional/peer-reviewed study · **S** = reputable named case study, no number.
- Also return: **"unverified candidates"** bucket (seen but couldn't confirm) — never discard silently.
- **Empty vertical = valid result.** Write "no confirmed deployment found" — do NOT invent.

## 6. Country reality (state it, don't fight it)
- Your raw count reflects **visibility, not truth.** Note your country's discount:
  - US = inflated. China/Russia/Japan = deflated (search harder in-language). Others = mid.
- A thin cell = low adoption OR low visibility. Say which you think it is; don't assume.

## 7. Hard bans
- No census/coverage claims. Always "disclosed sample."
- No promoting SMOKE or CLAIMED into a graded profitability verdict.
- No stating a conclusion you didn't walk to. Trial the source, then record.
- No rounding up. CONFIRMED-existence ≠ proven-value. Keep them separate.
- **NEVER drop the source URL.** Every register row and every findings-log entry carries the full clickable link to its source. A claim without its URL is unverifiable = worthless. No paraphrasing a source into anonymity. If a fact has no linkable source, it does not go in.

## 8. Deliverable — TWO outputs, WRITTEN TO YOUR OWN COUNTRY FILES
- **PARALLEL SAFETY: never write to the Google Doc. Never write to a shared file.** Agents run concurrently; the Doc is index-based and would corrupt under concurrent writes. Write ONLY to your own country-scoped files. A single merge step (run later, single-threaded) consolidates all countries into the Doc.
- **(a) Register** → `register_<CC>.md` (e.g. `register_FR.md`) — structured table (§5 schema), all 20 rows. The *counting* layer. **Append per company as you go** (checkpoint — if you die, partial file survives).
- **(b) Findings** → `findings_<CC>.md` — notable QUALITATIVE signals: skeptical press, regulator warnings, surprising/contradictory numbers, deliberate non-disclosure. NOT company rows — insight. Format: `vertical · finding · source URL · why it matters · date`. (e.g. Le Monde: "French banks rationing AI, terrified by costs, no process run end-to-end by AI" — a killer counter-signal that vanishes if only the table is kept.)
- Plus in your files: unverified-candidates bucket + SMOKE domains hit (for the Noise Filter).
- Every row/finding carries its **full source URL** (§7). Register + Findings feed the map; neither IS the graded map (only tier-P promotable, after verification).


<!-- SWEEP OUTPUT: Google Sheet 'AI Deployment Register — Country Sweep' -->
<!-- SHEET_ID: <KARTO_SHEET_ID — in karto.config> -->
<!-- URL: <your Google Sheet URL — see karto.config> -->
<!-- Tabs: Register / Findings / Noise / Progress. Agents write local register_<CC>.md; I merge → Sheet (single writer). -->
