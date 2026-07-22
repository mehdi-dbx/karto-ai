import json, subprocess, urllib.request, glob, re
QUOTA="gcp-dev-field-eng-aiapiquota"
AUTH="/Users/mehdi.lamrani/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py"
TOK=subprocess.run(["python3",AUTH,"token"],capture_output=True,text=True).stdout.strip()
SID="14BzbimaeY4tSXq6Ia8-gfYRZhUW6ZMlqUzprxgqaIkY"
def api(url,method="GET",body=None):
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method,headers={"Authorization":f"Bearer {TOK}","x-goog-user-project":QUOTA,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r))
def cells(line):
    parts=[p.strip() for p in line.split("|")]
    while parts and parts[0]=="": parts.pop(0)
    while parts and parts[-1]=="": parts.pop()
    return parts

VALID_CC={"US","CN","UK","DE","FR","JP","KR","IN","RU","MA"}
reg=[]; seen=set()
for f in sorted(glob.glob("data/register/register_*.md")):
    cc=f.split("_")[1].split(".")[0].upper()   # authoritative country from filename
    for line in open(f):
        line=line.rstrip("\n")
        if "|" not in line or "http" not in line: continue
        c=cells(line)
        if len(c)<9 or c[0].lower()=="company" or set("".join(c[:1]))<=set("-: "): continue
        # find the URL (last http field) and company (first field)
        company=c[0]
        url=[x for x in c if x.startswith("http")]
        url=url[-1] if url else ""
        # normalize: force col2 = the authoritative country code from filename.
        # rebuild as: company, country, sector, row_assigned/use_case, use_case, existence, value, tier, url
        # tolerate the two known schemas by keeping the middle fields as the agent gave, minus any col that == a country-ish token
        mid=[x for x in c[1:] if x!=url and x not in VALID_CC][:6]
        row=[company, cc]+mid
        # pad/trim to 9
        row=(row+[""]*9)[:8]+[url]
        key=(company.lower(), (mid[-1] if mid else "")[:50].lower(), url.lower())
        if key in seen: continue
        seen.add(key); reg.append(row)

fnd=[]; fseen=set()
for f in sorted(glob.glob("data/findings/findings_*.md")):
    cc=f.split("_")[1].split(".")[0].upper()
    for line in open(f):
        line=line.rstrip("\n")
        if "|" not in line or "http" not in line: continue
        c=cells(line)
        if len(c)<2 or c[0].lower() in ("vertical","country","finding") or set("".join(c[:1]))<=set("-: "): continue
        url=[x for x in c if x.startswith("http")]; url=url[-1] if url else ""
        key=(cc,(c[0])[:80].lower())
        if key in fseen: continue
        fseen.add(key); fnd.append([cc]+c[:5])

from collections import Counter
print("register rows:",len(reg),"| by country:",dict(Counter(r[1] for r in reg)))
print("findings:",len(fnd))
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Register!A2:K6000:clear","POST",{})
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Register!A2?valueInputOption=RAW","PUT",{"range":"Register!A2","values":reg})
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Findings!A2:F6000:clear","POST",{})
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Findings!A2?valueInputOption=RAW","PUT",{"range":"Findings!A2","values":fnd})
print("written")
