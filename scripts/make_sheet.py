import json, subprocess, urllib.request
QUOTA="gcp-dev-field-eng-aiapiquota"
AUTH="/Users/mehdi.lamrani/.vibe/marketplace/plugins/fe-google-tools/skills/google-auth/resources/google_auth.py"
TOK=subprocess.run(["python3",AUTH,"token"],capture_output=True,text=True).stdout.strip()
def api(url,method="GET",body=None):
    d=json.dumps(body).encode() if body else None
    r=urllib.request.Request(url,data=d,method=method,headers={"Authorization":f"Bearer {TOK}","x-goog-user-project":QUOTA,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r))

# 1. create with 4 tabs
doc=api("https://sheets.googleapis.com/v4/spreadsheets","POST",{
  "properties":{"title":"AI Deployment Register — Country Sweep"},
  "sheets":[
    {"properties":{"title":"Register","gridProperties":{"frozenRowCount":1}}},
    {"properties":{"title":"Findings","gridProperties":{"frozenRowCount":1}}},
    {"properties":{"title":"Noise","gridProperties":{"frozenRowCount":1}}},
    {"properties":{"title":"Progress","gridProperties":{"frozenRowCount":1}}},
  ]})
sid=doc["spreadsheetId"]
print("SHEET_ID:",sid)
print("URL: https://docs.google.com/spreadsheets/d/%s/edit"%sid)

# 2. headers per tab
headers={
 "Register":["company","country","company_sector","row_assigned","axis(H/V)","use_case","existence","value_claimed","tier","source_url","date"],
 "Findings":["country","row","finding","source_url","why_it_matters","date"],
 "Noise":["domain","country","row","note"],
 "Progress":["country","status","companies_done","companies_total","verticals_done","last_updated","notes"],
}
data=[{"range":f"{tab}!A1","values":[hdr]} for tab,hdr in headers.items()]
api(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values:batchUpdate","POST",
    {"valueInputOption":"RAW","data":data})

# 3. bold+grey header row on every tab
props=api(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}?fields=sheets.properties")["sheets"]
reqs=[]
for s in props:
    gid=s["properties"]["sheetId"]
    reqs.append({"repeatCell":{"range":{"sheetId":gid,"startRowIndex":0,"endRowIndex":1},
      "cell":{"userEnteredFormat":{"backgroundColor":{"red":0.85,"green":0.85,"blue":0.85},
      "textFormat":{"bold":True}}},"fields":"userEnteredFormat(backgroundColor,textFormat)"}})
api(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}:batchUpdate","POST",{"requests":reqs})
print("headers + formatting done")
# save id
open("/tmp/sheet_id.txt","w").write(sid)
