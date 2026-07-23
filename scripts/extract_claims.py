#!/usr/bin/env python3
"""
V2 Module A2 — regex value-extraction (NO LLM, per owner decision).
Parse value_claimed + use_case of every register row into data/claims.csv:
  row_id, company, cc, amount, currency, unit, claim_type, source_phrase
Auditability: source_phrase is the exact substring matched, verbatim from the register.

claim_type is inferred by nearby keywords (savings|revenue|investment|users|scale|vague).
    python3 scripts/extract_claims.py
"""
import csv, re, os

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG=os.path.join(ROOT,"data","register.csv")
OUT=os.path.join(ROOT,"data","claims.csv")

CUR={"$":"USD","US$":"USD","€":"EUR","£":"GBP","¥":"CNY","R$":"BRL","₩":"KRW","₹":"INR","AUD":"AUD","CAD":"CAD","SGD":"SGD","NOK":"NOK","SEK":"SEK","DKK":"DKK"}
# money: optional currency symbol/code, number, optional scale word
MONEY=re.compile(r"(US\$|R\$|[\$€£¥₩₹]|AUD|CAD|SGD|NOK|SEK|DKK)\s?(\d[\d,\.]*)\s?(bn|billion|b\b|million|mn|m\b|k\b|trillion|tn)?", re.I)
# scale counts: number + noun (users/clients/stores/employees/interactions/models/agents)
SCALE=re.compile(r"(\d[\d,\.]*)\s?(bn|billion|million|m|k)?\s?\+?\s?(users|clients|customers|stores|employees|staff|interactions|models|agents|transactions|trades|branches|devices|patients|documents|calls)", re.I)
PCT=re.compile(r"([+\-~]?\d[\d\.]*)\s?%")

SCALE_MULT={"k":1e3,"m":1e6,"mn":1e6,"million":1e6,"b":1e9,"bn":1e9,"billion":1e9,"tn":1e12,"trillion":1e12}

def classify(phrase, ctx):
    s=(phrase+" "+ctx).lower()
    if any(w in s for w in["saving","saved","cut cost","cost reduc","reduc","efficien","avoided"]): return "savings"
    if any(w in s for w in["revenue","sales","gains","gmv","income","uplift","conversion"]): return "revenue"
    if any(w in s for w in["invest","capex","commit","funding","deal","partnership","acquisition","acquire"]): return "investment"
    if any(w in s for w in["user","client","customer","interaction","transaction","store","employee","staff","patient","document","call","device","branch","trade","model","agent"]): return "scale"
    return "vague"

def num(s):
    try: return float(s.replace(",",""))
    except: return None

rows=list(csv.reader(open(REG)))[1:]
out=[]
for i,r in enumerate(rows):
    company,cc=r[0],r[1]
    val=r[7] if len(r)>7 else ""
    use=r[5] if len(r)>5 else ""
    for field in (val, use):
        if not field: continue
        for m in MONEY.finditer(field):
            cur=CUR.get(m.group(1).upper(),CUR.get(m.group(1),"?")); amt=num(m.group(2))
            scale=(m.group(3) or "").lower()
            if amt is not None and scale in SCALE_MULT: amt=amt*SCALE_MULT[scale]
            out.append([i,company,cc,amt,cur,"currency",classify(m.group(0),field),m.group(0).strip()])
        for m in SCALE.finditer(field):
            amt=num(m.group(1)); scale=(m.group(2) or "").lower()
            if amt is not None and scale in SCALE_MULT: amt=amt*SCALE_MULT[scale]
            out.append([i,company,cc,amt,"count",m.group(3).lower(),"scale",m.group(0).strip()])
        for m in PCT.finditer(field):
            out.append([i,company,cc,num(m.group(1).lstrip("+~")),"pct","%","metric_pct",m.group(0).strip()])

with open(OUT,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["row_id","company","cc","amount","currency","unit","claim_type","source_phrase"]); w.writerows(out)

from collections import Counter
print(f"claims.csv: {len(out)} claims from {len(rows)} rows -> {OUT}")
print("by claim_type:", dict(Counter(c[6] for c in out)))
print("rows with >=1 claim:", len({c[0] for c in out}))
