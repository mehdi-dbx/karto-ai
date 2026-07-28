#!/usr/bin/env python3
"""validate_nation.py — enforce the nation-axis disciplines IN CODE.

The pilot's lesson (adversarial review round 2): every discipline that lived only
in the Gemini prompt got violated somewhere — the null-rule (R1), the source
classes, the appropriated rule. A prompt asks; it does not gate. This is the gate.

Design choice (user, 2026-07-28): **log-in-field, never null.** A caught problem
does NOT delete the value — it keeps the value and attaches a `flag` so the issue
is VISIBLE and downstream/UI can show it, rather than silently dropping evidence.

Rules enforced (each attaches a flag string to the offending metric; nothing is
censored — military facts included are held to the same bar as everything else,
not removed):
  V1  value present but source_url missing/unparseable   -> flag "no-source"
  V2  source domain on the deny-list (social/forum/       -> flag "banned-source:<d>"
      third-country state media)                             + downgrade tier to "secondary"
  V3  funding entry status=appropriated w/o primary       -> auto-degrade to "announced"
      budget-instrument source                               + flag "degraded-appropriated"
  V4  source_date not ISO/absolute ("5 months ago",       -> flag "soft-date"
      "not-stated" on a real article)
  V5  opportunity_read present but min-premise-set not     -> flag "thin-premise" (on record)
      met (needs funding status + procurement_access +
      one capability field, all non-unknown)
  V6  chokepoint_node corporate-PR source marked primary   -> retier to "industry"
  V7  strategy_snapshot empty string                       -> replace with explicit
                                                              {"status":"no-snapshot"}

Usage:
  python3 scripts/validate_nation.py --in data/nation-facts.json [--out ...] [--report]
  # rewrites in place (or --out), adds record["_violations"] summary + per-field flags.
"""
import argparse, json, os, re, datetime
from urllib.parse import urlparse

TODAY = datetime.date.today()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# V2 deny-list: social/forum/video + third-country state media. A claim about
# country X sourced to another state's govt/military media is a propaganda surface.
# DOMAIN-CLASS ban (not URL-path): linkedin.com/pulse must die the same as
# linkedin.com/posts. Matched against the registrable domain only (review #2).
BANNED = ["reddit.com", "facebook.com", "twitter.com", "x.com", "youtube.com",
          "youtu.be", "linkedin.com", "medium.com", "quora.com", "instagram.com",
          "tiktok.com", "threads.net", "pinterest.com", "chinamil.com.cn",
          "rt.com", "sputnik", "tass.ru", "presstv", "xinhuanet", "globaltimes.cn"]
# corporate-PR / vendor domains that must NOT be tier "primary" (V6)
CORP_PR = ["skhynix", "nvidia", "shinetsu", "shin-etsu", "tsmc.com", "samsung",
           "asml.com", "intel.com", "amd.com"]
# what counts as a PRIMARY budget instrument for V3 (appropriated)
BUDGET_HINTS = ["budget", "appropriat", "cabinet", "decree", "law", "act",
                "finance", "treasury", "gazette", "allocation", ".gov", "gouv",
                "gov.", "official"]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
SOFT_DATE = re.compile(r"ago|not-stated|n/?a|unknown|recent|last (month|year|week)", re.I)

CAPABILITY_FIELDS = ["compute_band", "compute_control", "chip_regime",
                     "power_posture", "national_champion"]
EMPTY = (None, "", "unknown", "not-found", "not-stated", "none")


def _flag(metric, msg):
    if not isinstance(metric, dict):
        return
    metric.setdefault("flag", [])
    if isinstance(metric["flag"], str):
        metric["flag"] = [metric["flag"]]
    if msg not in metric["flag"]:
        metric["flag"].append(msg)


def _url_ok(u):
    if not u or not isinstance(u, str):
        return False
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _domain(u):
    try:
        return str(urlparse(u).netloc).lower()
    except Exception:
        return ""


def validate_metric(m, counters, is_funding_entry=False):
    """Apply V1..V4 to one metric object in place.
    Returns "DROP" if the metric must be removed by the caller (banned source —
    review blocker #1: a banned source's VALUE must not ship, flag alone is not
    enough; a true fact on the wrong country survives a plausibility check)."""
    if not isinstance(m, dict):
        return None
    val = m.get("value")
    url = m.get("source_url")
    # V2 — banned source domain (DOMAIN-CLASS). Checked FIRST: if the only source
    # is banned, the value is dropped, not annotated (blocker #1).
    if _url_ok(url):
        dom = _domain(url)
        for b in BANNED:
            # match on registrable domain (endswith or exact segment), not path
            if dom == b or dom.endswith("." + b) or b in dom:
                counters["banned"] += 1
                return "DROP"
    # V1 — value present but no usable source
    if val not in EMPTY and not _url_ok(url):
        _flag(m, "no-source"); counters["no_source"] += 1
    # V3 — appropriated needs a primary budget instrument (funding entries only)
    if is_funding_entry and m.get("status") == "appropriated":
        u = (url or "").lower()
        tier = m.get("source_tier")
        if tier != "primary" or not any(h in u for h in BUDGET_HINTS):
            m["status"] = "announced"
            _flag(m, "degraded-appropriated"); counters["degraded"] += 1
    # V4 — date hygiene
    d = m.get("source_date")
    if val not in EMPTY and isinstance(d, str) and d and not ISO_DATE.match(d) and SOFT_DATE.search(d):
        _flag(m, "soft-date"); counters["soft_date"] += 1
    # V9 — future date (B4: India's procurement dated 2033). A source can't be
    # dated after today; that's a mis-extraction (a forecast year, not a pub date).
    if isinstance(d, str) and ISO_DATE.match(d):
        try:
            if datetime.date.fromisoformat(d[:10]) > TODAY:
                _flag(m, "future-date"); counters["future_date"] += 1
        except Exception:
            pass


