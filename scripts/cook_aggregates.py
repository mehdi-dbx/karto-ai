#!/usr/bin/env python3
"""
KARTO — cook aggregates from the raw register into atlas-ready JSON.
Raw bones (data/register.csv) -> cooked meat (data/atlas.json) for the dashboard.
Reproducible: python3 scripts/cook_aggregates.py
"""
import csv, json, re, os, glob
from collections import Counter, defaultdict

# ROOT resolves from this file, but the gate's dry-run cook (scripts/gate.py) sets
# KARTO_ROOT to a temp dir so it can cook STAGED data in isolation without touching real data/.
ROOT = os.environ.get("KARTO_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
OUT  = os.path.join(ROOT, "data", "atlas.json")

CC_NAME = {"US":"United States","JP":"Japan","CN":"China","KR":"South Korea","UK":"United Kingdom",
 "IN":"India","FR":"France","IT":"Italy","DE":"Germany","ES":"Spain","RU":"Russia","CH":"Switzerland",
 "BR":"Brazil","MA":"Morocco",
 # Wave 1
 "TW":"Taiwan","NL":"Netherlands","CA":"Canada","AU":"Australia","SA":"Saudi Arabia","SG":"Singapore",
 "IL":"Israel","SE":"Sweden","DK":"Denmark","AE":"United Arab Emirates","HK":"Hong Kong","ZA":"South Africa",
 # Wave 2
 "MX":"Mexico","IE":"Ireland","BE":"Belgium","NO":"Norway","FI":"Finland","PL":"Poland","TR":"Turkey",
 "ID":"Indonesia","AT":"Austria","VN":"Vietnam","PT":"Portugal"}
# rough centroids [lon,lat] for map placement (self-contained, no geo lib)
CC_LL = {"US":[-98,39],"JP":[138,37],"CN":[104,35],"KR":[128,36],"UK":[-2,54],"IN":[79,22],
 "FR":[2,47],"IT":[12,42],"DE":[10,51],"ES":[-4,40],"RU":[90,62],"CH":[8,47],"BR":[-51,-11],"MA":[-7,32],
 # Wave 1
 "TW":[121,23.7],"NL":[5.3,52.1],"CA":[-106,56],"AU":[134,-25],"SA":[45,24],"SG":[103.8,1.35],
 "IL":[35,31.5],"SE":[15,62],"DK":[10,56],"AE":[54,24],"HK":[114.1,22.3],"ZA":[24,-29],
 # Wave 2
 "MX":[-102,23],"IE":[-8,53],"BE":[4.5,50.6],"NO":[8.5,61],"FI":[26,64],"PL":[19,52],"TR":[35,39],
 "ID":[118,-2],"AT":[14.5,47.6],"VN":[106,16],"PT":[-8,39.5]}

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
        if len(x)<11: x=x+[""]*(11-len(x))
        rows.append(x)  # 0 company 1 cc 2 vertical 3 raw 4 horizontal 5 use 6 existence 7 value 8 tier 9 url 10 date

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
dated=sum(1 for r in rows if r[10].strip() and r[10].strip().lower()!="missing")
GLOBAL={"deployments":tot,"companies":companies,"countries":countries,
 "confirmed":eb["confirmed"],"claimed":eb["claimed"],"none":eb["none"],
 "with_value_number":with_num,"tier_primary":tierP,"dated":dated}

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

def verdict_v2(cells):
    # B3: 4-state — splits old 'talk' into 'unquantified' (real confirmed activity, no numbers:
    # a sales target) vs 'talk' (unconfirmed rumor: noise). A consultant reads these oppositely.
    #   proven        >=40% of rows carry a value number
    #   active        >=15% carry a value number
    #   unquantified  <15% numbers BUT majority of rows CONFIRMED  (real program, no published ROI)
    #   talk          <15% numbers AND majority CLAIMED/unconfirmed (hype / rumor)
    n=len(cells)
    if not n: return "talk"
    conf=sum(1 for r in cells if exist_bucket(r[6])=="confirmed")
    withnum=sum(1 for r in cells if has_num(r[7]))
    share=withnum/n
    if conf>0 and share>=0.40: return "proven"
    if conf>0 and share>=0.15: return "active"
    if conf*2>=n: return "unquantified"   # majority (>=50%) confirmed, but thin on numbers
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
            out.append({"v":v,"h":h,"n":len(cs),"withnum":withnum,
                        "verdict":verdict_for(cs),        # DEPRECATED (3-state) — remove next release
                        "verdict_v2":verdict_v2(cs)})     # B3 4-state
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
                    "proof_pct":round(100*withnum/len(cs)),
                    "verdict":verdict_for(cs),"verdict_v2":verdict_v2(cs)})
    return sorted(out, key=lambda x:-x["n"])
