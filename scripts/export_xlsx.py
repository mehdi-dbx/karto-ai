#!/usr/bin/env python3
"""
KARTO — export the published Google Sheet to a local karto-report.xlsx.

This is PHASE 3 (the local-file deliverable). Chain:
  PHASE 1  merge_registers_to_sheet.py --local    (data/*.md -> canonical data/*.csv, in repo)
  PHASE 2  merge_registers_to_sheet.py --publish  (CSV -> Google Sheet tabs)
  PHASE 3  export_xlsx.py                          (Sheet -> karto-report.xlsx, opens in Excel/Numbers/LibreOffice)

Fully autonomous: run `python3 scripts/export_xlsx.py` and the repo produces the .xlsx.
No Claude, no extra libraries — uses the Drive export endpoint (native .xlsx, all tabs, formatting).
"""
import subprocess, urllib.request, urllib.parse, urllib.error, os, sys

QUOTA = "gcp-dev-field-eng-aiapiquota"
AUTH = "/Users/mehdi.lamrani/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py"
SID = "14BzbimaeY4tSXq6Ia8-gfYRZhUW6ZMlqUzprxgqaIkY"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "karto-report.xlsx")
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def main():
    tok = subprocess.run(["python3", AUTH, "token"], capture_output=True, text=True).stdout.strip()
    if not tok:
        print("ERROR: no Google token (run google_auth.py login)."); sys.exit(1)
    url = (f"https://www.googleapis.com/drive/v3/files/{SID}/export"
           f"?mimeType={urllib.parse.quote(XLSX_MIME)}")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}",
        "x-goog-user-project": QUOTA,          # <-- the header the raw curl was missing (caused 403)
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        print(f"ERROR: Drive export failed HTTP {e.code}: {e.read().decode()[:300]}"); sys.exit(1)
    # sanity: xlsx is a zip → starts with 'PK'
    if data[:2] != b"PK":
        print(f"ERROR: response is not a valid xlsx (got {data[:60]!r})"); sys.exit(1)
    with open(OUT, "wb") as fh:
        fh.write(data)
    print(f"OK: wrote {OUT} ({len(data):,} bytes) — opens in Excel / Numbers / LibreOffice, all tabs.")

if __name__ == "__main__":
    main()
