#!/usr/bin/env python3
"""harvest_nation.py — nation-state AI-policy harvest (KARTO third axis).

Implements SPEC v3 (docs/nation-axis-spec-v3.md), which survived two adversarial
review rounds. Per country, four ALLOWLISTED sourcing streams feed ONE Gemini 2.5
Flash call that emits a field-provenance'd JSON record:

  1. PDF      — the country's own strategy doc (pdftotext; scanned/image PDF is
                FLAGGED extraction_failed, never OCR'd, never guessed).
  2. NEWS     — Serper web: funding announcements, national champion, military
                signals, whether the implementing ministry actually spends.
  3. INFRA    — Serper restricted to a datacenter/compute allowlist: capacity
                BAND (never a raw MW number), sovereign-vs-hyperscaler, power.
  4. PROCURE  — Serper restricted to trade/procurement allowlist (WTO GPA, USTR,
                World Bank): procurement_access — the variable the opportunity
                model turns on.

Discipline (inherited from the demand-side register, hard rules):
  * No fabrication. Every volatile field carries {value,source_url,source_date,
    source_tier}; a field with no field-level source is null. The model is told:
    real source or null — never invent.
  * compute_band is a BAND from the infra allowlist only; a generic news hit may
    NOT populate it -> unknown.
  * funding_status 'appropriated' needs a primary budget instrument, else
    'announced'.
  * chip_regime is stored as an instrument {rule_or_deal,effective_date}, NOT an
    enum of a (rescinded) tier regime.
  * chokepoint_node is NOT harvested — it is joined from
    data/chokepoint-registry.json at write time.
  * opportunity_read must cite the premise field-values it rests on, or be null.
    Military AI is SURFACED as fact (drones, doctrine, lethal-autonomy stance),
    never censored; held to the same evidence bar as every field. Only
    fabrication and operational how-to are out of bounds.
  * source_date + a Wayback snapshot URL are captured so a dead link later can be
    told apart from a fabrication.

Model: Gemini 2.5 Flash via Google AI Studio key at ~/.config/karto/gemini_key
(free tier; ~$0 for the whole run). Runs OUTSIDE any Claude context.

Usage:
  python3 scripts/harvest_nation.py --countries US,CN,AE,SA,IN,KR,JP,FR,SG,IL \
      --out data/nation-facts.json
  # resumable: countries already in --out are skipped unless --force.
  # --limit N for a smoke run; --dry to skip the model and just show bundles.
"""
import argparse, json, os, re, subprocess, sys, time, urllib.request, urllib.parse, urllib.error, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# ISO2 the caller passes -> the country name + iso3 in docs/nation-sources.csv
# (loaded from the CSV so we never hardcode the roster twice).

# --- infra allowlist: only these domains may back a compute_* field (F4') -----
# Broadened after pilot (P5: 0/10 populated). Reputable DC-industry + energy
# sources; tier=aggregator. Expect ~4-6/10 populated, not 10/10 — per-country MW
# genuinely isn't in snippets for many countries (paywalled DC reports).
INFRA_ALLOW = ["datacentermap.com", "cloudscene.com", "iea.org",
               "datacenterdynamics.com", "dcd", "data-center-map",
               "cushmanwakefield.com", "dgtlinfra.com", "dcbyte.com",
               "semianalysis.com", "synergyresearch", "statista.com",
               "constructionreview", "brightlio", "baxtel.com", "cbre.com"]
# --- procurement/trade allowlist: only these may back procurement_access (F1')
PROCURE_ALLOW = ["wto.org", "ustr.gov", "worldbank.org", "trade.gov",
                 "gpa", "sgp.gov", "oecd.org", "europa.eu"]
# --- law/enforcement stream: sources that can license an ethics_stance TAIL ----
# (state-control/rights-based/permissive) beyond generic strategy language (F2').
# Gov/legal/regulator domains + reputable law trackers. NOT social/forum.
LAW_ALLOW = [".gov", "europa.eu", "oecd.org", "iapp.org", "loc.gov",
             "cac.gov.cn", "gov.uk", "legislation", "官方", "regulation",
             "dig.watch", "future-of-life", "stanford.edu"]