VERT_TOTALS_GLOBAL=verticals_for(rows)
VERT_TOTALS_BY_CC={cc:verticals_for([r for r in rows if r[1]==cc]) for cc in {r[1] for r in rows}}

# ---------- companies[] + benchmarks (B1/B2) + silent set (A1/D4) ----------
def slugify(name):
    s=re.sub(r"[^a-z0-9]+","-", name.lower()).strip("-")
    return s or "company"

# aggregate register rows per (company, cc)
comp=defaultdict(list)
for r in rows: comp[(r[0], r[1])].append(r)

# load universe (searched population) for silent companies + join
UNI={}
uni_path=os.path.join(ROOT,"data","universe.csv")
if os.path.exists(uni_path):
    ur=list(csv.reader(open(uni_path))); uhdr=ur[0]
    for u in ur[1:]:
        d=dict(zip(uhdr,u))
        UNI[(d["company"].strip(), d["cc"].strip().upper())]=d

# Phase A — alias map: universe (name,cc) -> the register (name,cc) it actually corresponds to.
# Prevents mislabeling swept companies as "silent" over spelling/suffix/cc differences.
ALIAS={}
alias_path=os.path.join(ROOT,"data","company_aliases.csv")
if os.path.exists(alias_path):
    for a in csv.DictReader(open(alias_path)):
        ALIAS[(a["universe_name"].strip(), a["universe_cc"].strip().upper())]=(a["register_name"].strip(), a["register_cc"].strip().upper())

def company_vertical(cc, name, regrows):
    if regrows: return regrows[0][2]           # from register
    return ""                                   # silent: vertical unknown (universe has no vertical)

COMPANIES=[]
seen_slugs={}
for (name,cc),rr in comp.items():
    dep=len(rr)
    conf=sum(1 for r in rr if exist_bucket(r[6])=="confirmed")
    wn=sum(1 for r in rr if has_num(r[7]))
    vert=rr[0][2]
    slug=slugify(name);
    if slug in seen_slugs: slug=f"{slug}-{cc.lower()}"   # collision guard
    seen_slugs[slug]=1
    u=UNI.get((name,cc),{})
    COMPANIES.append({"slug":slug,"name":name,"cc":cc,"vertical":vert,
        "deployments":dep,"confirmed":conf,"with_value_number":wn,
        "proof_rate":round(wn/dep,3) if dep else 0,
        "mktcap":u.get("market_cap_usd") or None,"revenue":u.get("revenue_usd") or None,
        "employees":u.get("employees") or None,"silent":False})

# silent companies: in universe, absent from register (honoring the alias map — Phase A)
reg_keys={(name,cc) for (name,cc) in comp}
for (name,cc),u in UNI.items():
    if (name,cc) in reg_keys: continue
    if ALIAS.get((name,cc)) in reg_keys: continue   # swept under a different spelling/cc — NOT silent
    slug=slugify(name)
    if slug in seen_slugs: slug=f"{slug}-{cc.lower()}"
    seen_slugs[slug]=1
    COMPANIES.append({"slug":slug,"name":name,"cc":cc,"vertical":u.get("raw_sector",""),
        "deployments":0,"confirmed":0,"with_value_number":0,"proof_rate":0,
        "mktcap":u.get("market_cap_usd") or None,"revenue":u.get("revenue_usd") or None,
        "employees":u.get("employees") or None,"silent":True,"index":u.get("index","")})

# B1 normalized metrics — compute-when-present (null-safe). Lights up post-resweep, no schema change.
def _num(x):
    try: return float(str(x).replace(",","")) if x not in (None,"","None") else None
    except: return None
