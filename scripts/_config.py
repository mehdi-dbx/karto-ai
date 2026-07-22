"""Load KARTO local config (karto.config at repo root). Values are user-specific and git-ignored."""
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load():
    cfg = {}
    path = os.path.join(_ROOT, "karto.config")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); cfg[k.strip()] = v.strip()
    # env vars override file
    for k in ("KARTO_SHEET_ID", "KARTO_DOC_ID", "KARTO_QUOTA_PROJECT"):
        if os.environ.get(k): cfg[k] = os.environ[k]
    missing = [k for k in ("KARTO_SHEET_ID","KARTO_QUOTA_PROJECT") if not cfg.get(k)]
    if missing:
        raise SystemExit(f"Missing {missing} — copy karto.config.example to karto.config and fill it in.")
    return cfg
