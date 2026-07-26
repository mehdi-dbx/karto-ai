#!/usr/bin/env python3
"""vendor_customers.py — reverse (vendor -> customers) discovery, near-zero tokens.

The forward sweep asked "for company X, which vendors?" — one search per company.
This flips it: one vendor's customer/case-study pages name DOZENS of companies at
once. Discovery is pure string-matching the known KARTO universe against fetched
page text — NO model tokens. Serper (paid HTTP, ~$0.001/query) + local fetch only.

Precision design (validated on Anthropic, ~zero false positives):
  - match FULL distinctive company names; a suffix-stripped core is kept only if it
    stays >=2 words / >=8 chars (so "Regional S.A.B." never degrades to "regional").
  - a GENERIC stoplist kills ambiguous single words (Meta, Block, Next, 3M, ...).
  - a company counts as an edge only if its name appears in the Serper SNIPPET
    (where the vendor is already the query context) OR sits within ~160 chars of a
    signal word (vendor name / "customer" / "case study" / "using" ...) in the body.
  - edges with >=2 independent source pages are flagged high-confidence.

Evidence honesty: a name on a vendor page is thin — rows are written
existence="claimed" with use_case "Named as a <vendor> customer/case study", and a
real source_url. Never upgraded to confirmed here; the forward sweep / manual review
does that. Output is the standard staging shape for resweep_to_staging.py.

Usage:
  python3 scripts/vendor_customers.py --only Anthropic          # test one
  python3 scripts/vendor_customers.py --out staging/vendor_customers.json   # all
"""
import argparse, json, os, re, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_local import serper, fetch_trim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG  = os.path.join(ROOT, "data", "register.csv")

# vendor -> (canonical tag, [search queries], signal-word regex fragment)
VENDORS = {
    "Anthropic": ("Anthropic Claude",
        ['Anthropic Claude enterprise customers', 'Anthropic customer case studies list',
         '"uses Claude" OR "using Claude" company enterprise',
         'Anthropic Claude business customers 2025', 'companies deploying Anthropic Claude'],
        r"claude|anthropic"),
    "OpenAI": ("OpenAI",
        ['OpenAI ChatGPT Enterprise customers list', 'OpenAI enterprise customer case studies',
         '"uses ChatGPT Enterprise" company', 'companies using OpenAI GPT enterprise 2025',
         'OpenAI business customer stories'],
        r"openai|chatgpt|gpt-?[45]"),
    "Microsoft Copilot": ("Microsoft Copilot",
        ['Microsoft 365 Copilot enterprise customers list', 'Microsoft Copilot customer case studies',
         '"deployed Microsoft 365 Copilot" company', 'companies using Microsoft Copilot 2025',
         'Microsoft Copilot customer stories enterprise'],
        r"copilot|microsoft 365"),
    "AWS Bedrock": ("Amazon Bedrock",
        ['Amazon Bedrock customers list', 'AWS Bedrock generative AI customer case studies',
         '"using Amazon Bedrock" company enterprise', 'companies deploying AWS Bedrock 2025',
         'AWS Bedrock customer stories'],
        r"bedrock|aws|amazon"),
    "Google Vertex/Gemini": ("Google Gemini / Vertex AI",
        ['Google Gemini Enterprise customers list', 'Google Vertex AI customer case studies',
         '"using Gemini" OR "Vertex AI" company enterprise', 'companies deploying Google Gemini 2025',
         'Google Cloud generative AI customer stories'],
        r"gemini|vertex ai|google cloud"),
    "Databricks": ("Databricks",
        ['Databricks AI customers list', 'Databricks customer case studies generative AI',
         '"using Databricks" company enterprise AI', 'companies deploying Databricks Mosaic AI 2025',
         'Databricks customer stories'],
        r"databricks|mosaic"),
    "Palantir": ("Palantir",
        ['Palantir AIP customers list', 'Palantir Foundry customer case studies',
         '"using Palantir" company enterprise', 'companies deploying Palantir AIP 2025',
         'Palantir customer stories commercial'],
        r"palantir|foundry|aip"),
    "Cohere": ("Cohere",
        ['Cohere enterprise customers list', 'Cohere customer case studies',
         '"using Cohere" company enterprise', 'companies deploying Cohere 2025'],
        r"cohere"),
}

SUFFIX = re.compile(r"\b(corp|corporation|company|co|inc|incorporated|group|holdings?|ltd|limited|plc|ag|sa|s\.a\.b?\.?|nv|se|the)\b\.?", re.I)
GENERIC = {"regional","shift","partners","kingdom","holding","holdings","global","first",
           "general","national","international","total","east","west","united","air","meta",
           "block","next","3m","sap","google","microsoft","oracle","ibm","amazon","apple",
           "intel","adobe","nvidia","salesforce","oracle","the","co","ai","sk","lg","gs","nc"}
