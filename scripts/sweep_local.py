#!/usr/bin/env python3
"""sweep_local.py — economical AI-deployment sweep, run locally.

Replaces the per-company subagent (which paid full harness overhead + dumped whole
pages into an Opus/Sonnet context) with three cheap steps:

  1. SEARCH   — Serper API (paid HTTP, ~$0.001/query, ZERO model tokens)
  2. FETCH+TRIM — urllib + local HTML strip; only ~1.5k chars/page reach the model
  3. EXTRACT  — ONE Haiku call per company over the bundled, pre-trimmed snippets
                (no agent harness, no second LLM verify pass — a programmatic
                URL-filter downstream does the cheap verify, same as the grinds)

Auth: the model call goes through the Databricks AI gateway named by
$ANTHROPIC_BASE_URL, using a bearer token minted from the matching CLI profile
(default: ai_devtools). Search key: ~/.config/karto/serper_key (already present).

Output shape matches scripts/resweep_to_staging.py exactly:
  {"companies": [{"company","cc","vertical","rows":[{use_case,horizontal,
                  existence,value_claimed,vendor,source_url,date}...]}, ...]}

Usage:
  python3 scripts/sweep_local.py --queue staging/resweep_queue.json \
      --exclude staging/resweep_result_grindall.json \
      --limit 10 --out staging/sweep_local_calib.json
  # --limit 10 = calibration run; prints token + $ estimate at the end.
  # drop --limit (or set 0) to sweep the whole remaining queue.

Nothing here is fabricated: a deployment with no real http(s) source_url is
dropped by resweep_to_staging.py, and the model is instructed to omit any row it
cannot tie to one of the supplied search-result URLs.
"""
import argparse, json, os, re, subprocess, sys, urllib.request, urllib.error, html, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FUNCTIONS = ["Core / Domain", "Customer Support", "Software / Code",
             "Sales / Marketing", "Back-office / Ops", "Security / Risk"]

# ---- Serper search (same backend as ~/.claude/tools/apisearch.py) -----------
def _serper_key():
    k = os.environ.get("SERPER_API_KEY", "").strip()
    if k:
        return k
    p = os.path.expanduser("~/.config/karto/serper_key")
    if os.path.exists(p):
        return open(p).read().strip()
    sys.exit("sweep_local: no Serper key ($SERPER_API_KEY or ~/.config/karto/serper_key).")

