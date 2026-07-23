#!/usr/bin/env python3
"""Reversibly deduplicate near-duplicate VERTICAL labels in data/register.csv.

The register (source of truth) has accumulated near-duplicate vertical labels
that must be folded into a clean, canonical vocabulary before a later use-case
taxonomy pass. This script:

  1. Backs up register.csv to a timestamped copy (reversible).
  2. Folds duplicates via an explicit mapping + per-row manufacturing logic.
  3. Preserves the original vertical in raw_sector *only when raw_sector is
     empty* (otherwise raw_sector is left untouched -- the original label
     stays recoverable from the timestamped backup).
  4. Rewrites register.csv and prints before/after vertical counts.

It is idempotent: already-canonical labels are left unchanged, so re-running
is a no-op. Every non-vertical/non-raw_sector column is preserved verbatim and
the row count never changes.

Folds applied:
  * "Media"                -> "Media / Entertainment / Gaming"  (richer canonical)
  * "General Manufacturing" -> per-row best fit:
        robotics / automation / precision  -> "Manufacturing & Robotics"
        hard goods / heavy machinery / else -> "Industrial / Machinery" (default)
    "Manufacturing & Robotics" and "Industrial / Machinery" stay distinct.
"""

from __future__ import annotations

import csv
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REGISTER = Path(__file__).resolve().parent.parent / "data" / "register.csv"

VERTICAL_COL = 2
RAW_SECTOR_COL = 3

# --- Simple 1:1 folds ------------------------------------------------------
DIRECT_MAP = {
    "Media": "Media / Entertainment / Gaming",
}

# --- Per-row manufacturing consolidation -----------------------------------
GENERAL_MANUFACTURING = "General Manufacturing"
ROBOTICS = "Manufacturing & Robotics"
INDUSTRIAL = "Industrial / Machinery"

# Keywords (matched against company + raw_sector, case-insensitive) that mark a
# row as robotics/automation/precision. Everything else -- including genuinely
# ambiguous rows -- defaults to Industrial / Machinery per spec.
ROBOTICS_KEYWORDS = (
    "robot",
    "automation",
    "precision",
    "semiconductor",
    "electronics",
    "mechatronic",
)


def classify_general_manufacturing(company: str, raw_sector: str) -> str:
    """Map a 'General Manufacturing' row to its best-fit canonical vertical."""
    haystack = f"{company} {raw_sector}".lower()
    if any(keyword in haystack for keyword in ROBOTICS_KEYWORDS):
        return ROBOTICS
    return INDUSTRIAL  # hard goods / heavy machinery / ambiguous default


def canonical_vertical(company: str, vertical: str, raw_sector: str) -> str:
    """Return the canonical vertical for a row (unchanged if already canonical)."""
    if vertical in DIRECT_MAP:
        return DIRECT_MAP[vertical]
    if vertical == GENERAL_MANUFACTURING:
        return classify_general_manufacturing(company, raw_sector)
    return vertical


def normalize(rows: list[list[str]]) -> tuple[list[list[str]], int]:
    """Return (new_rows, changed_count). rows includes the header."""
    changed = 0
    out = [rows[0]]  # header
    for row in rows[1:]:
        company = row[0]
        old_vertical = row[VERTICAL_COL]
        raw_sector = row[RAW_SECTOR_COL]
        new_vertical = canonical_vertical(company, old_vertical, raw_sector)
        if new_vertical != old_vertical:
            changed += 1
            # Preserve the original label in raw_sector only when it is empty.
            if not raw_sector.strip():
                row[RAW_SECTOR_COL] = old_vertical
            row[VERTICAL_COL] = new_vertical
        out.append(row)
    return out, changed


def counts(rows: list[list[str]]) -> Counter:
    return Counter(row[VERTICAL_COL] for row in rows[1:])


def main() -> int:
    if not REGISTER.exists():
        print(f"ERROR: {REGISTER} not found", file=sys.stderr)
        return 1

    with REGISTER.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    before = counts(rows)
    row_count_before = len(rows)

    # Never clobber an existing backup: the first backup for a given date holds
    # the pre-dedup original, and a same-day re-run must not overwrite it with
    # already-normalized data. Add a numeric suffix if the name is taken.
    backup = REGISTER.with_name(f"register.backup-vertdedup-{date.today():%Y%m%d}.csv")
    if backup.exists():
        n = 2
        while backup.with_name(f"{backup.stem}-{n}.csv").exists():
            n += 1
        backup = backup.with_name(f"{backup.stem}-{n}.csv")
    shutil.copy2(REGISTER, backup)

    new_rows, changed = normalize(rows)
    after = counts(new_rows)

    # Safety: row count must be identical.
    assert len(new_rows) == row_count_before, "row count changed!"

    with REGISTER.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(new_rows)

    print(f"Backup written: {backup}")
    print(f"Rows (incl. header): {row_count_before} -> {len(new_rows)} (unchanged)")
    print(f"Rows changed: {changed}")
    print(f"Distinct verticals: {len(before)} -> {len(after)}")
    print()
    print("BEFORE:")
    for label, n in before.most_common():
        print(f"  {n:5d}  {label}")
    print("AFTER:")
    for label, n in after.most_common():
        print(f"  {n:5d}  {label}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
