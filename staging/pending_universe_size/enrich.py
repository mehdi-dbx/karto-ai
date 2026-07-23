#!/usr/bin/env python3
"""Enrich companies from stockanalysis.com. Reads company names from argv,
prints TAB-separated: company\tticker\tmarketcap\trevenue\temployees (raw ints, blank if missing)."""
import sys, re, json, urllib.request, urllib.parse, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

def get(url, retries=5):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(8 * (attempt + 1))  # 8,16,24,32s backoff
                continue
            raise
        except Exception:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise
    return ""

MULT = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}

def parse_num(s):
    """'87.67B' -> 87670000000 ; '25.18B' -> ..."""
    if not s: return ""
    s = s.strip().replace("$", "").replace(",", "")
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([TBMK])?$", s, re.I)
    if not m: return ""
    val = float(m.group(1))
    if m.group(2):
        val *= MULT[m.group(2).upper()]
    return str(int(round(val)))

def _search(q):
    try:
        d = json.loads(get("https://stockanalysis.com/api/search?q=" + urllib.parse.quote(q)))
        return d.get("data", [])
    except Exception:
        return []

SUFFIX = {"inc", "incorporated", "corp", "corporation", "company", "companies",
          "co", "plc", "ltd", "limited", "holdings", "holding", "group",
          "sa", "ag", "nv", "the", "lp", "llc", "class", "com", "of"}

def _norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def _core(s):
    return " ".join(t for t in _norm(s).split() if t not in SUFFIX)

# Known multi-class / ambiguous names where search can't distinguish by class
OVERRIDE = {
    "alphabet inc. (class a)": "GOOGL",
    "alphabet inc. (class c)": "GOOG",
    "fox corporation (class a)": "FOXA",
    "fox corporation (class b)": "FOX",
    "news corp (class a)": "NWSA",
    "news corp (class b)": "NWS",
    "berkshire hathaway": "BRK.B",
}

def resolve_ticker(name):
    """Return best-matching primary US ticker for a company name, or ''."""
    ov = OVERRIDE.get(name.strip().lower())
    if ov:
        return ov
    variants = [name]
    stripped = re.sub(r"[.,]", "", name).strip()
    if stripped != name:
        variants.append(stripped)
    variants.append(name + " Company")
    # collect primary-US candidates (type 's', no exchange slash)
    cand = {}  # ticker -> company name
    for q in variants:
        for x in _search(q):
            if x.get("t") == "s" and "/" not in x.get("s", ""):
                t = x["s"].upper()
                cand.setdefault(t, x.get("n", ""))
        if cand:
            break  # first variant that yields any candidate
    if not cand:
        return ""
    qcore = _core(name)
    qtok = set(qcore.split())

    def score(item):
        t, cn = item
        ccore = _core(cn)
        ctok = set(ccore.split())
        s = 0.0
        if ccore == qcore:
            s += 100
        elif ccore.startswith(qcore) or qcore.startswith(ccore):
            s += 50
        if qtok:
            s += 20 * len(qtok & ctok) / len(qtok)
        s -= 3 * max(0, len(ctok) - len(qtok))  # penalize extra distinctive words
        if "." in t:
            s -= 30  # prefer clean ticker over .A/.WI variants
        return s

    best = max(cand.items(), key=score)
    return best[0]

def fetch_stats(ticker):
    """Return (marketcap, revenue, employees) raw-int strings."""
    try:
        html = get("https://stockanalysis.com/stocks/%s/" % ticker.lower())
    except Exception:
        return "", "", ""
    mc = rv = emp = ""
    m = re.search(r'marketCap:"([^"]+)"', html)
    if m: mc = parse_num(m.group(1))
    m = re.search(r'revenue:"([^"]+)"', html)
    if m: rv = parse_num(m.group(1))
    m = re.search(r'\{t:"Employees",v:"([0-9,]+)"', html)
    if m: emp = m.group(1).replace(",", "")
    return mc, rv, emp

def main():
    for name in sys.argv[1:]:
        tk = resolve_ticker(name)
        mc = rv = emp = ""
        if tk:
            mc, rv, emp = fetch_stats(tk)
        print("\t".join([name, tk, mc, rv, emp]))
        sys.stdout.flush()
        time.sleep(0.3)

if __name__ == "__main__":
    main()