def serper(query, num=8):
    body = json.dumps({"q": query, "num": num}).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search", data=body,
        headers={"X-API-KEY": _serper_key(), "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []
    out = []
    for h in (data.get("organic") or [])[:num]:
        out.append({"title": (h.get("title") or "").strip(),
                    "link":  (h.get("link") or "").strip(),
                    "snippet": (h.get("snippet") or "").strip(),
                    "date": h.get("date", "")})
    return out

# ---- local fetch + trim (no model tokens) -----------------------------------
_TAG = re.compile(r"<[^>]+>")
_WS  = re.compile(r"\s+")
def fetch_trim(url, cap=1500):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 karto-sweep"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(400_000).decode("utf-8", "ignore")
    except Exception:
        return ""
    # crude readability: drop script/style, strip tags, collapse ws
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    txt = html.unescape(_TAG.sub(" ", raw))
    txt = _WS.sub(" ", txt).strip()
    return txt[:cap]

# ---- gateway model call (Databricks AI gateway -> Anthropic messages) --------
_TOKEN = None
def _bearer(profile):
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    out = subprocess.run(["databricks", "auth", "token", "-p", profile],
                         capture_output=True, text=True)
    try:
        _TOKEN = json.loads(out.stdout)["access_token"]
    except Exception:
        sys.exit(f"sweep_local: could not mint token via profile '{profile}': {out.stderr[:200]}")
    return _TOKEN

def _custom_headers():
    # header lines are NEWLINE-separated; a value may itself be a JSON map
    # (e.g. Databricks-Ai-Gateway-Request-Tags: {"source":"x","org":"y"}), so
    # never split on commas — split each line on the FIRST colon only.
    hdrs = {}
    raw = os.environ.get("ANTHROPIC_CUSTOM_HEADERS", "")
    for line in raw.split("\n"):
        line = line.strip()
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip().strip('"'); v = v.strip()
        if k:
            hdrs[k] = v
    return hdrs

# usage counters shared across worker threads -> guard with a lock
_usage = {"in": 0, "out": 0, "calls": 0}
_usage_lock = threading.Lock()

def haiku_extract(company, cc, vertical, results, profile, model):
    base = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")
    url = base + "/v1/messages"
    bundle = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['link']}\nDATE: {r.get('date','')}\n{r['snippet']} {r.get('_body','')}"
        for i, r in enumerate(results))
    prompt = f"""You extract REAL, publicly-documented AI deployments for one company from search results.

COMPANY: {company} ({cc}, {vertical})

From the numbered search results below, list each DISTINCT AI deployment. Rules:
- Only include a deployment if it maps to one of the URLs below (copy that exact URL into source_url). If you cannot tie it to a supplied URL, OMIT it. Never invent a URL or a figure.
- existence="confirmed" only if the source shows it is actually deployed/in production; otherwise "claimed".
- value_claimed only if a real number is disclosed, else "none".
- horizontal must be one of: {", ".join(FUNCTIONS)}.
- vendor = named AI vendor/model/stack if stated, else "".
- Do not split one initiative into many rows.

Return ONLY a JSON object: {{"rows":[{{"use_case","horizontal","existence","value_claimed","vendor","source_url","date"}}]}}. No prose.

SEARCH RESULTS:
{bundle}"""
    body = json.dumps({
        "model": model,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    headers = {"Authorization": "Bearer " + _bearer(profile),
               "Content-Type": "application/json",
               "anthropic-version": "2023-06-01"}
    headers.update(_custom_headers())
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        sys.exit(f"sweep_local: gateway HTTP {e.code} — {detail}")
    except Exception as e:
        print(f"  ! {company}: model call failed — {e}", file=sys.stderr)
        return []
    u = resp.get("usage", {})
    with _usage_lock:
        _usage["in"] += u.get("input_tokens", 0)
        _usage["out"] += u.get("output_tokens", 0)
        _usage["calls"] += 1
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return []
    try:
        return (json.loads(m.group(0)).get("rows") or [])
    except Exception:
        return []

# ---- queries per company ----------------------------------------------------
def queries_for(company):
    c = company
    return [
        f"{c} AI deployment 2025",
        f"{c} generative AI use case",
        f"{c} AI customer service OR fraud OR supply chain",
        f'"{c}" (Copilot OR "Azure OpenAI" OR Claude OR Gemini OR Bedrock OR Databricks)',
        f"{c} annual report AI initiatives",
    ]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", default=os.path.join(ROOT, "staging", "resweep_queue.json"))
    ap.add_argument("--exclude", default="", help="a grindall-shape JSON; its companies are skipped")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--profile", default="ai_devtools")
    ap.add_argument("--model", default=os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", "system.ai.claude-haiku-4-5"))
    ap.add_argument("--fetch", type=int, default=2, help="how many top URLs to fetch+trim per company (0=snippets only)")
    ap.add_argument("--workers", type=int, default=10, help="concurrent companies in flight")
    ap.add_argument("--out", default=os.path.join(ROOT, "staging", "sweep_local_out.json"))
    args = ap.parse_args()

    q = json.load(open(args.queue))
    items = q if isinstance(q, list) else q.get("companies", q.get("queue", []))

    done = set()
    if args.exclude and os.path.exists(args.exclude):
        ex = json.load(open(args.exclude))
        for c in ex.get("companies", []):
            done.add((c.get("company", "").strip(), c.get("cc", "").strip()))

    todo = [it for it in items
            if (it.get("company", "").strip(), it.get("cc", "").strip()) not in done]
    if args.limit and args.limit > 0:
        todo = todo[:args.limit]

    print(f"sweep_local: {len(todo)} companies to sweep "
          f"(queue {len(items)}, excluded {len(done)}), model={args.model}, "
          f"fetch={args.fetch}/co, workers={args.workers}")

    _bearer(args.profile)  # mint once up front so worker threads don't race on the CLI

    def sweep_one(it):
        company = it.get("company", "").strip(); cc = it.get("cc", "").strip()
        vertical = it.get("vertical", "").strip()
        results = []
        seen = set()
        for query in queries_for(company):
            for r in serper(query, num=6):
                if r["link"] and r["link"] not in seen:
                    seen.add(r["link"]); results.append(r)
        results = results[:12]
        for r in results[:args.fetch]:
            b = fetch_trim(r["link"])
            if b:
                r["_body"] = b
        rows = haiku_extract(company, cc, vertical, results, args.profile, args.model) if results else []
        return {"company": company, "cc": cc, "vertical": vertical, "rows": rows}

    out_companies = []
    done_n = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(sweep_one, it): it for it in todo}
        for fut in as_completed(futs):
            done_n += 1
            try:
                res = fut.result()
            except Exception as e:
                it = futs[fut]
                res = {"company": it.get("company", ""), "cc": it.get("cc", ""),
                       "vertical": it.get("vertical", ""), "rows": []}
                print(f"  ! {res['company']}: {str(e)[:120]}", file=sys.stderr)
            out_companies.append(res)
            print(f"  [{done_n}/{len(todo)}] {res['company']} ({res['cc']}): "
                  f"{len(res['rows'])} rows  [tok in/out {_usage['in']}/{_usage['out']}]")

    json.dump({"companies": out_companies}, open(args.out, "w"), indent=1)
    nrows = sum(len(c["rows"]) for c in out_companies)
    print(f"\nwrote {args.out}: {len(out_companies)} companies, {nrows} rows")
    # Haiku 4.5 list price ~$1/Mtok in, ~$5/Mtok out (adjust if your gateway differs)
    est = _usage["in"]/1e6*1.0 + _usage["out"]/1e6*5.0
    n = max(1, len(out_companies))
    print(f"model usage: {_usage['calls']} calls, {_usage['in']} in + {_usage['out']} out tokens")
    print(f"est cost: ${est:.4f} total  ~= ${est/n:.4f}/company  "
          f"(x1663 remaining -> ~${est/n*1663:.2f})")

if __name__ == "__main__":
    main()