for c in COMPANIES:
    rev=_num(c.get("revenue")); emp=_num(c.get("employees")); mc=_num(c.get("mktcap"))
    c["mktcap"]=mc; c["revenue"]=rev; c["employees"]=emp
    c["per_bn_revenue"]=round(c["deployments"]/(rev/1e9),2) if rev and rev>0 else None
    c["per_10k_emp"]=round(c["deployments"]/(emp/1e4),2) if emp and emp>0 else None

# B2 percentile benchmarks within peer groups (deployment count / confirmed / proof rate)
def pctile(sorted_vals, v):
    # share of peers strictly below v, ties share rank; 0-100
    below=sum(1 for x in sorted_vals if x < v)
    return round(100*below/(len(sorted_vals)-1)) if len(sorted_vals)>1 else None

active_comp=[c for c in COMPANIES if not c["silent"]]
def peer_bench(group):
    if len(group)<5: return None
    dvals=sorted(c["deployments"] for c in group)
    cvals=sorted(c["confirmed"] for c in group)
    pvals=sorted(c["proof_rate"] for c in group)
    out={}
    for c in group:
        c.setdefault("benchmarks",{})
        out[c["slug"]]={"deployments":pctile(dvals,c["deployments"]),
                        "confirmed":pctile(cvals,c["confirmed"]),
                        "proof_rate":pctile(pvals,c["proof_rate"]),"n":len(group)}
    return out
# global-vertical peer groups
byv=defaultdict(list)
for c in active_comp: byv[c["vertical"]].append(c)
for v,grp in byv.items():
    b=peer_bench(grp)
    if b:
        for c in grp: c["benchmarks"]["global_vertical"]=b[c["slug"]]
# country-vertical peer groups
byvc=defaultdict(list)
for c in active_comp: byvc[(c["vertical"],c["cc"])].append(c)
for key,grp in byvc.items():
    b=peer_bench(grp)
    if b:
        for c in grp: c["benchmarks"]["country_vertical"]=b[c["slug"]]

# D4 silent view payload: silent companies + peer context (median deployments of vertical×country peers)
import statistics
peer_med={}
for (v,cc),grp in byvc.items():
    peer_med[(v,cc)]=statistics.median([c["deployments"] for c in grp]) if grp else 0
SILENT=[{"slug":c["slug"],"name":c["name"],"cc":c["cc"],"sector":c.get("vertical",""),
         "index":c.get("index",""),"mktcap":c.get("mktcap"),"revenue":c.get("revenue"),"employees":c.get("employees"),
         "peer_median":peer_med.get((c["vertical"],c["cc"]),None)}
        for c in COMPANIES if c["silent"]]

# ---------- A5 freshness helpers (used by CELLS + global) ----------
NOW_YEAR=2026   # cook anchor; date-based staleness. (No live clock dependency.)
def year_of(d):
    m=re.match(r"(19|20)\d{2}", (d or "").strip())
    return int(m.group(0)) if m else None
def stale_bucket(d):
    y=year_of(d)
    if y is None: return "undated"
    age=NOW_YEAR-y
    if age<=1: return "fresh"
    if age<=2: return "aging"
    return "stale"

# ---------- cell drill-down (Altitude 3): companies per (cc, vertical, horizontal) ----------
CELLS=defaultdict(list)
for r in rows:
    key=f"{r[1]}|{r[2]}|{norm_h(r[4])}"
    CELLS[key].append({"company":r[0],"use":r[5],"existence":exist_bucket(r[6]),
                       "value":r[7],"tier":r[8],"url":r[9],"raw_sector":r[3],"date":r[10],
                       "fresh":stale_bucket(r[10])})

# ---------- B4 momentum (deployments over time) ----------
def timeline(subset):
    ys=Counter(); undated=0
    for r in subset:
        y=year_of(r[10])
        if y is None: undated+=1
        else: ys[y]+=1
    return ys, undated
