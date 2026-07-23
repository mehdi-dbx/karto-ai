#!/usr/bin/env python3
"""V3 Step 12 (workload 3) — freshness re-verification queue = the ongoing heartbeat engine.

Doctrine (build-plan-updated-2): freshness is a FLOW, not a one-shot. A priority queue,
oldest last_verified first, weighted by row visibility (value-number rows + high-traffic
entities first), a fixed budget per run (~100 rows), cycles forever. Delta queries only
("what's new SINCE {last_verified}"), never re-derive from zero.

This script PLANS the next batch (it does not itself call the web — an agent consumes the
plan and proposes a gated diff, exactly like the resweep). Output: staging/freshness_queue.json
— the ranked next-N rows to re-verify, with the delta query to run for each.

    python3 scripts/freshness_queue.py [--budget 100]

Note: the register was (re)built this session, so all rows are currently FRESH — running the
verification agent now would be wasteful (nothing to update). The queue is built and ready;
it starts yielding real work once rows age past the freshness threshold on future builds.
"""
import csv, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
OUT  = os.path.join(ROOT, "staging", "freshness_queue.json")
NOW_YEAR = 2026
BUDGET = 100
if "--budget" in sys.argv:
    try: BUDGET = int(sys.argv[sys.argv.index("--budget")+1])
    except: pass

def year_of(d):
    m = re.match(r"(19|20)\d{2}", (d or "").strip()); return int(m.group(0)) if m else None
def has_num(v): return bool(re.search(r"\d", v or "")) and (v or "").strip().lower() not in ("none","n/a","")

rows = list(csv.reader(open(REG)))[1:]
scored = []
for i, r in enumerate(rows):
    y = year_of(r[10])
    age = (NOW_YEAR - y) if y else 3      # undated treated as moderately stale
    # priority = age + visibility weight (value-number rows and confirmed rows surface first)
    vis = (2 if has_num(r[7]) else 0) + (1 if (r[6] or "").upper().startswith("CONFIRMED") else 0)
    score = age * 2 + vis
    scored.append((score, i, r[0], r[1], r[10]))
scored.sort(reverse=True)
batch = scored[:BUDGET]

queue = {
    "budget": BUDGET,
    "anchor_year": NOW_YEAR,
    "note": "priority = staleness*2 + visibility(value-number/confirmed). Delta-query each: 'what is new about {company} AI SINCE {last_verified}'. Agent proposes gated diffs to register (last_verified bumps / corrections / SMOKE demotions) — never re-derives from zero.",
    "batch": [{"row_id": i, "company": co, "cc": cc, "last_verified": lv or "missing",
               "delta_query": f"{co} AI news since {lv or '2024'}"} for _, i, co, cc, lv in batch],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(queue, open(OUT, "w"), ensure_ascii=False, indent=1)
fresh = sum(1 for s,_,_,_,_ in scored if s <= 2*1)   # age<=0..1, low priority
print(f"freshness queue -> {OUT}: {len(batch)} rows planned (budget {BUDGET}).")
print(f"  register age profile: newest data is this session, so most rows are fresh; queue yields")
print(f"  real re-verification work as rows age on future builds (the heartbeat cadence).")
