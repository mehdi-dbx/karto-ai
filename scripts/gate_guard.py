#!/usr/bin/env python3
"""V3 Step 6 — path guard. Enforces that gate-managed data tables are only mutated through
scripts/gate.py. The gate stamps a checksum manifest (data/.gate_manifest.json) on every apply;
this guard recomputes checksums and fails if a managed table changed without going through the gate.

  python3 scripts/gate_guard.py check   # exit 1 if a managed table drifted off-gate
  python3 scripts/gate_guard.py stamp    # (re)record current checksums (called by gate.apply)

Managed tables (gate-only from Step 6 onward): money.csv, usecases.csv, vendors.csv, universe.csv.
register.csv is NOT managed here — it predates the gate (hand-built census + documented dedup);
it has its own backups + git history. Adding it to the gate is a later decision.
"""
import hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MANIFEST = os.path.join(DATA, ".gate_manifest.json")
MANAGED = ["money.csv", "usecases.csv", "vendors.csv", "universe.csv"]

def _sum(p):
    if not os.path.exists(p): return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def stamp():
    json.dump({t: _sum(os.path.join(DATA, t)) for t in MANAGED}, open(MANIFEST, "w"), indent=1)
    print("gate manifest stamped for:", ", ".join(t for t in MANAGED if os.path.exists(os.path.join(DATA, t))))

def check():
    if not os.path.exists(MANIFEST):
        print("gate_guard: no manifest yet (first run) — stamping."); stamp(); return 0
    man = json.load(open(MANIFEST)); drift = []
    for t in MANAGED:
        cur = _sum(os.path.join(DATA, t))
        if t in man and man[t] is not None and cur != man[t]:
            drift.append(t)
    if drift:
        print(f"GATE VIOLATION: {drift} changed off-gate. Route data changes through scripts/gate.py "
              f"(propose->review->apply). If this change was intentional & gated, run: python3 scripts/gate_guard.py stamp")
        return 1
    print("gate_guard: managed tables clean.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stamp": stamp()
    else: sys.exit(check())
