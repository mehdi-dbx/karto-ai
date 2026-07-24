#!/usr/bin/env python3
"""Depth-resweep planner. The register is breadth-first/depth-never: 76% of
companies have exactly 1 deployment, ceiling 6 — a systematic false-negative floor,
not reality. This ranks companies by expected gap (big + AI-active + suspiciously
few rows) and emits a structured query batch per company for the depth sweep.

Query expansion is the lever: one "{company} AI" query became ~1 deployment. Here
each company gets function × recency × primary-source queries so agents can go deep.

    python3 scripts/resweep_plan.py [--top N]   # default 40
Output: staging/resweep_queue.json
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
UNI  = os.path.join(ROOT, "data", "universe.csv")
OUT  = os.path.join(ROOT, "staging", "resweep_queue.json")

TOP = 40
if "--top" in sys.argv:
    try: TOP = int(sys.argv[sys.argv.index("--top")+1])
    except: pass
if "--all" in sys.argv:
    TOP = 10**9
# skip companies already swept (pass a JSON list-of-[company,cc] file)
DONE = set()
if "--exclude" in sys.argv:
    import json as _j
    p = sys.argv[sys.argv.index("--exclude")+1]
    try:
        for c in _j.load(open(p)).get("companies", []):
            DONE.add((c["company"], c["cc"]))
    except Exception as e:
        print("exclude load failed:", e)

FUNCTIONS = ["Core / Domain", "Customer Support", "Software / Code",
             "Sales / Marketing", "Back-office / Ops", "Security / Risk"]
# search phrasing per function (what to actually query)
FN_QUERY = {
    "Core / Domain":      "AI in core operations / product",
    "Customer Support":   "AI customer service chatbot",
    "Software / Code":    "AI software development / coding copilot",
    "Sales / Marketing":  "AI sales marketing personalization",
    "Back-office / Ops":  "AI back-office automation / finance / HR",
    "Security / Risk":    "AI fraud / risk / security",
}

reg = list(csv.reader(open(REG)))[1:]
rows_by_co = defaultdict(list)
for r in reg:
    rows_by_co[(r[0], r[1])].append(r)

# functions already covered per company (so agents target the GAPS)
covered_fn = defaultdict(set)
for r in reg:
    covered_fn[(r[0], r[1])].add(r[4])

uni = {(u["company"], u["cc"]): u for u in csv.DictReader(open(UNI))}

def num(x):
    try: return float(x)
    except: return 0.0

# AI-intensity proxy: verticals known to be AI-heavy weight higher
HOT_VERTS = {"Financial Services", "Technology", "Insurance", "Telecom",
             "Healthcare & Life Sciences", "Retail & E-commerce", "Media / Entertainment / Gaming"}

scored = []
for (co, cc), rr in rows_by_co.items():
    n = len(rr)
    vertical = rr[0][2]
    u = uni.get((co, cc), {})
    mcap = num(u.get("market_cap_usd"))
    rev  = num(u.get("revenue_usd"))
    size = max(mcap, rev*3)                      # revenue scaled to compare w/ mcap
    # expected-gap score: bigger + AI-hot vertical + currently few rows = higher priority
    size_w = min(size/50e9, 4)                   # cap so a few giants don't dominate
    hot_w  = 2 if vertical in HOT_VERTS else 1
    gap_w  = (6 - min(n, 6)) / 5                  # 1 row -> 1.0, 6 rows -> 0.0
    score = (size_w + 1) * hot_w * (0.4 + gap_w)
    missing = [f for f in FUNCTIONS if f not in covered_fn[(co, cc)]]
    scored.append({
        "company": co, "cc": cc, "vertical": vertical,
        "current_rows": n, "market_cap_usd": mcap, "revenue_usd": rev,
        "score": round(score, 2),
        "missing_functions": missing,
        "queries": (
            [f"{co} AI {FN_QUERY[f]}" for f in missing] +
            [f"{co} artificial intelligence 2025", f"{co} AI deployment case study",
             f"{co} annual report AI initiatives"]
        ),
    })

scored = [c for c in scored if (c["company"], c["cc"]) not in DONE]
scored.sort(key=lambda x: -x["score"])
batch = scored[:TOP]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({
    "target": "≥8 distinct, source-backed AI deployments per company (or list what was tried and why fewer exist)",
    "method": "query expansion: one query per uncovered function + recency + primary sources (10-K, earnings, newsroom). Dedup vs existing rows. Every row: existence=confirmed|claimed, a real source_url, and (company,country,use_case) unique.",
    "count": len(batch),
    "companies": batch,
}, open(OUT, "w"), ensure_ascii=False, indent=1)

print(f"resweep queue -> {OUT}: {len(batch)} companies (of {len(scored)} scored).")
print(f"{'company':32} {'cc':3} {'rows':4} {'score':6} missing_fns")
for c in batch[:TOP]:
    print(f"{c['company'][:31]:32} {c['cc']:3} {c['current_rows']:<4} {c['score']:<6} {len(c['missing_functions'])}")