def momentum_label(ys, first_seen, vertical_first_terciles):
    # rising if last-2yr count > prior-2yr; gone_quiet if history but nothing in last 2yr
    if not ys: return "none"
    recent=sum(v for y,v in ys.items() if y>=NOW_YEAR-1)
    prior=sum(v for y,v in ys.items() if NOW_YEAR-3<=y<NOW_YEAR-1)
    labels=[]
    if first_seen is not None and vertical_first_terciles and first_seen<=vertical_first_terciles[0]:
        labels.append("early_mover")
    elif first_seen is not None and vertical_first_terciles and first_seen>vertical_first_terciles[1]:
        labels.append("late_entrant")
    if recent>prior: labels.append("rising")
    elif recent==0 and sum(ys.values())>0: labels.append("gone_quiet")
    elif recent<prior: labels.append("cooling")
    else: labels.append("flat")
    return ",".join(labels) or "flat"

GLOBAL_TL, GLOBAL_UNDATED = timeline(rows)
TIMELINE_GLOBAL=[{"year":y,"n":GLOBAL_TL[y]} for y in sorted(GLOBAL_TL)]

# per-vertical first_seen terciles (for early/late labels)
vert_firsts={}
for v in VERTS:
    fs=[year_of(r[10]) for r in rows if r[2]==v and year_of(r[10])]
    vert_firsts[v]=sorted(fs)