# ---------------- keys ----------------
def _gemini_key():
    p = os.path.expanduser("~/.config/karto/gemini_key")
    if os.path.exists(p):
        return open(p).read().strip()
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    sys.exit("harvest_nation: no Gemini key (~/.config/karto/gemini_key). Cannot harvest — do NOT fabricate.")

def _serper_key():
    k = os.environ.get("SERPER_API_KEY", "").strip()
    if k:
        return k
    p = os.path.expanduser("~/.config/karto/serper_key")
    if os.path.exists(p):
        return open(p).read().strip()
    sys.exit("harvest_nation: no Serper key (~/.config/karto/serper_key).")

# domains dropped at retrieval so junk never even reaches the model (upstream of
# the validator's V2 log-in-field catch — belt and suspenders).
DROP_DOMAINS = ["reddit.com", "facebook.com", "twitter.com", "x.com",
                "youtube.com", "youtu.be", "quora.com", "chinamil.com.cn",
                "rt.com", "sputnik", "tass.ru", "presstv", "globaltimes.cn",
                "xinhuanet", "linkedin.com/posts", "linkedin.com/pulse",
                "medium.com"]

# ---------------- serper ----------------
def serper(query, num=6):
    body = json.dumps({"q": query, "num": num}).encode()
    req = urllib.request.Request("https://google.serper.dev/search", data=body,
        headers={"X-API-KEY": _serper_key(), "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []
    out = []
    for h in (data.get("organic") or []):
        link = (h.get("link") or "").strip()
        if any(d in link.lower() for d in DROP_DOMAINS):
            continue  # never surface social/forum/adversary-state-media to the model
        out.append({"title": (h.get("title") or "").strip(),
                    "link": link,
                    "snippet": (h.get("snippet") or "").strip(),
                    "date": h.get("date", "")})
        if len(out) >= num:
            break
    return out

def serper_allowlisted(query, allow, num=8):
    """Search, then keep ONLY results whose URL matches the allowlist (F1'/F4')."""
    hits = serper(query, num=num)
    return [h for h in hits if any(a in h["link"].lower() for a in allow)]

# ---------------- fetch / pdf ----------------
_TAG = re.compile(r"<[^>]+>"); _WS = re.compile(r"\s+")
def fetch_html_trim(url, cap=4000):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 karto-nation"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read(600_000).decode("utf-8", "ignore")
    except Exception:
        return ""
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", raw))).strip()[:cap]

def fetch_strategy_text(iso3, url, cap=90000):
    """Download strategy source to gitignored cache; extract text.
    Returns (text, status). status: 'ok' | 'extraction_failed' | 'no_url' | 'fetch_failed'."""
    if not url:
        return "", "no_url"
    cache_dir = os.path.join(ROOT, "data", "nation-pdfs")
    os.makedirs(cache_dir, exist_ok=True)
    is_pdf = url.lower().endswith(".pdf")
    ext = "pdf" if is_pdf else "html"
    path = os.path.join(cache_dir, f"{iso3}.{ext}")
    if not os.path.exists(path):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 karto-nation"})
            with urllib.request.urlopen(req, timeout=40) as r:
                open(path, "wb").write(r.read(20_000_000))
        except Exception:
            return "", "fetch_failed"
    if is_pdf:
        txt_path = path[:-4] + ".txt"
        subprocess.run(["pdftotext", path, txt_path], capture_output=True)
        if not os.path.exists(txt_path):
            return "", "extraction_failed"
        txt = open(txt_path, errors="ignore").read()
        # image-scan detection: multi-page PDF yielding < 200 words = failed (F10/spec)
        if len(txt.split()) < 200:
            return "", "extraction_failed"
        return txt[:cap], "ok"
    else:
        txt = fetch_html_trim(url, cap=cap)
        return (txt, "ok") if len(txt.split()) >= 80 else (txt, "extraction_failed")

# ---------------- wayback snapshot (F7') ----------------
def wayback(url):
    """Trigger/lookup a Wayback snapshot so a dead link later != a fabrication."""
    try:
        api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
        with urllib.request.urlopen(api, timeout=15) as r:
            d = json.loads(r.read().decode())
        snap = d.get("archived_snapshots", {}).get("closest", {})
        return snap.get("url", "")
    except Exception:
        return ""

# ---------------- the schema prompt ----------------
SCHEMA_INSTRUCTIONS = """You extract structured facts for KARTO's nation-state AI axis. \
You are given a country name and five evidence bundles (STRATEGY, NEWS, INFRA, PROCUREMENT, LAW). \
Return ONLY valid JSON matching the schema. HARD RULES:
- NEVER invent. If the bundles do not support a field, use the honest empty value ("unknown"/"not-found"/"not-stated"/null). A wrong confident value is worse than empty.
- EVERY metric is an object: {"value":..., "summary":<one factual sentence of CONTEXT, not just the label — this is required and is the most important part>, "source_url":..., "source_date":<ISO YYYY-MM-DD if determinable, else the raw string>, "source_tier":"primary"|"secondary"|"aggregator"}. source_url MUST be a URL present in the bundles; if none, value uses the empty value and source_url is null. The `summary` gives the reader the context a bare label cannot (e.g. WHAT the $40B is, WHY the stance is what it is).
- funding is a LIST of entries (multiple allowed — a fund, a program, and a defense line are DIFFERENT entries, never merged). Each entry: {"value":<amount+currency>, "figure_scope":"investment-fund"|"national-program"|"single-initiative"|"defense-only"|"multi-year-total", "period":<years if stated>, "status":"announced"|"appropriated"|"unknown", "summary":..., "source_url":..., "source_date":..., "source_tier":...}. status "appropriated" REQUIRES a primary budget-instrument source (budget law/appropriation/cabinet allocation); a press headline supports only "announced".
  * AI-NEXUS GATE (critical): a funding entry must be money FOR AI specifically. Do NOT include general R&D budgets, whole-of-defense budgets, or missile/weapons budgets just because "AI" appears near them. If a figure is a national R&D total or a defense budget that merely mentions AI, EXCLUDE it. Ask: is this money earmarked for AI? If not, drop the entry. (e.g. a country's total ¥40T R&D budget is NOT an AI funding entry; a record defense budget is NOT an AI funding entry.)
  * STALENESS: prefer figures from the last ~3 years. If you include an older figure, its period/date must make the vintage explicit; never present a pre-2023 figure as a current peer.
- compute_band: use ONLY the INFRA bundle. If INFRA has no capacity figure, value="unknown". Never derive datacenter size from news/strategy. BAND: "<10MW"|"10-100MW"|"100-1000MW"|"GW-scale"|"unknown".
- compute_control: sovereign|hyperscaler-hosted|mixed|unknown. If your only source is the strategy PDF (aspiration, not infrastructure), say so in the summary and prefer "unknown" over "sovereign".
- chip_regime: {"value":<current export rule or bilateral deal affecting this country's chip access>, "effective_date":..., "summary":..., "source_url":...} or null. NOT a tier enum.
- military_ai: value one of "active"|"stated"|"not-found" ("not-found" NOT "absent" — silence is expected). SURFACE military AI as IMPORTANT FACT — do NOT censor, bury, or soften it. The summary should carry the real texture (e.g. "AI-enabled ISR/drones fielded; lethal autonomy officially off the table [src]"). This is critical intelligence, recorded plainly and sourced.
- ethics_stance: value "stated-generic" is honest for the usual "responsible & human-centric" strategy language. Assign a TAIL ("rights-based"|"permissive"|"state-control") ONLY if the LAW bundle (a real law/regulation/enforcement action, NOT the strategy PDF) supports it. The summary must explain the call (e.g. "generic strategy language, but CAC algorithm-registration + generative-AI measures impose de-facto state control [law src]").
- procurement_access: use ONLY the PROCUREMENT bundle. If empty -> "unknown".
- general_idea: 3-5 sentence prose synthesis of the country's actual posture.
- DO NOT produce opportunity_read here. The opportunity read is generated in a SEPARATE pass AFTER validation, so it can never cite a value the validator later degrades (e.g. an "appropriated" that becomes "announced"). Omit it.
SCHEMA:
{
 "funding": [ {entry}, ... ],             // LIST; [] if none found
 "procurement_access": {metric},          // open-tender|champion-gated|offset-localization|closed|unknown
 "apparatus": {metric, plus "confirmed_active": true|false|null},  // AI office + IMPLEMENTING ministry (the spender, not just the strategy author)
 "compute_band": {metric},
 "compute_control": {metric},
 "chip_regime": {metric or null},
 "power_posture": {metric},               // abundant|constrained|unknown
 "national_champion": {metric or null},
 "military_ai": {metric},                 // surfaced as fact, rich summary
 "ethics_stance": {metric},
 "sectors": [str],
 "general_idea": str
}
Every {metric} MUST include the "summary" field. Do NOT include opportunity_read. Return the JSON object only."""

def gemini_extract(country, bundles):
    key = _gemini_key()
    bundle_text = ""
    for name, items in bundles.items():
        bundle_text += f"\n\n===== {name} BUNDLE =====\n"
        if isinstance(items, str):
            bundle_text += items[:90000]
        else:
            for h in items:
                bundle_text += f"[{h.get('date','')}] {h['title']} — {h['link']}\n{h.get('snippet','')}\n"
    prompt = SCHEMA_INSTRUCTIONS + f"\n\nCOUNTRY: {country}\n" + bundle_text
    # Gemini 2.5 Flash is a reasoning model: 'thinking' tokens count against
    # maxOutputTokens. Budget generously (thoughts + a ~1.5k-token JSON record)
    # or the JSON truncates mid-string. thinkingBudget caps the reasoning spend.
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                 "maxOutputTokens": 12288,
                                 "thinkingConfig": {"thinkingBudget": 3072}}}
    req = urllib.request.Request(GEMINI_URL, data=json.dumps(body).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode())
    cand_obj = resp["candidates"][0]
    finish = cand_obj.get("finishReason")
    parts = cand_obj.get("content", {}).get("parts", [])
    cand = parts[0]["text"] if parts else ""
    usage = resp.get("usageMetadata", {})
    if finish == "MAX_TOKENS" or not cand.strip():
        raise RuntimeError(f"gemini truncated/empty (finishReason={finish}, "
                           f"thoughts={usage.get('thoughtsTokenCount')}, out={usage.get('candidatesTokenCount')})")
    try:
        return json.loads(cand), usage
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gemini non-JSON (finishReason={finish}): {str(e)[:80]}; head={cand[:120]!r}")

