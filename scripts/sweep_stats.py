import glob, re
from collections import Counter
existence=Counter(); tier=Counter(); by_country=Counter(); confirmed_by_country=Counter()
total=0
for f in sorted(glob.glob("data/register/register_*.md")):
    cc=f.split("_")[1].split(".")[0].upper()
    for line in open(f):
        if "|" not in line or "http" not in line: continue
        c=[p.strip() for p in line.split("|")]
        while c and c[0]=="": c.pop(0)
        while c and c[-1]=="": c.pop()
        if len(c)<9 or c[0].lower()=="company": continue
        total+=1; by_country[cc]+=1
        rowtext=line.upper()
        if "CONFIRMED" in rowtext: existence["CONFIRMED"]+=1; confirmed_by_country[cc]+=1
        elif "CLAIMED" in rowtext: existence["CLAIMED"]+=1
        elif "SMOKE" in rowtext or "NO CONFIRMED" in rowtext: existence["SMOKE/NONE"]+=1
        else: existence["other"]+=1
print("TOTAL register rows:",total)
print("EXISTENCE:",dict(existence))
print("rows by country:",dict(by_country.most_common()))
