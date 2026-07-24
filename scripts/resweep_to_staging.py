#!/usr/bin/env python3
"""Turn the depth-resweep workflow output into a gated register proposal.

Reads a JSON file of verified per-company deployments (the workflow's return,
saved to staging/resweep_result.json) and writes:
    staging/pending_register_{stamp}/manifest.json
    staging/pending_register_{stamp}/rows.csv

Then review/apply through the gate as usual (never auto-applied):
    python3 scripts/gate.py review staging/pending_register_<stamp>
    python3 scripts/gate.py apply  staging/pending_register_<stamp> --yes

The register key is (company, country, use_case) — row-unique — so re-runs and
overlaps dedup instead of colliding. New deployments = INSERTs; nothing existing
is overwritten (the gate quarantines any non-null overwrite).
"""
import csv, json, os, sys, re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
STAGING = os.path.join(ROOT, "staging")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(STAGING, "resweep_result.json")

HDR = ["company","country","vertical","raw_sector","horizontal","use_case",
       "existence","value_claimed","tier","source_url","date"]

FUNCTIONS = {"Core / Domain","Customer Support","Software / Code",
             "Sales / Marketing","Back-office / Ops","Security / Risk"}

def norm_key(company, cc, use):
    return (company.strip(), cc.strip(), (use or "").strip().lower())

# existing register keys — so we only propose genuinely new deployments
existing = set()
reg = list(csv.reader(open(REG)))
for r in reg[1:]:
    if len(r) >= 6:
        existing.add(norm_key(r[0], r[1], r[5]))

data = json.load(open(SRC))
companies = data.get("companies", data if isinstance(data, list) else [])

out_rows, skipped_dup, skipped_bad = [], 0, 0
seen_this_batch = set()
for c in companies:
    company = c.get("company",""); cc = c.get("cc",""); vertical = c.get("vertical","")
    for d in c.get("rows", []):
        use = (d.get("use_case") or "").strip()
        url = (d.get("source_url") or "").strip()
        horizontal = (d.get("horizontal") or "").strip()
        existence = (d.get("existence") or "").strip().lower()
        # hard filters — no source or no use case = not a row (rule 4: real sources only)
        if not use or not re.match(r"^https?://", url): skipped_bad += 1; continue
        if horizontal not in FUNCTIONS: horizontal = ""      # tolerate, don't drop
        if existence not in ("confirmed","claimed"): existence = "claimed"
        k = norm_key(company, cc, use)
        if k in existing or k in seen_this_batch: skipped_dup += 1; continue
        seen_this_batch.add(k)
        val = (d.get("value_claimed") or "").strip() or "none"
        vendor = (d.get("vendor") or "").strip()
        # stash vendor into value/use context is lossy; keep vendor note in raw_sector-free way:
        # register has no vendor column, so append to use_case if named (keeps it searchable)
        use_full = use if not vendor else f"{use} [{vendor}]"
        date = (d.get("date") or "missing").strip() or "missing"
        out_rows.append([company, cc, vertical, "", horizontal, use_full,
                         existence, val, "", url, date])

if not out_rows:
    print(f"no new rows to propose (dup={skipped_dup}, bad={skipped_bad}). Nothing staged.")
    sys.exit(0)

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
pdir = os.path.join(STAGING, f"pending_register_{stamp}")
os.makedirs(pdir, exist_ok=True)
with open(os.path.join(pdir, "rows.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(HDR); w.writerows(out_rows)
json.dump({
    "table": "register.csv",
    "source": "depth-resweep workflow (query expansion + vendor-anchored, adversarially verified)",
    "stamp": stamp,
    "write_columns": HDR,           # inserts only; no existing row is edited
    "insert_ok": True,
}, open(os.path.join(pdir, "manifest.json"), "w"), indent=1)

print(f"staged {len(out_rows)} new deployment rows -> {pdir}")
print(f"  skipped: {skipped_dup} duplicates (already in register or repeated), {skipped_bad} bad (no source/use_case)")
print(f"  next: python3 scripts/gate.py review {os.path.relpath(pdir, ROOT)}")
