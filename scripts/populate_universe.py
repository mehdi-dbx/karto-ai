import json, subprocess, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _config import load as _load
_CFG = _load()

QUOTA=_CFG["KARTO_QUOTA_PROJECT"]
AUTH=_os.path.expanduser("~/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py")
TOK=subprocess.run(["python3",AUTH,"token"],capture_output=True,text=True).stdout.strip()
SID=_CFG["KARTO_SHEET_ID"]
def api(url,method="GET",body=None):
    d=json.dumps(body).encode() if body else None
    r=urllib.request.Request(url,data=d,method=method,headers={"Authorization":f"Bearer {TOK}","x-goog-user-project":QUOTA,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r))

# crosswalk: GICS-ish sector -> our V-row (verticals). Functions (H) are cross-cutting, not a home row.
XWALK={
 "Financial Services":"V1 Financial Services",
 "Insurance":"V2 Insurance",
 "Healthcare":"V4 Healthcare & Life Sciences",
 "Communication Services":"V5 Media/Entertainment/Gaming",  # Orange/Publicis/Teleperf refined below
 "Consumer Cyclical":"V6 Retail & E-commerce",
 "Consumer Services":"V15 Travel & Hospitality",
 "Consumer Defensive":"V6 Retail & E-commerce",
 "Industrials":"V7 Manufacturing & Robotics",
 "Basic Materials":"V7 Manufacturing & Robotics",
 "Technology":"H1 Software / (AI-native)",
 "Utilities":"V10 Energy & Utilities",
 "Energy":"V10 Energy & Utilities",
 "Real Estate":"V14 Real Estate & Construction",
 "Inspection and Certification":"V3 Legal & Professional Services",
}
# per-company overrides where the generic sector is wrong for our taxonomy
OVERRIDE={
 "Orange":"V13 Telecom","Publicis":"V5 Media/Marketing","Teleperformance":"H2 Customer Support",
 "Capgemini":"V3 Legal & Professional Services","Dassault Systèmes":"H1 Software",
 "STMicroelectronics":"V7 Manufacturing & Robotics","Edenred":"V1 Financial Services",
 "Carrefour":"V6 Retail & E-commerce","Accor":"V15 Travel & Hospitality",
 "Unibail-Rodamco-Westfield":"V14 Real Estate & Construction",
}
cac40=[
 ("Accor","Consumer Services"),("Air Liquide","Basic Materials"),("Airbus","Industrials"),
 ("ArcelorMittal","Basic Materials"),("Axa","Insurance"),("BNP Paribas","Financial Services"),
 ("Bouygues","Industrials"),("Bureau Veritas","Inspection and Certification"),("Capgemini","Technology"),
 ("Carrefour","Consumer Defensive"),("Crédit Agricole","Financial Services"),("Danone","Consumer Defensive"),
 ("Dassault Systèmes","Technology"),("Edenred","Industrials"),("Engie","Utilities"),
 ("EssilorLuxottica","Healthcare"),("Eurofins Scientific","Healthcare"),("Hermès","Consumer Cyclical"),
 ("Kering","Consumer Cyclical"),("L'Oréal","Consumer Defensive"),("Legrand","Industrials"),
 ("LVMH","Consumer Cyclical"),("Michelin","Industrials"),("Orange","Communication Services"),
 ("Pernod Ricard","Consumer Defensive"),("Publicis","Communication Services"),("Renault","Consumer Cyclical"),
 ("Safran","Industrials"),("Saint-Gobain","Industrials"),("Sanofi","Healthcare"),
 ("Schneider Electric","Industrials"),("Société Générale","Financial Services"),("Stellantis","Consumer Cyclical"),
 ("STMicroelectronics","Technology"),("Teleperformance","Communication Services"),("Thales","Industrials"),
 ("TotalEnergies","Energy"),("Unibail-Rodamco-Westfield","Real Estate"),("Veolia","Industrials"),("Vinci","Industrials"),
]
def home_row(name,sector):
    return OVERRIDE.get(name) or XWALK.get(sector,"(unmapped)")

# 1. add 'index' col to Register header (insert as col B-ish -> just append to header, keep simple: append at end)
# read current Register header
hdr=api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Register!A1:Z1").get("values",[[]])[0]
if "index" not in hdr:
    newhdr=hdr[:2]+["index"]+hdr[2:]   # company,country,index,company_sector,...
    api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Register!A1?valueInputOption=RAW","PUT",
        {"range":"Register!A1","values":[newhdr]})
    print("added 'index' to Register header")

# 2. add Universe tab
try:
    api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}:batchUpdate","POST",
        {"requests":[{"addSheet":{"properties":{"title":"Universe","gridProperties":{"frozenRowCount":1}}}}]})
    print("Universe tab created")
except Exception as e:
    print("Universe tab exists or:",str(e)[:80])

# 3. header + rows
uhdr=["company","country","index","company_sector","home_row","status","companies_note"]
rows=[uhdr]
for name,sec in cac40:
    rows.append([name,"FR","CAC40",sec,home_row(name,sec),"not_started",""])
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Universe!A1?valueInputOption=RAW","PUT",
    {"range":"Universe!A1","values":rows})
print(f"wrote {len(cac40)} CAC40 companies to Universe")

# bold header on Universe
props=api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}?fields=sheets.properties")["sheets"]
gid=[s["properties"]["sheetId"] for s in props if s["properties"]["title"]=="Universe"][0]
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}:batchUpdate","POST",{"requests":[
 {"repeatCell":{"range":{"sheetId":gid,"startRowIndex":0,"endRowIndex":1},
  "cell":{"userEnteredFormat":{"backgroundColor":{"red":0.85,"green":0.85,"blue":0.85},"textFormat":{"bold":True}}},
  "fields":"userEnteredFormat(backgroundColor,textFormat)"}}]})
print("done")
