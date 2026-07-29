#!/usr/bin/env python3
"""rundiff_nation.py — detect sampling-noise churn between harvest runs.

Adversarial review item #4 (not optional): the harvest is non-deterministic
(Serper + Gemini vary run-to-run). Enum values flip between runs with NO change
in the world — US procurement offset-localization<->open-tender, JP/IN military
active<->stated — same inputs, different outputs, i.e. sampling noise presented
as measurement. At 10 countries you catch it by eye; at 89 you never will.

This tool diffs a new facts file against a saved snapshot and flags any field
whose VALUE changed while its SOURCE_URL did NOT — that combination is the
signature of noise (a real update would bring a new source). A value change that
comes with a new source is legitimate and reported separately (info, not alarm).

Usage:
  # save a baseline after a run you trust:
  python3 scripts/rundiff_nation.py --snapshot data/nation-facts.json --save data/.nation-snapshot.json
  # after the next run, diff against it:
  python3 scripts/rundiff_nation.py --in data/nation-facts.json --against data/.nation-snapshot.json
"""
import argparse, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# scalar single-metric fields worth watching for churn
WATCH = ["procurement_access", "compute_band", "compute_control", "chip_regime",
         "power_posture", "national_champion", "military_ai", "ethics_stance"]


def _mv(f, k):
    m = f.get(k)
    if isinstance(m, dict):
        return m.get("value"), m.get("source_url")
    return None, None


def index(doc):
    out = {}
    for r in doc.get("records", []):
        out[r.get("iso3") or r.get("iso2")] = r.get("facts", {})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--against")
    ap.add_argument("--snapshot")
    ap.add_argument("--save")
    args = ap.parse_args()

    if args.snapshot and args.save:
        doc = json.load(open(os.path.join(ROOT, args.snapshot)))
        json.dump(doc, open(os.path.join(ROOT, args.save), "w"), indent=2, ensure_ascii=False)
        print(f"snapshot saved: {args.save}")
        return

    if not (args.inp and args.against):
        raise SystemExit("need --in and --against (or --snapshot/--save)")
    new = index(json.load(open(os.path.join(ROOT, args.inp))))
    old = index(json.load(open(os.path.join(ROOT, args.against))))

    noise, legit, gained, lost = [], [], [], []
    for iso, nf in new.items():
        of = old.get(iso)
        if of is None:
            continue
        for k in WATCH:
            nv, nu = _mv(nf, k)
            ov, ou = _mv(of, k)
            if nv == ov:
                continue
            # value changed
            if nu == ou:
                noise.append(f"{iso}.{k}: {ov!r} -> {nv!r}  (SAME source — noise)")
            elif ov not in (None, "unknown") and nv in (None, "unknown"):
                lost.append(f"{iso}.{k}: {ov!r} -> {nv!r}  (lost a value)")
            elif ov in (None, "unknown") and nv not in (None, "unknown"):
                gained.append(f"{iso}.{k}: {ov!r} -> {nv!r}  (gained a value)")
            else:
                legit.append(f"{iso}.{k}: {ov!r} -> {nv!r}  (new source — likely real)")

    def _sec(title, rows):
        print(f"\n=== {title} ({len(rows)}) ===")
        for r in rows:
            print("  " + r)

    print(f"run-diff: {len(new)} records vs snapshot of {len(old)}")
    _sec("CHURN — value changed, SAME source (sampling noise — review)", noise)
    _sec("LOST — had a value, now unknown", lost)
    _sec("GAINED — was unknown, now has a value", gained)
    _sec("CHANGED with new source (likely real)", legit)
    print(f"\nsummary: {len(noise)} noise, {len(lost)} lost, {len(gained)} gained, {len(legit)} sourced-change")
    if noise:
        print("!! noise > 0: these fields flipped without new evidence — treat values as low-confidence.")


if __name__ == "__main__":
    main()
