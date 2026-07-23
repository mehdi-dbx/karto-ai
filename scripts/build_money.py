#!/usr/bin/env python3
"""V3 Step 2 — unify money signals into ONE table (data/money.csv).

One row per MONEY EVENT (not per deployment — different grain than the register,
which is why it is its own table). Two origins feed it:
  - register_extraction : mined from register free-text by extract_claims.py (claims.csv)
  - dedicated_collection: purpose-collected commitment events (Step 12 FS pilot; writes here)

Schema (14 cols, per karto-v3-build-plan-reviewed.md Step 2):
  id, company, cc, amount, currency, unit, kind, origin, horizon, tier,
  source_url, source_phrase, register_row_id, date

kind vocabulary:
  savings_claim | revenue_claim | investment | acquisition | partnership |
  users_claim | vague

claims.csv claim_type -> kind:
  savings->savings_claim  revenue->revenue_claim  investment->investment
  scale->users_claim      metric_pct->vague       vague->vague   (unknown)->vague

Idempotent. claims.csv is the legacy feeder (retired; kept one release with a note).
Dedicated commitments land directly in money.csv with origin=dedicated_collection
and are preserved across rebuilds (no separate commitments.csv stub — deleted per plan).
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import Counter

DATA = Path(__file__).resolve().parent.parent / "data"
CLAIMS = DATA / "claims.csv"
MONEY  = DATA / "money.csv"

FIELDS = ["id","company","cc","amount","currency","unit","kind","origin","horizon",
          "tier","source_url","source_phrase","register_row_id","date"]

CLAIM_KIND = {
    "savings":"savings_claim", "revenue":"revenue_claim", "investment":"investment",
    "scale":"users_claim", "metric_pct":"vague", "vague":"vague",
}

def build():
    rows, n = [], 0
    # 1) register_extraction rows from claims.csv
    #    (row_id,company,cc,amount,currency,unit,claim_type,source_phrase)
    if CLAIMS.exists():
        for c in list(csv.reader(open(CLAIMS)))[1:]:
            if len(c) < 8:
                continue
            row_id, company, cc, amount, currency, unit, claim_type, phrase = c[:8]
            n += 1
            rows.append({
                "id": f"m{n:05d}", "company": company, "cc": cc,
                "amount": amount, "currency": currency, "unit": unit,
                "kind": CLAIM_KIND.get(claim_type.strip(), "vague"),
                "origin": "register_extraction", "horizon": "",
                "tier": "", "source_url": "", "source_phrase": phrase,
                "register_row_id": row_id, "date": "",
            })
    # 2) preserve any dedicated_collection rows already in money.csv (gate-written; Step 12)
    if MONEY.exists():
        for r in csv.DictReader(open(MONEY)):
            if r.get("origin") == "dedicated_collection":
                rows.append({k: r.get(k, "") for k in FIELDS})

    with open(MONEY, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

    print(f"money.csv: {len(rows)} rows -> {MONEY}")
    print("  by origin:", dict(Counter(r['origin'] for r in rows)))
    print("  by kind:", dict(Counter(r['kind'] for r in rows)))

if __name__ == "__main__":
    build()
