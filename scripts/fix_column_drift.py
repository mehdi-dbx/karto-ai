#!/usr/bin/env python3
"""
KARTO — repair column drift in register.csv.

47% of rows drifted: the existence token (| CONFIRMED etc.) got trapped at the
tail of use_case, existence col held a stray 'none', and value_claimed carried
the tier letter (P/I/S) while tier sat empty. This realigns them.

Pattern (verified: 772 rows, 0 residual — the spurious col was empty every time):
  use_case      "...text | CONFIRMED"   -> strip the "| TOKEN" tail
  existence     "none"                  -> the real TOKEN pulled from use_case
  value_claimed "P"  (a tier letter)    -> shifts right into tier
  tier          ""                      -> receives the tier letter
Clean rows (token already correctly in existence) are left untouched.

Reversible: writes a timestamped backup first. Re-run cook_aggregates.py after.
Usage: python3 scripts/fix_column_drift.py
"""
import csv, re, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
BAK  = os.path.join(ROOT, "data", "register.backup-drift-20260722.csv")

TAIL = re.compile(r'^(.*?)\s*\|\s*(CONFIRMED|CLAIMED|SMOKE|DIRECTIONAL|NONE|UNKNOWN)\s*$',
                  re.IGNORECASE | re.DOTALL)

rows = list(csv.reader(open(REG)))
hdr, data = rows[0], rows[1:]

fixed = 0
residual = 0
out = [hdr]
for r in data:
    if len(r) != 11:
        out.append(r); continue
    m = TAIL.match(r[5])
    if not m:
        out.append(r); continue          # clean row — token already where it belongs
    use, token = m.group(1).strip(), m.group(2).upper()
    value, tier, spurious = r[6], r[7], r[8]
    if spurious.strip():                  # shape assumption violated — leave it, flag it
        residual += 1
        out.append(r); continue
    # realign: existence <- token; use_case <- stripped; value stays; tier <- shifted letter
    out.append([r[0], r[1], r[2], r[3], r[4], use, token, value, tier, r[9], r[10]])
    fixed += 1

if residual:
    print(f"WARNING: {residual} drift rows had a non-empty spurious col — left untouched, eyeball them.")

shutil.copy2(REG, BAK)
with open(REG, "w", newline="") as f:
    w = csv.writer(f)
    w.writerows(out)

print(f"backup -> {BAK}")
print(f"repaired {fixed} drifted rows; {len(data)} total; {residual} residual")
