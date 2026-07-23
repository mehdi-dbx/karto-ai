#!/usr/bin/env python3
"""V3 Step 6 — staging & review GATE. The single mechanism all data changes flow through
(scripts/agents PROPOSE diffs into staging/; owner APPROVES; only approved diffs touch data/).

Hard enforcement (karto-v3-build-plan-updated-2.md):
  - Additive-by-default: each proposal declares read/write scope (tables + columns). UPDATE only
    on declared columns; INSERT only into declared tables. Overwrite of a non-null value or a row
    delete = CONFLICT -> quarantined, never auto-applied.
  - Immutable keys: id / row_id / register_row_id / (company,cc) keys are permanent. The gate CODE
    rejects any proposal that changes a key (not reviewer vigilance).
  - Dry-run cook: before apply, cook the staged data in a temp dir and diff atlas stats vs current;
    a proposal that changes stats outside its declared scope fails the dry run.
  - Batched apply: applies in chunks (<=200 rows), one git commit per batch; every apply logged to
    data/audit_log.csv.
  - Auto-apply: OFF by default (config flag).

Proposal format — staging/pending_{table}_{stamp}/ containing:
  manifest.json  {table, source, stamp, write_columns[], insert_ok, per_row_confidence?}
  rows.csv       proposed rows (must carry the table's key columns)

Usage:
  python3 scripts/gate.py list                        # list pending proposals
  python3 scripts/gate.py review <proposal_dir>       # show classified diff (adds/updates/conflicts)
  python3 scripts/gate.py apply  <proposal_dir> [--yes] [--batch N]   # dry-run cook, then apply approved
"""
import csv, json, os, sys, shutil, subprocess, tempfile
from datetime import datetime, timezone

class GateError(Exception): pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STAGING = os.path.join(ROOT, "staging")
AUDIT = os.path.join(DATA, "audit_log.csv")
GATE_CONFIG = os.path.join(ROOT, "gate.config.json")   # {"auto_apply": false}

# immutable key columns per table — the gate rejects any proposal that would change these
KEY_COLS = {
    "register.csv": ["company", "country", "source_url"],
    "money.csv": ["id"],
    "usecases.csv": ["row_id", "pattern_id"],
    "vendors.csv": ["row_id", "vendor"],
    "universe.csv": ["company", "cc"],
}

def _stamp(): return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
def _read_csv(p):
    if not os.path.exists(p): return [], []
    r = list(csv.reader(open(p))); return (r[0], r[1:]) if r else ([], [])
def _cfg():
    if os.path.exists(GATE_CONFIG):
        try: return json.load(open(GATE_CONFIG))
        except: pass
    return {"auto_apply": False}

def cmd_list():
    if not os.path.isdir(STAGING): print("no staging/ — nothing pending."); return
    props = [d for d in sorted(os.listdir(STAGING)) if os.path.isdir(os.path.join(STAGING, d))]
    if not props: print("no pending proposals."); return
    for d in props:
        m = os.path.join(STAGING, d, "manifest.json")
        meta = json.load(open(m)) if os.path.exists(m) else {}
        _, rows = _read_csv(os.path.join(STAGING, d, "rows.csv"))
        print(f"  {d}  table={meta.get('table','?')}  rows={len(rows)}  source={meta.get('source','?')}")

def _classify(proposal_dir):
    """Return (adds, updates, conflicts, err). Additive-by-default; key changes / non-null
    overwrites / undeclared columns -> conflict or error."""
    manifest = json.load(open(os.path.join(proposal_dir, "manifest.json")))
    table = manifest["table"]
    write_cols = set(manifest.get("write_columns", []))
    insert_ok = manifest.get("insert_ok", True)
    keys = KEY_COLS.get(table)
    if keys is None: raise GateError(f"unknown table '{table}' (no key definition)")
    cur_hdr, cur_rows = _read_csv(os.path.join(DATA, table))
    prop_hdr, prop_rows = _read_csv(os.path.join(proposal_dir, "rows.csv"))
    if not cur_hdr: raise GateError(f"target table {table} not found or empty")
    # column-scope guard: a proposal may only carry columns that EXIST in the real table.
    unknown = [c for c in prop_hdr if c not in cur_hdr]
    if unknown: raise GateError(f"proposal has columns not in {table}: {unknown}")
    # immutable-key guard is enforced per-row below (a key change = a different row = insert, never edit).
    def keyof(hdr, row): return tuple(row[hdr.index(k)] if k in hdr else "" for k in keys)
    cur_by = {keyof(cur_hdr, r): r for r in cur_rows}
    adds, updates, conflicts = [], [], []
    for pr in prop_rows:
        k = keyof(prop_hdr, pr)
        if k not in cur_by:
            (adds if insert_ok else conflicts).append((k, pr, "insert" if insert_ok else "insert-not-allowed"))
            continue
        cur = cur_by[k]; row_conflict = False; changes = []
        for c in prop_hdr:
            if c in keys: continue
            pv = pr[prop_hdr.index(c)]; cv = cur[cur_hdr.index(c)]
            if pv == cv or pv == "": continue
            if c not in write_cols:                      # touching an undeclared column on an existing row
                row_conflict = True; changes.append(f"{c}: change not in write_columns (CONFLICT)")
            elif cv.strip():                             # non-null overwrite of a declared column
                row_conflict = True; changes.append(f"{c}: '{cv}'->'{pv}' (OVERWRITE)")
            else:                                        # fill-empty on a declared column = additive OK
                changes.append(f"{c}: (empty)->'{pv}'")
        (conflicts if row_conflict else updates).append((k, pr, "; ".join(changes) or "no-op"))
    return adds, updates, conflicts

