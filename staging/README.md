# staging/ — the review gate (V3 Step 6)

ALL data changes flow through here. Nothing writes data/ directly (build path-guards it).

Propose:  create staging/pending_{table}_{stamp}/ with:
  manifest.json  {"table":"money.csv","source":"...","write_columns":[...],"insert_ok":true}
  rows.csv       proposed rows (must carry the table's key columns)

Review:   python3 scripts/gate.py review staging/pending_...   # adds / updates / CONFLICTS
Apply:    python3 scripts/gate.py apply  staging/pending_... --yes

Hard rules (enforced in code, not by vigilance):
- Additive-by-default: only fill-empty on declared write_columns; non-null overwrite -> CONFLICT (quarantined).
- Immutable keys: a key change = a new row (insert), never an edit.
- Dry-run cook: staged data cooked in a temp dir; out-of-scope atlas-stat drift blocks apply.
- Every apply -> data/audit_log.csv + re-stamps data/.gate_manifest.json (clears the build guard).
- Auto-apply OFF (gate.config.json {"auto_apply":false}).

Managed tables: money.csv, usecases.csv, vendors.csv, universe.csv.
