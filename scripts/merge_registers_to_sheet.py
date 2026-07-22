#!/usr/bin/env python3
"""
KARTO merge — two explicit phases:

  PHASE 1 (build_local):  consolidate + dedup all data/register + data/findings
                          → write CANONICAL snapshots into the repo:
                              data/register.csv   data/findings.csv
                          This is the SOURCE OF TRUTH. Committed to git.

  PHASE 2 (publish_sheet): push those CSVs to the Google Sheet (Register/Findings tabs).
                          MANDATORY but a SEPARATE step — the Sheet is a publish target,
                          not where the data lives.

Concurrency model (preserved): sweep AGENTS each write their own
data/register/register_<CC>.md (per-country, no write contention). THIS script is the
single writer that consolidates + publishes. Never have agents write the CSV or the Sheet.

Usage:
  python3 scripts/merge_registers_to_sheet.py            # phase 1 + phase 2 (default)
  python3 scripts/merge_registers_to_sheet.py --local    # phase 1 only (rebuild repo CSVs)
  python3 scripts/merge_registers_to_sheet.py --publish  # phase 2 only (CSV -> Sheet)
"""
import json, subprocess, urllib.request, glob, csv, sys, os
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _config import load as _load
_CFG = _load()


QUOTA = _CFG["KARTO_QUOTA_PROJECT"]
AUTH = _os.path.expanduser("~/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py")
SID = _CFG["KARTO_SHEET_ID"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG_CSV = os.path.join(ROOT, "data", "register.csv")
FND_CSV = os.path.join(ROOT, "data", "findings.csv")
REG_HDR = ["company","country","vertical","raw_sector","horizontal","use_case","existence","value_claimed","tier","source_url","date"]
FND_HDR = ["country","vertical","finding","source_url","why_it_matters"]
EXIST_TOK = ("CONFIRMED","CLAIMED","SMOKE","DIRECTIONAL","NONE","UNKNOWN")

def cells(line):
    p = [x.strip() for x in line.split("|")]
    while p and p[0] == "": p.pop(0)
    while p and p[-1] == "": p.pop()
    return p

def _looks_date(x):
    import re
    return bool(re.fullmatch(r"(19|20)\d{2}(-\d{1,2})?", (x or "").strip()))

# ---------------- PHASE 1: build canonical local CSVs ----------------
def build_local():
    reg, seen = [], set()
    for f in sorted(glob.glob(os.path.join(ROOT,"data","register","register_*.md"))):
        cc = os.path.basename(f).split("_")[1].split(".")[0].upper()  # country from filename (authoritative)
        for line in open(f):
            line = line.rstrip("\n")
            if "|" not in line or "http" not in line: continue
            c = cells(line)
            if len(c) < 9 or c[0].lower() == "company" or set("".join(c[:1])) <= set("-: "): continue
            # ANCHOR-PARSE on the existence token (fixes the column-drift class of bugs):
            # locate the cell whose leading word is an existence token; columns pivot around it.
            ei = next((i for i,x in enumerate(c) if x.split()[:1] and x.split()[0].upper() in EXIST_TOK), None)
            company = c[0]
            url = next((x for x in c if x.startswith("http")), "")
            if ei is not None:
                # left of existence: company, [country?], vertical, raw_sector, horizontal, use_case
                left = [x for x in c[1:ei] if x.upper()!=cc]            # drop a stray country cell
                # pad/truncate the 4 descriptive cols (vertical, raw_sector, horizontal, use_case)
                vert, raw, horz, use = (left + [""]*4)[:4]
                existence = c[ei].split()[0].upper()
                after = c[ei+1:]
                value = after[0] if len(after)>0 else ""
                tier  = next((x for x in after if x.strip().upper() in ("P","I","S","-","—")), "")
                # date = a cell that looks like a year / YYYY-MM (or literal 'missing'), not the url
                date = next((x for x in after if x!=url and (x.lower()=="missing" or _looks_date(x))), "")
                row = [company, cc, vert, raw, horz, use, existence, value, tier, url, date]
            else:
                # no existence token found — legacy fallback (keep, but flag by leaving existence blank)
                mid = [x for x in c[1:] if x != url and x.upper()!=cc][:6]
                row = ([company, cc] + mid + [""]*9)[:9] + [url, ""]
            key = (company.lower(), (row[5] or "")[:50].lower(), url.lower())
            if key in seen: continue
            seen.add(key); reg.append(row)
    fnd, fseen = [], set()
    for f in sorted(glob.glob(os.path.join(ROOT,"data","findings","findings_*.md"))):
        cc = os.path.basename(f).split("_")[1].split(".")[0].upper()
        for line in open(f):
            line = line.rstrip("\n")
            if "|" not in line or "http" not in line: continue
            c = cells(line)
            if len(c) < 2 or c[0].lower() in ("vertical","country","finding") or set("".join(c[:1])) <= set("-: "): continue
            key = (cc, c[0][:80].lower())
            if key in fseen: continue
            fseen.add(key); fnd.append(([cc] + c[:5] + [""]*5)[:5])
    with open(REG_CSV,"w",newline="") as fh:
        w = csv.writer(fh); w.writerow(REG_HDR); w.writerows(reg)
    with open(FND_CSV,"w",newline="") as fh:
        w = csv.writer(fh); w.writerow(FND_HDR); w.writerows(fnd)
    from collections import Counter
    print(f"PHASE 1 (local): {len(reg)} register rows -> {REG_CSV}")
    print(f"                 {len(fnd)} findings rows -> {FND_CSV}")
    print(f"                 by country: {dict(Counter(r[1] for r in reg))}")
    return reg, fnd

# ---------------- PHASE 2: publish CSVs -> Google Sheet ----------------
def _api(url, method="GET", body=None, tok=None):
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=d, method=method,
        headers={"Authorization": f"Bearer {tok}", "x-goog-user-project": QUOTA, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))

def publish_sheet():
    if not (os.path.exists(REG_CSV) and os.path.exists(FND_CSV)):
        print("ERROR: run PHASE 1 first (data/register.csv missing)."); sys.exit(1)
    tok = subprocess.run(["python3", AUTH, "token"], capture_output=True, text=True).stdout.strip()
    reg = list(csv.reader(open(REG_CSV)))       # includes header
    fnd = list(csv.reader(open(FND_CSV)))
    base = f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values"
    _api(f"{base}/Register!A1:K6000:clear", "POST", {}, tok)
    _api(f"{base}/Register!A1?valueInputOption=RAW", "PUT", {"range":"Register!A1","values":reg}, tok)
    _api(f"{base}/Findings!A1:F6000:clear", "POST", {}, tok)
    _api(f"{base}/Findings!A1?valueInputOption=RAW", "PUT", {"range":"Findings!A1","values":fnd}, tok)
    print(f"PHASE 2 (publish): {len(reg)-1} register + {len(fnd)-1} findings pushed to Sheet {SID}")

if __name__ == "__main__":
    args = sys.argv[1:]
    do_local = ("--publish" not in args)
    do_pub   = ("--local" not in args)
    if do_local: build_local()
    if do_pub:   publish_sheet()