# ---------------- opportunity_read (POST-VALIDATION pass, blocker #3) ----------
READ_INSTRUCTIONS = """You write ONE opportunity_read for a nation's AI profile, for a \
state-agency contractor/counselor. You are given the country's ALREADY-VALIDATED facts \
(post-gate: any degraded/dropped values are final — trust them exactly, do NOT upgrade). \
Rules:
- 2-4 sentences. Cite the specific field VALUES it rests on, e.g. "Because funding status is announced (not appropriated) and procurement_access is open-tender ...". Use the values AS GIVEN — if status says "announced", never write "appropriated".
- MINIMUM premise set: you need funding status + procurement_access + at least one capability field (compute_band/compute_control/chip_regime/national_champion), all non-unknown. If that set is not met, return exactly {"opportunity_read": null}.
- Military/defense posture is stated as FACTUAL OBSERVATION when present and sourced (surface it, don't hide it); never framed as operational how-to.
- Ground every clause in a provided value; invent nothing.
Return ONLY {"opportunity_read": <string or null>}."""

def generate_read(record):
    """Second Gemini pass over the VALIDATED facts (blocker #3: the read can never
    cite a value the validator already degraded). Deterministic inputs -> the read
    reflects the post-gate record, not the raw extraction."""
    f = record.get("facts", {})
    # compact the validated facts to the fields a read may rest on
    view = {"country": record["country"],
            "funding": [{"value": e.get("value"), "status": e.get("status"),
                         "figure_scope": e.get("figure_scope")} for e in (f.get("funding") or [])],
            "procurement_access": (f.get("procurement_access") or {}).get("value"),
            "compute_band": (f.get("compute_band") or {}).get("value"),
            "compute_control": (f.get("compute_control") or {}).get("value"),
            "chip_regime": (f.get("chip_regime") or {}).get("value") if isinstance(f.get("chip_regime"), dict) else None,
            "national_champion": (f.get("national_champion") or {}).get("value") if isinstance(f.get("national_champion"), dict) else None,
            "military_ai": (f.get("military_ai") or {}).get("value"),
            "sectors": f.get("sectors"),
            "chokepoint_node": (record.get("chokepoint_node") or {}).get("value")}
    prompt = READ_INSTRUCTIONS + "\n\nVALIDATED FACTS:\n" + json.dumps(view, ensure_ascii=False)
    key = _gemini_key()
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                 "maxOutputTokens": 2048, "thinkingConfig": {"thinkingBudget": 512}}}
    req = urllib.request.Request(GEMINI_URL, data=json.dumps(body).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        resp = json.loads(r.read().decode())
    try:
        txt = resp["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(txt).get("opportunity_read")
    except Exception:
        return None

def reads_pass(out_path):
    """Load a validated file, generate opportunity_read per record, write back."""
    d = json.load(open(out_path))
    for rec in d.get("records", []):
        try:
            rec["facts"]["opportunity_read"] = generate_read(rec)
            print(f"  read {rec['iso2']}: {'null' if not rec['facts']['opportunity_read'] else 'ok'}")
        except Exception as e:
            print(f"  read {rec['iso2']}: ERROR {e}")
        time.sleep(6)
    d.setdefault("_meta", {})["reads_generated_post_validation"] = True
    json.dump(d, open(out_path, "w"), indent=2, ensure_ascii=False)
    print(f"reads written -> {out_path}")

# ---------------- csv roster ----------------
def load_roster():
    """key -> {country, iso3, region, url} from docs/nation-sources.csv.
    Keyed by BOTH iso3 and (where known) iso2, so --countries accepts either.
    At 89-scale we key primarily on iso3 (present in every CSV row); the iso2
    aliases are a convenience for the pilot set."""
    import csv
    iso3_to_iso2 = {"USA":"US","CHN":"CN","ARE":"AE","SAU":"SA","IND":"IN","KOR":"KR",
        "JPN":"JP","FRA":"FR","SGP":"SG","ISR":"IL","DEU":"DE","GBR":"GB","BRA":"BR",
        "CAN":"CA","AUS":"AU","IDN":"ID","VNM":"VN"}
    roster = {}
    with open(os.path.join(ROOT, "docs", "nation-sources.csv")) as f:
        for row in csv.DictReader(f):
            iso3 = row["iso3"].strip()
            if not iso3:
                continue
            rec = {"country": row["country"].strip(), "iso3": iso3,
                   "region": row["region"].strip(), "url": row["official_source_url"].strip()}
            roster[iso3] = rec              # every row keyed by iso3
            iso2 = iso3_to_iso2.get(iso3)
            if iso2:
                roster[iso2] = rec           # pilot convenience alias
    return roster

# ---------------- chokepoint join ----------------
def chokepoint_for(iso3):
    reg = json.load(open(os.path.join(ROOT, "data", "chokepoint-registry.json")))
    iso3_to_name = {"USA":"USA","CHN":"China","TWN":"Taiwan","NLD":"Netherlands",
                    "KOR":"South Korea","JPN":"Japan","ISR":"Israel"}
    name = iso3_to_name.get(iso3)
    h = reg["holders"].get(name) if name else None
    if h:
        return {"value": h["nodes"], "detail": h["detail"], "source_url": h["source"], "source_tier": "industry"}
    return {"value": "none", "detail": None, "source_url": None, "source_tier": "n/a"}

def compute_registry_for(iso3):
    """Hand-curated capacity band joined at build (P5: not harvestable from snippets)."""
    reg = json.load(open(os.path.join(ROOT, "data", "compute-registry.json")))
    c = reg["capacity"].get(iso3)
    if c:
        return {"value": c["band"], "mw": c["mw"], "as_of": c["as_of"],
                "summary": c["note"], "source_url": c["source"], "source_tier": "aggregator"}
    return None

# ---------------- post-process (B5) ----------------
# a value that is clearly a machine/product, not a legal-entity champion
_NOT_A_CHAMPION = re.compile(r"supercomputer|cluster|platform|initiative|programme|program|framework|institute|project", re.I)

def postprocess_facts(facts, strategy_url, strat_status):
    """B5 fixes applied deterministically after extraction:
    - PDF-URL inheritance: a field with a value but null source_url, when the
      strategy PDF was readable, inherits strategy_url (tier=primary, marked
      inherited) — the claim genuinely came from the doc we fed the model.
    - national_champion type guard: a supercomputer/programme is not a company."""
    inherit_ok = (strat_status == "ok" and strategy_url)
    def _fix(m):
        if isinstance(m, dict) and m.get("value") not in (None, "", "unknown", "not-found", "not-stated", "none") \
           and not m.get("source_url") and inherit_ok:
            m["source_url"] = strategy_url
            m["source_tier"] = "primary"
            m["source_inherited"] = "strategy-doc"
    for k, v in facts.items():
        if k == "funding":
            for e in (v or []):
                _fix(e)
        elif isinstance(v, dict):
            _fix(v)
    ch = facts.get("national_champion")
    if isinstance(ch, dict) and isinstance(ch.get("value"), str) and _NOT_A_CHAMPION.search(ch["value"]):
        ch.setdefault("flag", []).append("not-a-legal-entity")

# ---------------- per-country harvest ----------------
def harvest_one(iso2, meta):
    country, iso3, url = meta["country"], meta["iso3"], meta["url"]
    strat_text, strat_status = fetch_strategy_text(iso3, url)
    news = serper(f"{country} national AI strategy champion military defense AI", num=8)
    # B4/B2: a dedicated funding hunt — targets the AI budget instrument itself
    # (finds e.g. IndiaAI Mission cabinet allocation) and, because DROP_DOMAINS is
    # applied in serper(), re-sources from legit press instead of leaving a banned
    # claim to be backfilled with noise.
    # Country-neutral budget-instrument words only (NO country-specific currency
    # like 'crore' — that would rig retrieval for one nation). "cabinet approved",
    # "appropriation", "budget allocation" are the generic signals of a real
    # AI budget instrument in any jurisdiction.
    funding_news = serper(f"{country} artificial intelligence national programme budget allocation cabinet approved appropriation billion", num=8)
    news = (news + [h for h in funding_news if h["link"] not in {n["link"] for n in news}])[:12]
    infra = serper_allowlisted(f"{country} data center capacity megawatts AI compute installed", INFRA_ALLOW, num=10)
    procure = serper_allowlisted(f"{country} government procurement AI tender WTO GPA localization offset", PROCURE_ALLOW, num=10)
    law = serper_allowlisted(f"{country} AI law regulation enforcement data protection algorithm rules", LAW_ALLOW, num=10)
    bundles = {
        "STRATEGY": (strat_text if strat_status == "ok" else f"[STRATEGY {strat_status}: {url}]"),
        "NEWS": news, "INFRA": infra, "PROCUREMENT": procure, "LAW": law,
    }
    # iso2 for display: the pilot alias if the caller passed one, else the iso3
    iso2_disp = iso2 if len(iso2) == 2 else iso3
    record = {"country": country, "iso3": iso3, "iso2": iso2_disp, "region": meta["region"],
              "strategy_url": url, "strategy_extraction": strat_status}
    facts, usage = gemini_extract(country, bundles)
    postprocess_facts(facts, url, strat_status)  # B5: PDF-URL inheritance + champion type
    record["facts"] = facts
    record["chokepoint_node"] = chokepoint_for(iso3)  # build-time join, NOT harvested
    # compute_band: prefer the hand-curated registry (P5 — not harvestable); keep
    # the model's harvested attempt under compute_band_harvested for transparency.
    reg_compute = compute_registry_for(iso3)
    if reg_compute:
        record.setdefault("_joined", {})["compute_band_harvested"] = facts.get("compute_band")
        facts["compute_band"] = reg_compute
    record["_provenance"] = {
        "strategy_snapshot": wayback(url) if url else "",
        "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "streams": {"news": len(news), "infra": len(infra), "procurement": len(procure), "law": len(law)},
        "tokens": {"in": usage.get("promptTokenCount"), "out": usage.get("candidatesTokenCount")},
    }
    return record

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--countries", default="US,CN,AE,SA,IN,KR,JP,FR,SG,IL")
    ap.add_argument("--out", default="data/nation-facts.json")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="Sweep every distinct country in nation-sources.csv (89-scale).")
    ap.add_argument("--reads", action="store_true",
                    help="POST-VALIDATION pass: (re)generate opportunity_read from the "
                         "already-validated facts in --out. Run AFTER validate_nation.py.")
    args = ap.parse_args()

    if args.reads:
        reads_pass(os.path.join(ROOT, args.out))
        return

    roster = load_roster()
    want = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    if args.limit:
        want = want[:args.limit]

    # --all sweeps every distinct country in the CSV (89-scale)
    if args.all:
        seen = set()
        want = []
        for k, m in roster.items():
            if m["iso3"] not in seen:
                seen.add(m["iso3"]); want.append(m["iso3"])

    out_path = os.path.join(ROOT, args.out)
    existing = {}  # keyed by canonical iso3
    if os.path.exists(out_path) and not args.force:
        try:
            for rec in json.load(open(out_path)).get("records", []):
                existing[rec["iso3"]] = rec
        except Exception:
            pass

    results = dict(existing)
    for i, key in enumerate(want):
        if key not in roster:
            print(f"  !! {key} not in roster/CSV — skipping"); continue
        meta = roster[key]
        iso3 = meta["iso3"]
        if iso3 in existing and not args.force:
            print(f"  skip {iso3} (already harvested)"); continue
        print(f"[{i+1}/{len(want)}] harvesting {meta['country']} ({iso3}) ...")
        if args.dry:
            st, stt = fetch_strategy_text(iso3, meta["url"])
            print(f"    strategy: {stt}, {len(st.split())} words")
            continue
        try:
            rec = harvest_one(key, meta)
            results[iso3] = rec
            u = rec["_provenance"]["tokens"]
            print(f"    ok — {u['in']} in / {u['out']} out; "
                  f"streams {rec['_provenance']['streams']}; strat={rec['strategy_extraction']}")
        except Exception as e:
            print(f"    ERROR {meta['country']}: {e}")
        time.sleep(6)  # stay under 10 RPM free tier

    if not args.dry:
        payload = {"_meta": {"spec": "nation-axis-spec-v3", "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                   "records": [results[k] for k in results]}
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        json.dump(payload, open(out_path, "w"), indent=2, ensure_ascii=False)
        print(f"\nwrote {len(results)} records -> {args.out}")

if __name__ == "__main__":
    main()
