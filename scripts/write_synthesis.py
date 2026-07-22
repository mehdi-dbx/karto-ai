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
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method,headers={"Authorization":f"Bearer {TOK}","x-goog-user-project":QUOTA,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r))
# add a Synthesis tab
try:
    api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}:batchUpdate","POST",
        {"requests":[{"addSheet":{"properties":{"title":"Synthesis","index":0}}}]})
except Exception: pass

S=[
["AI DEPLOYMENT SWEEP — CLOSING SYNTHESIS (breadth layer)"],
[""],
["Scope: 14 countries · ~1,600 companies (major stock indices) · 5+ languages · ~1,600 gated & source-linked deployment rows"],
["Method: enumerate each index → native-language search (WebFetch/DDG) → existence+value gate → checkpoint per company. Sample, NOT census."],
[""],
["THE THREE FINDINGS (held in ALL 14 countries):"],
["1. DEPLOYMENT IS REAL & NEAR-UNIVERSAL. ~89% of recorded rows CONFIRMED (own disclosure/filing/named system). Named AI programs everywhere: S&P500 to Moroccan mid-caps."],
["2. INDEPENDENT VALUE PROOF IS ~ABSENT. Every country report ended the same: value figures are self-claimed or vendor-sourced; independently-audited numbers essentially nonexistent (US: 0 across 503)."],
["3. THE SKEPTIC LAYER IS RICH & CONSISTENT: abstainers (Nintendo, Games Workshop, Berkshire), reversals (Société Générale build→buy), documented FAILURES (Keyence RPA, Zillow, Take-Two disbanded AI team), and the legally-exposed high-stakes cluster (UnitedHealth/CVS/Humana claim-denial; Anatel probing Vivo)."],
[""],
["CROSS-CUTTING PATTERNS:"],
["- Banking/insurance = deepest, most-quantified deployments in EVERY country."],
["- Sovereign-LLM race is real: China (named LLM per major SOE), Korea (HyperCLOVA X/EXAONE), Japan (tsuzumi/cotomi), France (Mistral partners), Switzerland/Swisscom (CHF100M)."],
["- 'Sell-vs-use' trap pervasive: chipmakers/IT-services/data-center firms sell AI ≠ use it. Gated out consistently (SMIC, Infosys-products, Solaria, Fluidra, Adani)."],
["- Heavy industry has real quantified production AI: Vale (72 autonomous units), Ambev (>50% of BR beer), Baosteel, ENEOS, Holcim (45 plants), John Deere (5M acres)."],
["- VISIBILITY-DISCOUNT THESIS PARTLY WRONG: China/Japan/Korea were DENSE, not thin — the barrier was English-only searching, not the markets. Morocco genuinely thin (small-market disclosure)."],
[""],
["THE RARE INDEPENDENT/EXTERNAL-VALIDATION SIGNALS (the ~1%):"],
["- CSPC (CN): AI-designed molecule → AstraZeneca deal ($110M upfront / up to $5.22bn) — 3rd-party commercial validation."],
["- China Yangtze Power: AI work published in Nature Communications."],
["- HCA (US) SPOT: ~8,000 lives saved (clinical outcome)."],
[""],
["BOTTOM LINE: The world is deploying AI everywhere and almost no one can independently prove it pays. Adoption ≠ profit. This breadth sweep empirically confirms the graded 20-row map's central thesis at ~1,600 data points."],
["", ],
["Data tabs: Register (all rows) · Findings (qualitative signals) · Universe (company backbone) · Noise (rejected domains). Every row source-linked."],
]
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/Synthesis!A1?valueInputOption=RAW","PUT",{"range":"Synthesis!A1","values":S})
# bold title
props=api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}?fields=sheets.properties")["sheets"]
gid=[s["properties"]["sheetId"] for s in props if s["properties"]["title"]=="Synthesis"][0]
api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}:batchUpdate","POST",{"requests":[
 {"repeatCell":{"range":{"sheetId":gid,"startRowIndex":0,"endRowIndex":1},"cell":{"userEnteredFormat":{"textFormat":{"bold":True,"fontSize":13}}},"fields":"userEnteredFormat.textFormat"}},
 {"updateSheetProperties":{"properties":{"sheetId":gid,"gridProperties":{"frozenRowCount":1}},"fields":"gridProperties.frozenRowCount"}}]})
print("Synthesis tab written")
