#!/usr/bin/env python3
"""
KARTO — cook aggregates from the raw register into atlas-ready JSON.
Raw bones (data/register.csv) -> cooked meat (data/atlas.json) for the dashboard.
Reproducible: python3 scripts/cook_aggregates.py
"""
import csv, json, re, os, glob
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
OUT  = os.path.join(ROOT, "data", "atlas.json")

CC_NAME = {"US":"United States","JP":"Japan","CN":"China","KR":"South Korea","UK":"United Kingdom",
 "IN":"India","FR":"France","IT":"Italy","DE":"Germany","ES":"Spain","RU":"Russia","CH":"Switzerland",
 "BR":"Brazil","MA":"Morocco"}
# rough centroids [lon,lat] for map placement (self-contained, no geo lib)
CC_LL = {"US":[-98,39],"JP":[138,37],"CN":[104,35],"KR":[128,36],"UK":[-2,54],"IN":[79,22],
 "FR":[2,47],"IT":[12,42],"DE":[10,51],"ES":[-4,40],"RU":[90,62],"CH":[8,47],"BR":[-51,-11],"MA":[-7,32]}

def has_num(v): return bool(re.search(r"\d", v or "")) and (v or "").strip().lower() not in ("none","n/a","")
def exist_bucket(e):
    e=(e or "").upper()
    if e.startswith("CONFIRMED"): return "confirmed"
    if e.startswith("CLAIMED"): return "claimed"
    return "none"

rows=[]
with open(REG) as f:
    r=csv.reader(f); hdr=next(r)
    for x in r:
        if len(x)<10: x=x+[""]*(10-len(x))
        rows.append(x)  # 0 company 1 cc 2 vertical 3 raw 4 horizontal 5 use 6 existence 7 value 8 tier 9 url

# universe sizes (companies searched per country) for density denominator
uni=Counter()
for f in glob.glob(os.path.join(ROOT,"data","universe","universe_*.tsv")):
    cc=os.path.basename(f).split("_")[1].split(".")[0].upper()
    uni[cc]=sum(1 for _ in open(f))

# ---------- global (Altitude 0) ----------
tot=len(rows)
companies=len({r[0].lower() for r in rows})
countries=len({r[1] for r in rows})
eb=Counter(exist_bucket(r[6]) for r in rows)
with_num=sum(1 for r in rows if has_num(r[7]))
tierP=sum(1 for r in rows if r[8].strip().upper()=="P")
GLOBAL={"deployments":tot,"companies":companies,"countries":countries,
 "confirmed":eb["confirmed"],"claimed":eb["claimed"],"none":eb["none"],
 "with_value_number":with_num,"tier_primary":tierP}

# ---------- per country (Altitude 1) ----------
COUNTRIES=[]
for cc in sorted({r[1] for r in rows}):
    cr=[r for r in rows if r[1]==cc]
    conf=sum(1 for r in cr if exist_bucket(r[6])=="confirmed")
    ncomp=len({r[0].lower() for r in cr})
    searched=uni.get(cc, ncomp)
    withnum=sum(1 for r in cr if has_num(r[7]))
    COUNTRIES.append({
      "cc":cc,"name":CC_NAME.get(cc,cc),"ll":CC_LL.get(cc,[0,0]),
      "deployments":len(cr),"companies":ncomp,"searched":searched,
      "confirmed":conf,"confirmed_pct":round(100*conf/len(cr)) if cr else 0,
      "density":round(conf/searched,2) if searched else 0,   # confirmed per company searched (a ratio, not a %)
      "with_value_number":withnum,
      "proof_pct":round(100*withnum/len(cr)) if cr else 0,   # % of deployments carrying a value number
      "top_verticals":[{"v":v,"n":n} for v,n in Counter(r[2] for r in cr).most_common(5)],
    })

# ---------- vertical x horizontal grid, global + per country (Altitude 2) ----------
def norm_h(h):
    s=(h or "").lower()
    if any(k in s for k in["support","customer","service","cx","call","chatbot"]): return "Customer Support"
    if any(k in s for k in["software","code","dev","copilot","engineering"]): return "Software / Code"
    if any(k in s for k in["market","sales","content","advertis","campaign","personaliz"]): return "Sales / Marketing"
    if any(k in s for k in["back","hr","finance","procure","admin","rpa","ops","operation"]): return "Back-office / Ops"
    if any(k in s for k in["security","fraud","cyber","risk","threat","aml"]): return "Security / Risk"
    return "Core / Domain"
