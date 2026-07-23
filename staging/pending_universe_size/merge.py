#!/usr/bin/env python3
"""Merge regional fragment CSVs into the final rows.csv for the gate.
Validates (company,cc) keys against data/universe.csv and reports mismatches.
Idempotent: safe to re-run as fragments grow."""
import csv, os, glob, sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
UNIVERSE = os.path.join(REPO, "data", "universe.csv")
PARTS = os.path.join(BASE, "parts")
OUT = os.path.join(BASE, "rows.csv")
COLS = ["company", "cc", "market_cap_usd", "revenue_usd", "employees", "ticker"]

# valid keys from universe
valid = set()
with open(UNIVERSE) as f:
    for r in csv.DictReader(f):
        valid.add((r["company"], r["cc"]))

merged = {}          # (company,cc) -> row dict
unmatched = []       # rows whose keys don't join universe
dupes = 0
for frag in sorted(glob.glob(os.path.join(PARTS, "rows_*.csv"))):
    with open(frag) as f:
        for r in csv.DictReader(f):
            key = (r.get("company", ""), r.get("cc", ""))
            # keep only a row that carries at least one size field
            has = any((r.get(c) or "").strip() for c in COLS[2:])
            if not has:
                continue
            if key not in valid:
                unmatched.append((frag, key))
                continue
            if key in merged:
                dupes += 1
            merged[key] = {c: (r.get(c) or "").strip() for c in COLS}

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    for key in sorted(merged):
        w.writerow(merged[key])

# stats
def filled(col):
    return sum(1 for row in merged.values() if row[col])
print(f"merged rows: {len(merged)}")
for c in COLS[2:]:
    print(f"  {c}: {filled(c)}")
print(f"duplicate keys collapsed: {dupes}")
print(f"unmatched (dropped, key not in universe): {len(unmatched)}")
for frag, key in unmatched[:50]:
    print(f"    {os.path.basename(frag)}: {key}")
