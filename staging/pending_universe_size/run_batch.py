#!/usr/bin/env python3
"""Process a batch of companies [start,end) from US.csv, enrich, append to rows_US.csv.
Resumable: skips companies already present in rows_US.csv. Usage: run_batch.py START END"""
import csv, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enrich

BASE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(BASE, "parts", "US.csv")
OUT = os.path.join(BASE, "parts", "rows_US.csv")
HEADER = ["company","cc","market_cap_usd","revenue_usd","employees","ticker"]

def load_done():
    done = set()
    if os.path.exists(OUT):
        with open(OUT, newline="") as f:
            for row in csv.DictReader(f):
                done.add(row["company"])
    return done

def main():
    start = int(sys.argv[1]); end = int(sys.argv[2])
    with open(IN, newline="") as f:
        rows = list(csv.DictReader(f))
    done = load_done()
    processed = written = 0
    for row in rows[start:end]:
        company = row["company"]; cc = row["cc"]
        if company in done:
            continue
        tk = enrich.resolve_ticker(company)
        mc = rv = emp = ""
        if tk:
            mc, rv, emp = enrich.fetch_stats(tk)
        processed += 1
        # append immediately if at least one field found (per-company checkpoint)
        if tk or mc or rv or emp:
            exists = os.path.exists(OUT)
            with open(OUT, "a", newline="") as f:
                w = csv.writer(f)
                if not exists:
                    w.writerow(HEADER)
                w.writerow([company, cc, mc, rv, emp, tk])
            written += 1
        print(f"{company}\t{tk}\t{mc}\t{rv}\t{emp}", flush=True)
        time.sleep(1.5)
    print(f"\nBATCH {start}-{end}: processed {processed}, wrote {written} rows", flush=True)

if __name__ == "__main__":
    main()