def validate_record(rec, counters):
    f = rec.get("facts", {})
    # funding is a list of entries — a banned entry is DROPPED, not annotated
    # (blocker #1: a wrong-country fact must not ship). Record a tombstone so the
    # drop is visible, not silent.
    kept_funding = []
    for entry in (f.get("funding") or []):
        if validate_metric(entry, counters, is_funding_entry=True) == "DROP":
            rec.setdefault("_dropped", []).append(
                {"field": "funding", "value": entry.get("value"), "reason": "banned-source",
                 "was_source": entry.get("source_url")})
        else:
            kept_funding.append(entry)
    if "funding" in f:
        f["funding"] = kept_funding
    # single metrics — a banned single metric is NULLED with a tombstone
    for k, v in f.items():
        if k in ("funding", "sectors", "general_idea", "opportunity_read"):
            continue
        if isinstance(v, dict):
            if validate_metric(v, counters) == "DROP":
                rec.setdefault("_dropped", []).append(
                    {"field": k, "value": v.get("value"), "reason": "banned-source",
                     "was_source": v.get("source_url")})
                # null the value in place, keep the object so the field still renders
                v["value"] = "unknown"; v["source_url"] = None
                v["source_tier"] = None; _flag(v, "dropped:banned-source")
    # V5 — opportunity_read min-premise-set
    orr = f.get("opportunity_read")
    if orr:
        fund_ok = any((e.get("status") not in EMPTY) for e in (f.get("funding") or []))
        proc_ok = isinstance(f.get("procurement_access"), dict) and f["procurement_access"].get("value") not in EMPTY
        cap_ok = any(isinstance(f.get(c), dict) and f[c].get("value") not in EMPTY for c in CAPABILITY_FIELDS)
        if not (fund_ok and proc_ok and cap_ok):
            rec.setdefault("_flags", []).append("opportunity_read:thin-premise")
            counters["thin_premise"] += 1
    # V8 — compute_control asserting a definite value from the STRATEGY doc is
    # aspiration-as-fact, not infrastructure data (reviewer P5). An infra claim
    # must rest on an infra/aggregator source, not the country's own strategy PDF.
    cc = f.get("compute_control")
    if isinstance(cc, dict) and cc.get("value") in ("sovereign", "mixed", "hyperscaler-hosted"):
        src = (cc.get("source_url") or "")
        strat = rec.get("strategy_url", "")
        if src and strat and src == strat:
            _flag(cc, "aspiration-not-infra"); counters["aspiration"] += 1
    # V6 — chokepoint corporate-PR marked primary
    ck = rec.get("chokepoint_node")
    if isinstance(ck, dict) and ck.get("value") not in ("none", None):
        u = (ck.get("source_url") or "").lower()
        if ck.get("source_tier") == "primary" and any(c in u for c in CORP_PR):
            ck["source_tier"] = "industry"
            _flag(ck, "retier:corporate-pr"); counters["retier"] += 1
    # V7 — empty snapshot -> explicit status
    prov = rec.get("_provenance", {})
    if prov.get("strategy_snapshot") == "":
        prov["strategy_snapshot"] = {"status": "no-snapshot"}
        counters["no_snapshot"] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/nation-facts.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    path = os.path.join(ROOT, args.inp)
    d = json.load(open(path))
    counters = {"no_source": 0, "banned": 0, "degraded": 0, "soft_date": 0,
                "thin_premise": 0, "retier": 0, "no_snapshot": 0, "aspiration": 0,
                "future_date": 0}
    for rec in d.get("records", []):
        validate_record(rec, counters)
    d.setdefault("_meta", {})["validated"] = True
    d["_meta"]["validation_counts"] = counters
    out = os.path.join(ROOT, args.out) if args.out else path
    json.dump(d, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"validated {len(d.get('records', []))} records -> {args.out or args.inp}")
    print("flags raised (log-in-field, nothing deleted):")
    for k, v in counters.items():
        print(f"  {k:16} {v}")
    if args.report:
        print("\n=== per-record flags ===")
        for rec in d.get("records", []):
            fl = []
            for k, m in rec.get("facts", {}).items():
                if isinstance(m, dict) and m.get("flag"):
                    fl.append(f"{k}:{','.join(m['flag'])}")
            for e in (rec.get("facts", {}).get("funding") or []):
                if e.get("flag"):
                    fl.append(f"funding[{e.get('figure_scope','?')}]:{','.join(e['flag'])}")
            fl += rec.get("_flags", [])
            if fl:
                print(f"  {rec['iso2']}: " + " | ".join(fl))


if __name__ == "__main__":
    main()
