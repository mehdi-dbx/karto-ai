#!/usr/bin/env python3
"""V3 Step 9 — vendor extraction (Module A6). Curated dictionary + regex pass (method=regex);
residue reported for an optional one-time build-time Claude pass (method=llm), gated.
No runtime LLM. `inhouse` is a VALUE (build-vs-buy); "not disclosed" is legitimate — never infer.

Output data/vendors.csv: {row_id, vendor, vendor_type, source_phrase, method}
    python3 scripts/extract_vendors.py
"""
import csv, re, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")
OUT  = os.path.join(ROOT, "data", "vendors.csv")

# canonical vendor -> (type, [aliases/regex]). type: model|cloud|platform|integrator|inhouse
VENDORS = [
    ("OpenAI","model",[r"openai", r"chatgpt", r"gpt-?4", r"gpt-?5", r"\bgpt\b"]),
    ("Anthropic","model",[r"anthropic", r"\bclaude\b"]),
    ("Google","model",[r"\bgemini\b", r"\bbard\b", r"vertex ai", r"deepmind"]),
    ("Meta","model",[r"\bllama\b", r"\bmeta ai"]),
    ("Mistral AI","model",[r"mistral"]),
    ("Cohere","model",[r"cohere"]),
    ("DeepSeek","model",[r"deepseek"]),
    ("Microsoft","platform",[r"microsoft", r"copilot", r"m365", r"office 365"]),
    ("Microsoft Azure","cloud",[r"\bazure\b"]),
    ("Amazon AWS","cloud",[r"\baws\b", r"amazon web services", r"bedrock", r"sagemaker"]),
    ("Google Cloud","cloud",[r"google cloud", r"\bgcp\b"]),
    ("NVIDIA","platform",[r"nvidia", r"\bcuda\b", r"\bdgx\b"]),
    ("IBM","platform",[r"\bibm\b", r"watson"]),
    ("Salesforce","platform",[r"salesforce", r"agentforce", r"einstein"]),
    ("SAP","platform",[r"\bsap\b"]),
    ("Databricks","platform",[r"databricks"]),
    ("Snowflake","platform",[r"snowflake"]),
    ("Palantir","platform",[r"palantir", r"foundry"]),
    ("Oracle","platform",[r"oracle"]),
    ("ServiceNow","platform",[r"servicenow"]),
    ("C3.ai","platform",[r"c3\.ai", r"c3 ai"]),
    ("Accenture","integrator",[r"accenture"]),
    ("Deloitte","integrator",[r"deloitte"]),
    ("Capgemini","integrator",[r"capgemini"]),
    ("Cognizant","integrator",[r"cognizant"]),
    ("TCS","integrator",[r"\btcs\b", r"tata consultancy"]),
    ("Infosys","integrator",[r"infosys"]),
    ("Kyndryl","integrator",[r"kyndryl"]),
    ("Alibaba Cloud","cloud",[r"alibaba cloud", r"aliyun"]),
    ("Tencent Cloud","cloud",[r"tencent cloud"]),
    ("Baidu","model",[r"baidu", r"ernie"]),
]
INHOUSE = re.compile(r"proprietary|in-house|in house|own model|own llm|homegrown|built its own|self-developed|internally developed|own ai model|own large", re.I)

rows = list(csv.reader(open(REG)))[1:]
out, tagged, residue = [], set(), []
for i, r in enumerate(rows):
    use = r[5] or ""
    hits = []
    for name, vtype, pats in VENDORS:
        for p in pats:
            m = re.search(p, use, re.I)
            if m:
                s=max(0,m.start()-15); e=min(len(use),m.end()+15)
                hits.append((name, vtype, use[s:e].strip())); break
    if INHOUSE.search(use):
        m=INHOUSE.search(use); s=max(0,m.start()-15); e=min(len(use),m.end()+20)
        hits.append(("(in-house)","inhouse", use[s:e].strip()))
    # dedupe by vendor name
    seen=set()
    for name,vtype,phrase in hits:
        if name in seen: continue
        seen.add(name); tagged.add(i)
        out.append([i,name,vtype,phrase,"regex"])
    if not hits: residue.append((i,use[:80]))

with open(OUT,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["row_id","vendor","vendor_type","source_phrase","method"]); w.writerows(out)
cov=round(100*len(tagged)/len(rows))
print(f"vendors.csv: {len(out)} vendor tags across {len(tagged)}/{len(rows)} rows ({cov}%) -> {OUT}")
print("  by type:", dict(Counter(o[2] for o in out)))
print("  top vendors:", Counter(o[1] for o in out).most_common(12))
print(f"  residue (no vendor named — a legitimate frequent outcome): {len(residue)}")