VERTS=[v for v,_ in Counter(r[2] for r in rows).most_common()]
HORZS=["Core / Domain","Customer Support","Software / Code","Sales / Marketing","Back-office / Ops","Security / Risk"]
def verdict_for(cells):
    # cells: list of raw rows in this (vertical,horizontal) cell.
    # The scarce, honest signal is a QUANTIFIED value number (only ~34% of rows carry one) —
    # tier-P is too common (58%) to discriminate. So verdict = value-number density of the cell:
    #   strong  proven — a real share of deployments cite a quantified result
    #   active  happening & confirmed, but value is largely unquantified
    #   talk    nothing confirmed, or almost no numbers behind the claims
    n=len(cells)
    if not n: return "talk"
    conf=sum(1 for r in cells if exist_bucket(r[6])=="confirmed")
    withnum=sum(1 for r in cells if has_num(r[7]))
    if conf==0: return "talk"
    share=withnum/n
    if share>=0.40: return "strong"
    if share>=0.15: return "active"
    return "talk"

def grid_for(subset):
    buckets=defaultdict(list)
    for r in subset: buckets[(r[2],norm_h(r[4]))].append(r)
    out=[]
    for v in VERTS:
        for h in HORZS:
            cs=buckets[(v,h)]
            if not cs: continue
            withnum=sum(1 for r in cs if has_num(r[7]))
            out.append({"v":v,"h":h,"n":len(cs),"withnum":withnum,"verdict":verdict_for(cs)})
    return out
GRID_GLOBAL=grid_for(rows)
GRID_BY_CC={cc:grid_for([r for r in rows if r[1]==cc]) for cc in {r[1] for r in rows}}

# ---------- per-vertical totals (histogram: compare AI adoption across industries) ----------
def verticals_for(subset):
    buckets=defaultdict(list)
    for r in subset: buckets[r[2]].append(r)
    out=[]
    for v in VERTS:
        cs=buckets.get(v,[])
        if not cs: continue
        conf=sum(1 for r in cs if exist_bucket(r[6])=="confirmed")
        withnum=sum(1 for r in cs if has_num(r[7]))
        out.append({"v":v,"n":len(cs),"confirmed":conf,"withnum":withnum,
                    "proof_pct":round(100*withnum/len(cs)),"verdict":verdict_for(cs)})
    return sorted(out, key=lambda x:-x["n"])
VERT_TOTALS_GLOBAL=verticals_for(rows)
VERT_TOTALS_BY_CC={cc:verticals_for([r for r in rows if r[1]==cc]) for cc in {r[1] for r in rows}}

# ---------- cell drill-down (Altitude 3): companies per (cc, vertical, horizontal) ----------
CELLS=defaultdict(list)
for r in rows:
    key=f"{r[1]}|{r[2]}|{norm_h(r[4])}"
    CELLS[key].append({"company":r[0],"use":r[5],"existence":exist_bucket(r[6]),
                       "value":r[7],"tier":r[8],"url":r[9],"raw_sector":r[3]})

json.dump({"global":GLOBAL,"countries":COUNTRIES,"verticals":VERTS,"horizontals":HORZS,
           "grid_global":GRID_GLOBAL,"grid_by_country":GRID_BY_CC,"cells":CELLS,
           "vert_totals_global":VERT_TOTALS_GLOBAL,"vert_totals_by_country":VERT_TOTALS_BY_CC},
          open(OUT,"w"), ensure_ascii=False, indent=1)

print(f"cooked -> {OUT}")
print(f"  global: {GLOBAL['deployments']} deploys, {GLOBAL['companies']} cos, {GLOBAL['confirmed']} confirmed")
print(f"  countries: {len(COUNTRIES)} | grid cells (global): {len(GRID_GLOBAL)} | drill cells: {len(CELLS)}")
print(f"  horizontals after norm: {dict(Counter(norm_h(r[4]) for r in rows))}")
