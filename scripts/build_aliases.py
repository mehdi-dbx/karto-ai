#!/usr/bin/env python3
"""Phase A — build data/company_aliases.csv mapping universe company names to their register
equivalents when they differ only by spelling / suffix / country-code. Fixes the join bug that
mislabels swept companies (Tencent, Alibaba, HSBC, L'Oreal...) as "silent".

Match rule: normalize (strip accents, legal suffixes, punctuation, lowercase). If a universe
company's normalized name equals a register company's normalized name, they're the same entity.
Emits {universe_name, universe_cc, register_name, register_cc} for every resolved pair where the
raw (name,cc) key differs (i.e. the join currently misses it).
    python3 scripts/build_aliases.py
"""
import csv, re, os, unicodedata
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
UNI  = os.path.join(ROOT, "data", "universe.csv")
OUT  = os.path.join(ROOT, "data", "company_aliases.csv")

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(inc|corp|corporation|ltd|limited|plc|sa|ag|group|holdings?|co|nv|se|spa|the|company|"
               r"gmbh|oyj|asa|ab|as|bhd|tbk|pjsc|psc|njsc|pao|ojsc)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)

reg = list(csv.reader(open(REG)))[1:]
# normalized register name -> the canonical (name, cc) actually present in the register
reg_by_norm = {}
reg_keys = set()
for r in reg:
    reg_keys.add((r[0], r[1]))
    reg_by_norm.setdefault(norm(r[0]), (r[0], r[1]))

uni = list(csv.DictReader(open(UNI)))
rows = []
for u in uni:
    key = (u["company"], u["cc"])
    if key in reg_keys:                    # exact join already works — no alias needed
        continue
    hit = reg_by_norm.get(norm(u["company"]))
    if hit and hit != key:                 # same entity, different spelling/cc -> alias it
        rows.append([u["company"], u["cc"], hit[0], hit[1]])

with open(OUT, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["universe_name","universe_cc","register_name","register_cc"]); w.writerows(rows)
print(f"company_aliases.csv: {len(rows)} universe->register aliases resolved -> {OUT}")
for r in rows[:12]: print("   ", r[0], f"({r[1]})", "->", r[2], f"({r[3]})")
