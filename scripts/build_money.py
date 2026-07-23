#!/usr/bin/env python3
"""Merge the two money feeders into ONE unified table (two feeders, one table).

Feeders
-------
1. data/claims.csv       — OUTPUT-side claims mined from register free-text by
                           extract_claims.py (regex value-extraction).
                           cols: row_id,company,cc,amount,currency,unit,claim_type,source_phrase
2. data/commitments.csv  — INPUT-side commitments (A3 stub; may be header +
                           comment only, i.e. no data rows yet).
                           cols: company,cc,amount,currency,commitment_type,horizon,tier,source_url,date

Output — data/money.csv, ONE unified schema
--------------------------------------------
    company, cc, amount, currency, unit, kind, origin, source, date

  origin  = which feeder the row came from: "claim" or "commitment".
  kind    = normalized money type shared across BOTH feeders (see mapping below).
  source  = source_phrase (claims) OR source_url (commitments).
  date    = date (commitments have one; claims do not -> blank).
  amount / currency / unit carried straight through from the feeder.

Unified `kind` vocabulary
-------------------------
    investment, savings, revenue, partnership, acquisition,
    scale_count, percentage_metric, other

claim_type (claims.csv)   -> kind                commitment_type (commitments.csv) -> kind
  investment              -> investment            invest          -> investment
  savings                 -> savings               savings_claim   -> savings
  revenue                 -> revenue               revenue_claim   -> revenue
  scale                   -> scale_count           partner         -> partnership
  metric_pct              -> percentage_metric     acquire         -> acquisition
  vague                   -> other                 (unknown)       -> other
  (unknown)               -> other

Idempotent: rerunning overwrites data/money.csv from the feeders each time.
Handles commitments.csv being empty / comment-only without crashing.
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CLAIMS = DATA / "claims.csv"
COMMITMENTS = DATA / "commitments.csv"
MONEY = DATA / "money.csv"

FIELDS = ["company", "cc", "amount", "currency", "unit", "kind", "origin", "source", "date"]

# Feeder-specific money-type -> unified kind.
CLAIM_KIND = {
    "investment": "investment",
    "savings": "savings",
    "revenue": "revenue",
    "scale": "scale_count",
    "metric_pct": "percentage_metric",
    "vague": "other",
}
COMMITMENT_KIND = {
    "invest": "investment",
    "savings_claim": "savings",
    "revenue_claim": "revenue",
    "partner": "partnership",
    "acquire": "acquisition",
}


def _clean(value: str | None) -> str:
    return (value or "").strip()


def read_claims() -> list[dict]:
    """Map claims.csv rows into the unified schema (origin=claim)."""
    if not CLAIMS.exists():
        return []
    rows = []
    with CLAIMS.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            claim_type = _clean(r.get("claim_type"))
            rows.append(
                {
                    "company": _clean(r.get("company")),
                    "cc": _clean(r.get("cc")),
                    "amount": _clean(r.get("amount")),
                    "currency": _clean(r.get("currency")),
                    "unit": _clean(r.get("unit")),
                    "kind": CLAIM_KIND.get(claim_type, "other"),
                    "origin": "claim",
                    "source": _clean(r.get("source_phrase")),
                    "date": "",  # claims carry no date
                }
            )
    return rows


def read_commitments() -> list[dict]:
    """Map commitments.csv rows into the unified schema (origin=commitment).

    Skips blank lines and '#'-comment lines so the A3 stub (header + comment,
    no data) yields zero rows instead of crashing.
    """
    if not COMMITMENTS.exists():
        return []
    with COMMITMENTS.open(newline="", encoding="utf-8") as fh:
        lines = [ln for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    if len(lines) <= 1:  # header only (or nothing) -> no data rows
        return []
    rows = []
    for r in csv.DictReader(lines):
        commitment_type = _clean(r.get("commitment_type"))
        rows.append(
            {
                "company": _clean(r.get("company")),
                "cc": _clean(r.get("cc")),
                "amount": _clean(r.get("amount")),
                "currency": _clean(r.get("currency")),
                "unit": "",  # commitments feeder has no unit column
                "kind": COMMITMENT_KIND.get(commitment_type, "other"),
                "origin": "commitment",
                "source": _clean(r.get("source_url")),
                "date": _clean(r.get("date")),
            }
        )
    return rows


def main() -> None:
    rows = read_claims() + read_commitments()

    with MONEY.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    by_origin: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for row in rows:
        by_origin[row["origin"]] = by_origin.get(row["origin"], 0) + 1
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1

    print(f"Wrote {MONEY.relative_to(DATA.parent)} — {len(rows)} money rows")
    print("\nby origin:")
    for origin in sorted(by_origin):
        print(f"  {origin:12s} {by_origin[origin]}")
    print("\nby kind:")
    for kind in sorted(by_kind):
        print(f"  {kind:18s} {by_kind[kind]}")


if __name__ == "__main__":
    main()