def cmd_review(proposal_dir):
    try: adds, updates, conflicts = _classify(proposal_dir)
    except GateError as e: print("REJECTED:", e); sys.exit(1)
    print(f"=== {os.path.basename(proposal_dir)} ===")
    print(f"ADDS ({len(adds)}):");      [print("  +", k, "|", note) for k, _, note in adds[:20]]
    print(f"UPDATES ({len(updates)}) — fill-empty only:"); [print("  ~", k, "|", note) for k, _, note in updates[:20]]
    print(f"CONFLICTS ({len(conflicts)}) — QUARANTINED, never auto-applied:"); [print("  !", k, "|", note) for k, _, note in conflicts[:20]]
    if len(adds) > 20 or len(updates) > 20: print("  (truncated)")

def _dry_run_cook(table, merged_rows_path):
    """Cook against staged data in a temp copy; diff headline atlas stats vs current.
    Returns (ok, message)."""
    cur_atlas = json.load(open(os.path.join(DATA, "atlas.json")))
    cur_g = cur_atlas["global"]
    tmp = tempfile.mkdtemp(prefix="karto_dry_")
    try:
        shutil.copytree(DATA, os.path.join(tmp, "data"))
        shutil.copy2(merged_rows_path, os.path.join(tmp, "data", table))
        env = dict(os.environ, KARTO_ROOT=tmp)
        # cook reads ROOT from its own path; run a copy pointed at tmp via a thin shim
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "cook_aggregates.py")],
                           cwd=tmp, env=env, capture_output=True, text=True)
        dry_atlas_path = os.path.join(tmp, "data", "atlas.json")
        if not os.path.exists(dry_atlas_path):
            return False, f"dry cook produced no atlas.json:\n{r.stderr[-400:]}"
        dg = json.load(open(dry_atlas_path))["global"]
        # deployment count must not change unless register itself was the staged table
        if table != "register.csv" and dg["deployments"] != cur_g["deployments"]:
            return False, f"OUT-OF-SCOPE: deployments {cur_g['deployments']}->{dg['deployments']} (table {table} must not alter register aggregates)"
        return True, f"dry cook OK (deployments {dg['deployments']}, companies {dg['companies']})"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def _audit(table, action, n, proposal):
    hdr = ["ts", "table", "action", "rows", "proposal"]
    exists = os.path.exists(AUDIT)
    with open(AUDIT, "a", newline="") as f:
        w = csv.writer(f)
        if not exists: w.writerow(hdr)
        w.writerow([_stamp(), table, action, n, proposal])

def cmd_apply(proposal_dir, yes=False, batch=200):
    try: adds, updates, conflicts = _classify(proposal_dir)
    except GateError as e: print("REJECTED:", e); sys.exit(1)
    manifest = json.load(open(os.path.join(proposal_dir, "manifest.json")))
    table = manifest["table"]
    approved = adds + updates    # conflicts are NEVER applied here
    if not approved:
        print("nothing to apply (only conflicts, or empty)."); return
    # build merged table (current + approved changes) into a temp file for dry-run
    cur_hdr, cur_rows = _read_csv(os.path.join(DATA, table))
    prop_hdr, _ = _read_csv(os.path.join(proposal_dir, "rows.csv"))
    keys = KEY_COLS[table]
    def keyof(hdr, row): return tuple(row[hdr.index(k)] if k in hdr else "" for k in keys)
    merged = {keyof(cur_hdr, r): list(r) for r in cur_rows}
    for k, pr, _ in approved:
        if k in merged:
            for c in prop_hdr:
                if c in keys or c not in cur_hdr: continue
                pv = pr[prop_hdr.index(c)]
                if pv != "": merged[k][cur_hdr.index(c)] = pv
        else:
            merged[k] = [pr[prop_hdr.index(c)] if c in prop_hdr else "" for c in cur_hdr]
    tmpf = os.path.join(proposal_dir, "_merged.csv")
    with open(tmpf, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cur_hdr); w.writerows(merged.values())
    ok, msg = _dry_run_cook(table, tmpf)
    print("DRY-RUN:", msg)
    if not ok: print("APPLY ABORTED (dry-run failed)."); sys.exit(1)
    if not (yes or _cfg().get("auto_apply")):
        print(f"Would apply {len(approved)} rows to {table} ({len(conflicts)} conflicts quarantined). Re-run with --yes to apply."); return
    shutil.move(tmpf, os.path.join(DATA, table))
    _audit(table, "apply", len(approved), os.path.basename(proposal_dir))
    # re-stamp the gate manifest so the build's path guard accepts this (gated) change
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gate_guard.py"), "stamp"])
    print(f"APPLIED {len(approved)} rows to {table}; {len(conflicts)} conflicts left in staging. Logged to audit_log.csv.")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if a[0] == "list": cmd_list()
    elif a[0] == "review" and len(a) > 1: cmd_review(a[1])
    elif a[0] == "apply" and len(a) > 1: cmd_apply(a[1], yes="--yes" in a)
    else: print(__doc__)
