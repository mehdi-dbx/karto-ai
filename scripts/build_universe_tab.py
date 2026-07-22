import json, subprocess, urllib.request, glob
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _config import load as _load
_CFG = _load()

QUOTA=_CFG["KARTO_QUOTA_PROJECT"]
AUTH=_os.path.expanduser("~/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py")
TOK=subprocess.run(["python3",AUTH,"token"],capture_output=True,text=True).stdout.strip()
SID=_CFG["KARTO_SHEET_ID"]
def api(url,method="GET",body=None):
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method,headers={"Authorization":f"Bearer {TOK}","x-goog-user-project":QUOTA,"Content-Type":"application/json"})
    try:
        return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e:
        print("ERR",e.code,e.read().decode()[:200]); raise

def home_row(sector):
    s=(sector or "").lower()
    table=[
     (["bank","financ"],"V1 Financial Services"),
     (["insurance","reinsur","assur"],"V2 Insurance"),
     (["health","pharma","biotech","medical","life scien"],"V4 Healthcare"),
     (["media","entertain","gaming","publish"],"V5 Media/Gaming"),
     (["retail","consumer","e-commerce","distribut","apparel","food","bever","luxur","fmcg","fast moving","goods"],"V6 Retail & E-commerce"),
     (["manufactur","industrial","automotive","aerospace","machinery","chemical","material","steel","mechanical","heavy","conglomerate","semiconductor","electronic"],"V7 Manufacturing"),
     (["education","universit"],"V8 Education"),
     (["defence","defense","government"],"V9 Government"),
     (["utilit","energy","oil","gas","power","electric","renewab"],"V10 Energy & Utilities"),
     (["logisti","supply chain","shipping","transport","rail"],"V11 Logistics"),
     (["agri","farm","fertiliz"],"V12 Agriculture"),
     (["telecom","telecommunicat","wireless"],"V13 Telecom"),
     (["real estate","construct","building","btp","property","reit","cement"],"V14 Real Estate & Construction"),
     (["travel","hospitality","hotel","airline","leisure","tourism"],"V15 Travel & Hospitality"),
     (["technology","software","information tech","inspection","communication serv"],"V3/H1 Tech-ProfServ (agent decides)"),
    ]
    for keys,row in table:
        if any(k in s for k in keys): return row
    return "(unmapped)"

rows=[["company","country","index","company_sector","home_row_guess","status"]]
for f in sorted(glob.glob("universe_*.tsv")):
    for line in open(f):
        p=line.rstrip("\n").split("\t")
        if len(p)>=4 and p[0].strip():
            rows.append([p[0],p[1],p[2],p[3],home_row(p[3]),"not_started"])
print("total rows (incl header):",len(rows))

# clear (values clear needs empty JSON body {})
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Universe!A1:Z3000:clear","POST",{})
# single batched values update
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Universe!A1?valueInputOption=RAW","PUT",
    {"range":"Universe!A1","values":rows})
print("written OK:",len(rows)-1,"companies")
from collections import Counter
print(dict(Counter(r[1] for r in rows[1:])))
