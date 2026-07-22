#!/usr/bin/env python3
"""
Append the 23 Wave-1/Wave-2 country files to the canonical register.csv WITHOUT
full-rebuilding from .md (the original 14 .md files were never drift-fixed; only
register.csv holds the fixed data). Anchor-parse each new file on the existence
token to avoid the column-drift class of bug. Idempotent-ish: skips CCs already
present in register.csv so re-runs don't double-append.

    python3 scripts/append_new_countries.py
"""
import csv, re, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG_CSV = os.path.join(ROOT, "data", "register.csv")
FND_CSV = os.path.join(ROOT, "data", "findings.csv")
NEW_CCS = ["TW","NL","CA","AU","SA","SG","IL","SE","DK","AE","HK","ZA",
           "MX","IE","BE","NO","FI","PL","TR","ID","AT","VN","PT"]
EXIST_TOK = ("CONFIRMED","CLAIMED","SMOKE","DIRECTIONAL","NONE","UNKNOWN")

def cells(line):
    p = [x.strip() for x in line.split("|")]
    while p and p[0] == "": p.pop(0)
    while p and p[-1] == "": p.pop()
    return p

def looks_date(x):
    return bool(re.fullmatch(r"(19|20)\d{2}(-\d{1,2})?", (x or "").strip())) or (x or "").strip().lower()=="missing"

# load existing canonical rows
with open(REG_CSV) as f:
    r = csv.reader(f); hdr = next(r); existing = list(r)
have_ccs = {row[1] for row in existing if len(row) > 1}
print(f"existing register.csv: {len(existing)} rows, {len(have_ccs)} countries")

added = 0
per_cc = {}
for cc in NEW_CCS:
    if cc in have_ccs:
        print(f"  {cc}: already in register.csv — skipping (no double-append)")
        continue
    fpath = os.path.join(ROOT, "data", "register", f"register_{cc}.md")
    if not os.path.exists(fpath):
        print(f"  {cc}: FILE MISSING — skip"); continue
    n0 = added
    for line in open(fpath):
        line = line.rstrip("\n")
        if "|" not in line: continue
        c = cells(line)
        if len(c) < 6 or c[0].lower() == "company": continue
        # anchor on existence token
        ei = next((i for i,x in enumerate(c) if x.split()[:1] and x.split()[0].upper() in EXIST_TOK), None)
        if ei is None:
            continue  # no existence token -> not a real data row (e.g. separator)
        company = c[0]
        url = next((x for x in c if x.startswith("http")), "")
        left = [x for x in c[1:ei] if x.upper() != cc]     # drop stray country cell
        vert, raw, horz, use = (left + [""]*4)[:4]
        existence = c[ei].split()[0].upper()
        after = c[ei+1:]
        value = after[0] if len(after) > 0 else ""
        tier = next((x for x in after if x.strip().upper() in ("P","I","S","-","—")), "")
        date = next((x for x in after if x != url and looks_date(x)), "")
        # keep only rows with a real deployment OR an explicit existence verdict + url
        row = [company, cc, vert, raw, horz, use, existence, value, tier, url, date]
        existing.append(row); added += 1
    per_cc[cc] = added - n0
    print(f"  {cc}: +{per_cc[cc]} rows")

with open(REG_CSV, "w", newline="") as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(existing)

print(f"\nAPPENDED {added} rows across {len(per_cc)} countries.")
print(f"register.csv now: {len(existing)} rows.")

# findings: append new-country findings too (5-col: cc,vertical,finding,url,why)
fnd_rows = []
if os.path.exists(FND_CSV):
    with open(FND_CSV) as f:
        fr = csv.reader(f); fhdr = next(fr); fnd_rows = list(fr)
    fhave = {row[0] for row in fnd_rows if row}
else:
    fhdr = ["country","vertical","finding","source_url","why_it_matters"]; fhave = set()
fadded = 0
for cc in NEW_CCS:
    if cc in fhave: continue
    fpath = os.path.join(ROOT, "data", "findings", f"findings_{cc}.md")
    if not os.path.exists(fpath): continue
    for line in open(fpath):
        line = line.rstrip("\n")
        if "|" not in line: continue
        c = cells(line)
        if len(c) < 2 or c[0].lower() in ("vertical","country","finding"): continue
        if set("".join(c[:1])) <= set("-: "): continue
        fnd_rows.append(([cc] + c + [""]*5)[:5]); fadded += 1
with open(FND_CSV, "w", newline="") as f:
    w = csv.writer(f); w.writerow(fhdr); w.writerows(fnd_rows)
print(f"findings.csv: +{fadded} rows, now {len(fnd_rows)} total.")