# single-word company names that are ALSO common English words — a bare-word match is
# unreliable (hit "discovery"/"compass"/"phoenix" as ordinary text on vendor pages).
# These require the FULL registered name (incl. suffix) to count, never the bare word.
COMMON_WORD = {"discovery","compass","evolution","phoenix","booking","corning","humana",
               "workday","fiserv","westpac","swedbank","broadcom","target","block","next",
               "orange","total","corpay","assurant","aflac","centene","paccar","entergy",
               "halma","diploma","informa","experian","admiral","segro","nucor","ptc"}

def tokens_for(co):
    toks = set(); full = co.lower().strip()
    # a single-word name that is itself a common English word (Discovery, Compass, Orange,
    # Target...) is NOT matchable by name alone — it hits ordinary text on vendor pages.
    # Drop it unless the registered name is multi-word (e.g. "Warner Bros. Discovery").
    if len(full) >= 6 and not (len(full.split()) == 1 and full in COMMON_WORD):
        toks.add(full)
    core = SUFFIX.sub("", co).strip(" .,&").lower()
    if core and core != full:
        nw = len(core.split())
        if nw >= 2 and len(core) >= 8: toks.add(core)
        # single-word core: keep only if long, non-generic, AND not a common English word
        elif nw == 1 and len(core) >= 7 and core not in GENERIC and core not in COMMON_WORD:
            toks.add(core)
    return {t for t in toks if t not in GENERIC}

def load_universe():
    uni = {}
    r = csv.reader(open(REG)); next(r)
    for row in r:
        if len(row) < 3: continue
        for t in tokens_for(row[0]):
            uni.setdefault(t, (row[0], row[1], row[2]))
    return uni

def discover(tag, queries, sigfrag, uni, fetchcap=12000):
    signal = re.compile(sigfrag + r"|customer|case stud|deploy|using|adopt|powered by|built with", re.I)
    def prox(body, tok, win=160):
        for m in re.finditer(r"\b" + re.escape(tok) + r"\b", body):
            s = max(0, m.start()-win); e = min(len(body), m.end()+win)
            if signal.search(body[s:e]): return True
        return False
    seen = set(); pages = []
    for q in queries:
        for h in serper(q, num=10):
            if h["link"] and h["link"] not in seen:
                seen.add(h["link"]); pages.append(h)
    edges = {}
    for h in pages:
        snip = (h.get("title","") + " " + h.get("snippet","")).lower()
        full = fetch_trim(h["link"], cap=fetchcap).lower()
        for tok, (co, cc, vert) in uni.items():
            if re.search(r"\b"+re.escape(tok)+r"\b", snip) or prox(full, tok):
                edges.setdefault((co, cc, vert), {}).setdefault("urls", set()).add(h["link"])
    return edges

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="run a single vendor key")
    ap.add_argument("--min-src", type=int, default=1, help="min source pages to keep an edge")
    ap.add_argument("--out", default=os.path.join(ROOT, "staging", "vendor_customers.json"))
    args = ap.parse_args()

    uni = load_universe()
    print(f"universe match-tokens: {len(uni)}")
    vendors = {args.only: VENDORS[args.only]} if args.only else VENDORS

    comps = {}       # (company,cc) -> staging entry (canonical source_url each)
    evidence = []    # every (company,cc,vendor,source_url) edge — full traceability sidecar
    report = {}
    for vk, (tag, queries, sigfrag) in vendors.items():
        edges = discover(tag, queries, sigfrag, uni)
        kept = {k: v for k, v in edges.items() if len(v["urls"]) >= args.min_src}
        report[vk] = (len(edges), len(kept))
        print(f"\n{vk}: {len(edges)} edges ({sum(1 for v in edges.values() if len(v['urls'])>=2)} multi-src), keeping {len(kept)}")
        for (co, cc, vert), v in sorted(kept.items(), key=lambda x: -len(x[1]["urls"])):
            urls = sorted(v["urls"]); multi = len(urls) >= 2
            e = comps.setdefault((co, cc), {"company": co, "cc": cc, "vertical": vert, "rows": []})
            e["rows"].append({
                "use_case": f"Named as a {tag} customer/case study [{tag}]",
                "horizontal": "",
                "existence": "confirmed" if multi else "claimed",
                "value_claimed": "none",
                "vendor": tag,
                "source_url": urls[0],           # canonical link for the register row
                "date": "missing",
            })
            for u in urls:                       # ALL links preserved in the evidence sidecar
                evidence.append([co, cc, tag, "confirmed" if multi else "claimed", len(urls), u])
            print(f"   {'**' if multi else '  '} {co} ({cc})  {len(urls)}src")

    json.dump({"companies": list(comps.values())}, open(args.out, "w"), indent=1)
    # traceability sidecar: one row per (company, vendor, source) — every Serper link kept
    ev_path = os.path.join(ROOT, "staging", "vendor_evidence.csv")
    with open(ev_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "country", "vendor", "confidence", "n_sources", "source_url"])
        w.writerows(evidence)
    nrows = sum(len(c["rows"]) for c in comps.values())
    print(f"\nwrote {args.out}: {len(comps)} companies, {nrows} vendor-customer rows")
    print(f"wrote {ev_path}: {len(evidence)} evidence edges (all source links preserved)")
    print("per-vendor (edges, kept):", report)

if __name__ == "__main__":
    main()
