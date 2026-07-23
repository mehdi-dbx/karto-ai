#!/usr/bin/env python3
"""
V2 Module A1 — consolidate the 35 per-country universe_*.tsv files into one
data/universe.csv (the searched population). NO size data yet (owner deferred the
resweep) — market_cap/revenue/employees columns are present but blank, to be
enriched later without a schema change.

Also emits data/orphans.txt: register companies that DON'T join to the universe
(spelling variants — the expected failure mode; build an alias map over time).

    python3 scripts/build_universe.py
"""
import csv, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "universe.csv")
ORPH = os.path.join(ROOT, "data", "orphans.txt")
REG  = os.path.join(ROOT, "data", "register.csv")

HDR = ["company","cc","vertical","index","raw_sector","market_cap_usd","revenue_usd","employees","ticker"]

rows, seen = [], set()
for f in sorted(glob.glob(os.path.join(ROOT,"data","universe","universe_*.tsv"))):
    cc = os.path.basename(f).split("_")[1].split(".")[0].upper()
    for line in open(f):
        p = [x.strip() for x in line.rstrip("\n").split("\t")]
        if len(p) < 2 or not p[0]: continue
        company = p[0]
        idx  = p[2] if len(p) > 2 else ""
        sect = p[3] if len(p) > 3 else ""
        key = (company.lower(), cc)
        if key in seen: continue
        seen.add(key)
        # vertical is unknown at universe stage (comes from register/classification);
        # left blank here, joined downstream in cook. size cols blank (deferred).
        rows.append([company, cc, "", idx, sect, "", "", "", ""])

with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(HDR); w.writerows(rows)

# orphan report: register (company,cc) not present in universe
reg = list(csv.reader(open(REG)))[1:]
regco = {(r[0].strip().lower(), r[1].strip().upper()) for r in reg}
orphans = sorted(regco - seen)
with open(ORPH, "w") as fh:
    fh.write(f"# {len(orphans)} register companies not joining universe (spelling variants -> build alias map)\n")
    for name, cc in orphans:
        fh.write(f"{cc}\t{name}\n")

print(f"universe.csv: {len(rows)} companies, {len({r[1] for r in rows})} countries -> {OUT}")
print(f"orphans (register not in universe): {len(orphans)} -> {ORPH}")
print(f"join coverage: {round(100*(len(regco)-len(orphans))/len(regco))}%")
