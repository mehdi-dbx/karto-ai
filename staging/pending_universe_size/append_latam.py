#!/usr/bin/env python3
"""Append a batch of enriched rows to rows_LATAM_ROW.csv.
argv[1] = path to JSON list. Each item:
  {company, cc, mc_local, rev_local, emp, ticker, rate}
mc_local / rev_local = raw numbers in LOCAL currency (or USD if rate==1),
or null to leave empty. rate = local units per USD.
"""
import csv, json, os, sys

OUT = "/Users/mehdi.lamrani/code/code/karto/staging/pending_universe_size/parts/rows_LATAM_ROW.csv"
HEADER = ["company", "cc", "market_cap_usd", "revenue_usd", "employees", "ticker"]

def conv(v, rate):
    if v is None or v == "":
        return ""
    return str(int(round(float(v) / float(rate))))

def main():
    with open(sys.argv[1]) as f:
        rows = json.load(f)
    exists = os.path.exists(OUT)
    with open(OUT, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(HEADER)
        for r in rows:
            rate = r.get("rate", 1)
            mc = conv(r.get("mc_local"), r.get("mc_rate", rate))
            rev = conv(r.get("rev_local"), r.get("rev_rate", rate))
            emp = r.get("emp")
            emp = "" if emp in (None, "") else str(int(emp))
            tk = r.get("ticker") or ""
            w.writerow([r["company"], r["cc"], mc, rev, emp, tk])
    with open(OUT) as f:
        n = sum(1 for _ in f) - 1
    print(f"Appended {len(rows)} rows. File now has {n} data rows.")

if __name__ == "__main__":
    main()