def terciles(sorted_years):
    if len(sorted_years)<3: return None
    import statistics
    q1=sorted_years[len(sorted_years)//3]; q2=sorted_years[2*len(sorted_years)//3]
    return (q1,q2)
VERT_TERCILES={v:terciles(fs) for v,fs in vert_firsts.items()}

MOMENTUM_VERT=[]
for v in VERTS:
    sub=[r for r in rows if r[2]==v]
    ys,und=timeline(sub); fs=min((year_of(r[10]) for r in sub if year_of(r[10])), default=None)
    if not sub: continue
    MOMENTUM_VERT.append({"v":v,"first_seen":fs,"by_year":[{"year":y,"n":ys[y]} for y in sorted(ys)],
        "undated":und,"undated_pct":round(100*und/len(sub)),
        "label":momentum_label(ys,fs,VERT_TERCILES.get(v))})
MOMENTUM_CC=[]
for cc in sorted({r[1] for r in rows}):
    sub=[r for r in rows if r[1]==cc]
    ys,und=timeline(sub); fs=min((year_of(r[10]) for r in sub if year_of(r[10])), default=None)
    MOMENTUM_CC.append({"cc":cc,"name":CC_NAME.get(cc,cc),"first_seen":fs,
        "by_year":[{"year":y,"n":ys[y]} for y in sorted(ys)],
        "undated":und,"undated_pct":round(100*und/len(sub)) if sub else 0})

# attach momentum to each company (B4 -> D1/D5)
for c in COMPANIES:
    if c["silent"]: continue
    sub=comp.get((c["name"],c["cc"]),[])
    ys,und=timeline(sub); fs=min((year_of(r[10]) for r in sub if year_of(r[10])), default=None)
    c["first_seen"]=fs
    c["by_year"]=[{"year":y,"n":ys[y]} for y in sorted(ys)]
    c["undated_pct"]=round(100*und/len(sub)) if sub else 0
    c["momentum"]=momentum_label(ys,fs,VERT_TERCILES.get(c["vertical"]))

# ---------- A4 maturity classifier (L0-L4, disclosure footprint) ----------
STOP={"AI","GenAI","LLM","ML","GPT","The","A","An","And","Of","For","In","On","New","Our","Its"}
def named_product(use):
    # capitalized multi-letter token not in stoplist, or quoted product name
    q=re.findall(r'"([A-Z][\w\.\- ]{1,30})"', use or "")
    if q: return q[0].strip()
    for tok in re.findall(r'\b([A-Z][a-zA-Z]{2,})\b', use or ""):
        if tok not in STOP: return tok
    return None
def maturity(rr):
    conf=[r for r in rr if exist_bucket(r[6])=="confirmed"]
    ev=[]
    if not rr: return "L0", ev
    if not conf: return "L1", ["rows_no_confirmed"]
    horizons={norm_h(r[4]) for r in conf}
    years={year_of(r[10]) for r in conf if year_of(r[10])}
    prod=next((named_product(r[5]) for r in conf if named_product(r[5])), None)
    hasnum=any(has_num(r[7]) for r in conf)
    tierP=any(r[8].strip().upper()=="P" for r in conf)
    if len(horizons)>=2: ev.append("multi_horizontal")
    if prod: ev.append("named_product:"+prod)
    if hasnum: ev.append("value_number")
    if len(years)>=2: ev.append("multi_year")
    if tierP: ev.append("tier_p")
    l3 = (len(horizons)>=2) or bool(prod) or hasnum
    l4 = l3 and len(years)>=2 and (hasnum or tierP)
    if l4: return "L4", ev
    if l3: return "L3", ev
    return "L2", (ev or ["single_confirmed"])
for c in COMPANIES:
    if c["silent"]:
        c["maturity"]="L0"; c["maturity_evidence"]=["silent"]; continue
    lvl,ev=maturity(comp.get((c["name"],c["cc"]),[]))
    c["maturity"]=lvl; c["maturity_evidence"]=ev
MATURITY_DIST=Counter(c["maturity"] for c in COMPANIES)

# ---------- B6 findings join (by country+vertical) ----------
FINDINGS=[]
fnd_path=os.path.join(ROOT,"data","findings.csv")
if os.path.exists(fnd_path):
    fr=list(csv.reader(open(fnd_path)))[1:]
    for f in fr:
        if len(f)<3: continue
        FINDINGS.append({"cc":f[0].strip().upper(),"vertical":f[1].strip() if len(f)>1 else "",
                         "finding":f[2] if len(f)>2 else "","url":f[3] if len(f)>3 else "",
                         "why":f[4] if len(f)>4 else ""})

# ---------- B5 opportunity scores (documented, no ML) ----------
# prospect_score per company: confirmed activity + absence of value numbers (unmeasured) + size proxy (deployments as weak proxy since no mktcap)
# 0-100. formula published in meta.
for c in COMPANIES:
    if c["silent"]:
        c["prospect_score"]=0; continue
    conf=c["confirmed"]; unmeasured = 1 - (c["proof_rate"] or 0)
    # more confirmed activity AND less proof = higher prospect (running AI without measuring it)
    raw = min(conf,10)/10*60 + unmeasured*40
    c["prospect_score"]=round(raw)
# ---------- A5 freshness aggregate + D6 hype detector ----------
FRESH=Counter(stale_bucket(r[10]) for r in rows)
GLOBAL_FRESH={k:FRESH.get(k,0) for k in ("fresh","aging","stale","undated")}

# D6 hype: per vertical — announcements (rows) vs substantiation (value numbers + money events)
# Money now comes from the UNIFIED data/money.csv (V3 Step 2), keyed by register_row_id.
# origin=register_extraction (regex claims) + dedicated_collection (commitments; near-empty
# until the Step 12 FS pilot — the money-in axis renders with a "pending" marker in the UI).
MONEY_BY_ROW=defaultdict(list)
COMMIT_BY_CO=defaultdict(list)    # dedicated_collection commitments, keyed by (company,cc) — company-level, no register_row_id
ALL_COMMITS=[]
money_path=os.path.join(ROOT,"data","money.csv")
if os.path.exists(money_path):
    for m in csv.DictReader(open(money_path)):
        rid=m.get("register_row_id","")
        if rid.isdigit():
            MONEY_BY_ROW[int(rid)].append(m)
        if m.get("origin")=="dedicated_collection":
            COMMIT_BY_CO[(m.get("company",""),m.get("cc",""))].append(m)
            ALL_COMMITS.append(m)
GLOBAL["commitments"]=len(ALL_COMMITS)   # money-in events; >0 after Step 12 -> UI pending marker self-clears
# vertical of a company (from register) -> tally commitments per vertical
co_vert={}
for r in rows: co_vert.setdefault((r[0],r[1]), r[2])
COMMIT_BY_VERT=Counter()
for (co,cc),lst in COMMIT_BY_CO.items():
    v=co_vert.get((co,cc))
    if v: COMMIT_BY_VERT[v]+=len(lst)
# map row index -> vertical (rows list order == register_row_id)
HYPE_VERT=[]
byv_rows=defaultdict(list)
for i,r in enumerate(rows): byv_rows[r[2]].append(i)
for v,idxs in byv_rows.items():
    announced=len(idxs)
    withnum=sum(1 for i in idxs if has_num(rows[i][7]))
    invest=sum(1 for i in idxs if any(m["kind"]=="investment" for m in MONEY_BY_ROW.get(i,[])))
    HYPE_VERT.append({"v":v,"announced":announced,"substantiated":withnum,"investments":invest,
                      "commitments":COMMIT_BY_VERT.get(v,0),   # money-in axis (dedicated_collection, company-level)
                      "substantiation_rate":round(withnum/announced,3) if announced else 0})
HYPE_VERT.sort(key=lambda x:-x["announced"])

META={
  "schema_version":"2.0",
  "generated_from":"data/register.csv (source of truth; never hand-edit atlas.json)",
  "verdict_v2":{
    "field":"verdict_v2 (grid + vert_totals cells)","states":["proven","active","unquantified","talk"],
    "rules":{"proven":">=40% of cell rows carry a value number (and >=1 confirmed)",
             "active":">=15% carry a value number (and >=1 confirmed)",
             "unquantified":"<15% numbers BUT majority of rows CONFIRMED (real program, no published ROI)",
             "talk":"<15% numbers AND majority CLAIMED/unconfirmed (hype)"}},
  "deprecated":{"verdict":"3-state (strong/active/talk). Superseded by verdict_v2; removed next release."},
  "date_convention":{"YYYY":"treated as mid-year","YYYY-MM":"as-is","missing":"excluded from time series, counted in undated"}
}
GLOBAL["searched"]=len(UNI)
GLOBAL["silent"]=len(SILENT)
GLOBAL["freshness"]=GLOBAL_FRESH
META["benchmarks"]={"method":"percentile rank within peer group (share of peers below; ties share rank). Peer groups <5 -> null.",
                    "groups":["global_vertical","country_vertical"],"metrics":["deployments","confirmed","proof_rate"]}
META["silent"]="companies in data/universe.csv (searched) with zero register rows (L0 silent)."
META["freshness"]={"anchor_year":NOW_YEAR,"buckets":{"fresh":"<=1yr","aging":"2yr","stale":">2yr","undated":"no date"}}
META["hype"]="hype_by_vertical: announced (rows) vs substantiated (rows w/ value number) + money events from data/money.csv (V3 Step 2 unified table). commitments (money-in axis) = dedicated_collection rows, near-empty until the Step 12 FS pilot."
META["money"]="data/money.csv unified table: origin register_extraction (regex claims) | dedicated_collection (purpose-collected commitments). Retires claims.csv/commitments.csv."
META["maturity"]={"levels":{"L0":"silent (in universe, no rows)","L1":"talk (rows, none confirmed)","L2":"pilot (confirmed, single footprint)","L3":"operating (confirmed + multi-horizontal OR named product OR value number)","L4":"industrialized (L3 + multi-year + value/tier-P)"}}
META["scores"]={"prospect_score":"min(confirmed,10)/10*60 + (1-proof_rate)*40 — confirmed activity without measurement. 0-100."}
# ---------- A7/D9 use-case spine (data/usecases.csv -> usecases[] + transfer + diffusion) ----------
USECASES=[]; TRANSFER=[]
uc_path=os.path.join(ROOT,"data","usecases.csv")
tax_path=os.path.join(ROOT,"data","usecase_taxonomy.csv")
if os.path.exists(uc_path) and os.path.exists(tax_path):
    TAXN={t["pattern_id"]:t for t in csv.DictReader(open(tax_path))}
    tags=defaultdict(list)   # pattern_id -> [row_idx,...]
    for u in csv.DictReader(open(uc_path)):
        try: tags[u["pattern_id"]].append(int(u["row_id"]))
        except: pass
    for pid,idxs in tags.items():
        idxs=[i for i in idxs if i < len(rows)]
        if not idxs: continue
        cos={rows[i][0] for i in idxs}
        verts=Counter(rows[i][2] for i in idxs)
        ctys=Counter(rows[i][1] for i in idxs)
        yrs=[year_of(rows[i][10]) for i in idxs if year_of(rows[i][10])]
        wn=sum(1 for i in idxs if has_num(rows[i][7]))
        # diffusion: first_seen year per country
        diff={}
        for i in idxs:
            y=year_of(rows[i][10]); cc=rows[i][1]
            if y and (cc not in diff or y<diff[cc]): diff[cc]=y
        meta=TAXN.get(pid,{})
        USECASES.append({"pattern_id":pid,"name":meta.get("name",pid),"description":meta.get("description",""),
            "horizontal":meta.get("horizontal",""),"runners":len(cos),"deployments":len(idxs),
            "verticals":[v for v,_ in verts.most_common()],"countries":[c for c,_ in ctys.most_common()],
            "first_seen":min(yrs) if yrs else None,"with_value_number":wn,
            "proof_rate":round(wn/len(idxs),3),
            "diffusion":sorted([{"cc":c,"first_year":y} for c,y in diff.items()], key=lambda x:x["first_year"]),
            "top_companies":[rows[i][0] for i in idxs[:8]]})
    USECASES=[u for u in USECASES if u["runners"]>=2]   # no single-runner patterns (A7 test)
    USECASES.sort(key=lambda x:-x["runners"])
    # transfer_opportunities: pattern proven in vertical X (>=3 runners) but absent in vertical Y
    proven_pat_vert=defaultdict(set)
    for u in USECASES:
        for i in tags[u["pattern_id"]]:
            if i<len(rows): proven_pat_vert[u["pattern_id"]].add(rows[i][2])
    all_big_verts={v for v,_ in Counter(r[2] for r in rows).most_common(12)}
    for u in USECASES[:40]:
        present=proven_pat_vert[u["pattern_id"]]
        absent=[v for v in all_big_verts if v not in present]
        if present and absent:
            TRANSFER.append({"pattern_id":u["pattern_id"],"name":u["name"],
                "proven_in":sorted(present)[:6],"absent_in":sorted(absent)[:6]})
GLOBAL["usecase_patterns"]=len(USECASES)
QSTATS_USECASES=len(USECASES)

# ---------- A6/D10 vendor layer (data/vendors.csv -> vendors[] + per-company stack[]) ----------
VENDORS_AGG=[]; STACK_BY_CO=defaultdict(set); ROW_HAS_VENDOR=set()
vend_path=os.path.join(ROOT,"data","vendors.csv")
if os.path.exists(vend_path):
    vtags=defaultdict(list)   # vendor -> [row_idx]
    vtype={}
    for v in csv.DictReader(open(vend_path)):
        try: ri=int(v["row_id"])
        except: continue
        if ri>=len(rows): continue
        vtags[v["vendor"]].append(ri); vtype[v["vendor"]]=v["vendor_type"]
        ROW_HAS_VENDOR.add(ri)
        if v["vendor"]!="(in-house)": STACK_BY_CO[rows[ri][0]].add(v["vendor"])
    for vn,idxs in vtags.items():
        cos={rows[i][0] for i in idxs}
        verts=Counter(rows[i][2] for i in idxs); ctys=Counter(rows[i][1] for i in idxs)
        VENDORS_AGG.append({"vendor":vn,"slug":slugify(vn),"type":vtype.get(vn,""),
            "deployments":len(idxs),"customers":len(cos),
            "verticals":[v for v,_ in verts.most_common(6)],"countries":[c for c,_ in ctys.most_common(8)],
            "customer_list":sorted(cos)[:40]})
    VENDORS_AGG.sort(key=lambda x:-x["deployments"])
# attach stack to each company; refine prospect_score with vendor-absence (B5 reserved term)
co_row_idx=defaultdict(list)
for i,r in enumerate(rows): co_row_idx[(r[0],r[1])].append(i)
for c in COMPANIES:
    if c["silent"]: c["stack"]=[]; continue
    c["stack"]=sorted(STACK_BY_CO.get(c["name"],[]))
    # vendor-absence bump: confirmed activity + no named vendor => stronger prospect (needs services)
    has_vendor=any(i in ROW_HAS_VENDOR for i in co_row_idx.get((c["name"],c["cc"]),[]))
    if not c["silent"] and not has_vendor and c["confirmed"]>0:
        c["prospect_score"]=min(100, (c.get("prospect_score",0))+8)
    c["vendor_named"]=has_vendor
GLOBAL["vendors"]=len(VENDORS_AGG)

json.dump({"meta":META,"global":GLOBAL,"countries":COUNTRIES,"verticals":VERTS,"horizontals":HORZS,
           "grid_global":GRID_GLOBAL,"grid_by_country":GRID_BY_CC,"cells":CELLS,
           "vert_totals_global":VERT_TOTALS_GLOBAL,"vert_totals_by_country":VERT_TOTALS_BY_CC,
           "companies":COMPANIES,"silent":SILENT,"hype_by_vertical":HYPE_VERT,
           "timeline_global":TIMELINE_GLOBAL,"momentum_vertical":MOMENTUM_VERT,"momentum_country":MOMENTUM_CC,
           "findings":FINDINGS,"maturity_dist":dict(MATURITY_DIST),
           "usecases":USECASES,"transfer_opportunities":TRANSFER,"vendors":VENDORS_AGG},
          open(OUT,"w"), ensure_ascii=False, indent=1)

# ---------- N3 teaser stats for the question menu (data/question_stats.json) ----------
_unq=sum(1 for c in COMPANIES if not c["silent"] and c["confirmed"]>0 and c["with_value_number"]==0)
QSTATS={
  "count_l0": len(SILENT),
  "count_unquantified_active": _unq,
  "count_momentum_break": sum(1 for m in MOMENTUM_VERT if "rising" in (m.get("label") or "")),
  "count_deployments": GLOBAL["deployments"],
  "count_usecases": QSTATS_USECASES,     # Step 7
  "count_changes": None,      # lit by Step 10
}
json.dump(QSTATS, open(os.path.join(ROOT,"data","question_stats.json"),"w"), ensure_ascii=False, indent=1)

# ---------- H2 changelog: diff current vs prior compact state ----------
PREV=os.path.join(ROOT,"data","atlas_prev_state.json")
CHANGELOG=os.path.join(ROOT,"data","changelog.json")
def compact_state():
    st={}
    for c in COMPANIES:
        st[c["slug"]]={"n":c["deployments"],"conf":c["confirmed"],"wn":c["with_value_number"],
                       "mat":c.get("maturity"),"silent":c["silent"],"mom":c.get("momentum")}
    return st
cur_state=compact_state()
entries=[]
STAMP=os.environ.get("KARTO_COOK_DATE","")   # optional stamp; else undated entry
if os.path.exists(PREV):
    try: prev=json.load(open(PREV))
    except: prev={}
    name_of={c["slug"]:c["name"] for c in COMPANIES}
    for slug,now in cur_state.items():
        old=prev.get(slug)
        nm=name_of.get(slug,slug)
        if old is None:
            if not now["silent"]:
                entries.append({"type":"new_deployment","slug":slug,"name":nm,"text":f"{nm}: first appearance in the register"})
            continue
        if old.get("mat")!=now.get("mat") and now.get("mat") and old.get("mat"):
            entries.append({"type":"maturity_change","slug":slug,"name":nm,"text":f"{nm}: maturity {old['mat']} → {now['mat']}"})
        if old.get("wn",0)==0 and now.get("wn",0)>0:
            entries.append({"type":"first_value_number","slug":slug,"name":nm,"text":f"{nm}: first value number disclosed"})
        if old.get("n",0)<now.get("n",0):
            entries.append({"type":"new_deployment","slug":slug,"name":nm,"text":f"{nm}: +{now['n']-old['n']} deployment(s)"})
        if not old.get("silent") and now.get("silent"):
            entries.append({"type":"gone_quiet","slug":slug,"name":nm,"text":f"{nm}: no longer disclosing AI"})
json.dump({"generated":STAMP,"entries":entries}, open(CHANGELOG,"w"), ensure_ascii=False, indent=1)
QSTATS["count_changes"]=len(entries) if entries else None
json.dump(QSTATS, open(os.path.join(ROOT,"data","question_stats.json"),"w"), ensure_ascii=False, indent=1)
# persist current state as the next baseline
json.dump(cur_state, open(PREV,"w"), ensure_ascii=False)

print(f"cooked -> {OUT}")
print(f"  global: {GLOBAL['deployments']} deploys, {GLOBAL['companies']} cos, {GLOBAL['confirmed']} confirmed")
print(f"  countries: {len(COUNTRIES)} | grid cells (global): {len(GRID_GLOBAL)} | drill cells: {len(CELLS)}")
print(f"  horizontals after norm: {dict(Counter(norm_h(r[4]) for r in rows))}")
