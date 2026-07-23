#!/usr/bin/env python3
"""V3 Step 7 — use-case tagging (Module A7). Regex/keyword pass FIRST (method=regex);
residue (untagged rows) is reported for an optional one-time Claude build-time pass
(method=llm), whose outputs would be committed here and gated. No runtime LLM.

Taxonomy: data/usecase_taxonomy.csv  ->  data/usecases.csv {row_id,pattern_id,confidence,source_phrase,method}
A row may carry 1-2 patterns (best 2 keyword matches). source_phrase = the matched keyword's
neighbourhood in the use_case text (verbatim, for audit).
    python3 scripts/extract_usecases.py
"""
import csv, re, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
TAX  = os.path.join(ROOT, "data", "usecase_taxonomy.csv")
OUT  = os.path.join(ROOT, "data", "usecases.csv")

pats = []
for t in list(csv.DictReader(open(TAX))):
    pats.append((t["pattern_id"], [k.strip() for k in t["keywords"].split("|") if k.strip()]))

rows = list(csv.reader(open(REG)))[1:]
out, tagged_rows, residue = [], set(), []
for i, r in enumerate(rows):
    use = (r[5] or "")
    low = use.lower()
    hits = []
    for pid, kws in pats:
        for kw in kws:
            if kw in low:
                # capture a verbatim neighbourhood around the match for audit
                m = re.search(re.escape(kw), low)
                s = max(0, m.start()-20); e = min(len(use), m.end()+20)
                hits.append((pid, use[s:e].strip()))
                break
    # keep up to 2 distinct patterns per row
    seen = set(); kept = []
    for pid, phrase in hits:
        if pid in seen: continue
        seen.add(pid); kept.append((pid, phrase))
        if len(kept) == 2: break
    if kept:
        tagged_rows.add(i)
        conf = round(1.0/len(kept), 2) if len(kept) > 1 else 0.9
        for pid, phrase in kept:
            out.append([i, pid, conf, phrase, "regex"])
    else:
        residue.append((i, use[:80]))

with open(OUT, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["row_id","pattern_id","confidence","source_phrase","method"]); w.writerows(out)

cov = round(100*len(tagged_rows)/len(rows))
print(f"usecases.csv: {len(out)} tags across {len(tagged_rows)}/{len(rows)} rows ({cov}% coverage) -> {OUT}")
print(f"  residue (untagged, candidates for an LLM pass): {len(residue)}")
print("  top patterns:", Counter(o[1] for o in out).most_common(12))
# write residue for optional LLM pass
open(os.path.join(ROOT,"data","usecases_residue.txt"),"w").write(
    "\n".join(f"{i}\t{t}" for i,t in residue))
