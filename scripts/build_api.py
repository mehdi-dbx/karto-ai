#!/usr/bin/env python3
"""
V2 Module C3 — static API. Emit flat per-entity JSON files from data/atlas.json so
machines (notebooks, agents, Excel) can read the data by URL. GitHub Pages serves them.
    python3 scripts/build_api.py   -> api/company/*.json, api/country/*.json,
                                       api/vertical/*.json, api/index.json
Regenerate after every cook.
"""
import json, os, re

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A=json.load(open(os.path.join(ROOT,"data","atlas.json")))
API=os.path.join(ROOT,"api")
def wr(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path,"w"), ensure_ascii=False, indent=1)
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-") or "x"

# rows by company (for company payloads)
rows_by=dict()
for key,lst in A["cells"].items():
    for e in lst:
        rows_by.setdefault(e["company"], []).append(e)

ncomp=0
for c in A["companies"]:
    payload=dict(c); payload["deployments_detail"]=rows_by.get(c["name"],[])
    wr(os.path.join(API,"company",c["slug"]+".json"), payload); ncomp+=1

ncc=0
for co in A["countries"]:
    grid=A["grid_by_country"].get(co["cc"],[])
    verts=A["vert_totals_by_country"].get(co["cc"],[])
    wr(os.path.join(API,"country",co["cc"].lower()+".json"),
       {"country":co,"grid":grid,"verticals":verts}); ncc+=1

nv=0
for v in A["verticals"]:
    vg=[c for c in A["grid_global"] if c["v"]==v]
    vt=next((x for x in A["vert_totals_global"] if x["v"]==v), None)
    wr(os.path.join(API,"vertical",slug(v)+".json"), {"vertical":v,"totals":vt,"grid":vg}); nv+=1

INDEX={"schema_version":A["meta"]["schema_version"],
  "license":"CC BY-NC 4.0",
  "generated":"from data/register.csv via cook_aggregates.py + build_api.py",
  "counts":{"companies":ncomp,"countries":ncc,"verticals":nv,
            "deployments":A["global"]["deployments"]},
  "endpoints":{"company":"/api/company/{slug}.json","country":"/api/country/{cc}.json","vertical":"/api/vertical/{slug}.json"},
  "companies":[{"slug":c["slug"],"name":c["name"],"cc":c["cc"]} for c in A["companies"]],
  "countries":[{"cc":c["cc"],"name":c["name"]} for c in A["countries"]],
  "verticals":A["verticals"]}
wr(os.path.join(API,"index.json"), INDEX)
print(f"api: {ncomp} company + {ncc} country + {nv} vertical + index.json -> {API}/")
