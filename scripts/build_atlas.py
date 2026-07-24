#!/usr/bin/env python3
"""
KARTO Atlas builder — reads data/atlas.json, emits a standalone karto-atlas.html.
Self-contained (data embedded inline, no CDN). Regenerable: python3 scripts/build_atlas.py
Design: DASHBOARD-DESIGN.md. Palette: validated warm set (see that doc).

Build progresses altitude by altitude. Current: shell + A0 Orbit.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = os.path.join(ROOT, "data", "atlas.json")
OUT   = os.path.join(ROOT, "karto-atlas.html")
VENDOR = os.path.join(ROOT, "tools", "vendor")

import base64, glob
# V3 Step 6 path guard: warn loudly if a gate-managed table changed off-gate.
try:
    import subprocess as _sp
    _g = _sp.run([__import__("sys").executable, os.path.join(ROOT,"scripts","gate_guard.py"),"check"],
                 capture_output=True, text=True)
    if _g.returncode != 0: print("⚠ ", _g.stdout.strip() or _g.stderr.strip())
except Exception: pass

data = json.load(open(ATLAS))
DATA_JSON = json.dumps(data, ensure_ascii=False)

def font_face(family, weight, path, style="normal"):
    b64 = base64.b64encode(open(path,"rb").read()).decode()
    return (f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
_arch = glob.glob(os.path.join(VENDOR,"fonts","archivo-narrow-*.woff2"))
_serif = glob.glob(os.path.join(VENDOR,"fonts","source-serif-*.woff2"))
FONTS = ""
if _arch:  FONTS += font_face("Archivo Narrow","400 700",_arch[0])
if _serif: FONTS += font_face("Source Serif 4","400 600",_serif[0])
def img_data_uri(path):
    if not os.path.exists(path): return ""
    b64 = base64.b64encode(open(path,"rb").read()).decode()
    return f"data:image/png;base64,{b64}"
MEHDI_IMG = img_data_uri(os.path.join(VENDOR, "img", "mehdi.png"))

# ---- Lucide icons (monochrome stroke SVG, inherit currentColor -> theme-safe). No emoji. ----
# Uses the `lucide` PyPI package if importable; otherwise falls back to a committed cache
# (tools/vendor/lucide_cache.json) so the build is reproducible without the dep.
_LUCIDE_CACHE_PATH = os.path.join(VENDOR, "lucide_cache.json")
try:
    import lucide as _lucide
except Exception:
    _lucide = None
_lucide_cache = {}
if os.path.exists(_LUCIDE_CACHE_PATH):
    _lucide_cache = json.load(open(_LUCIDE_CACHE_PATH))
def _raw_icon(name, size):
    key = f"{name}:{size}"
    if key in _lucide_cache: return _lucide_cache[key]
    if _lucide is None:
        raise RuntimeError(f"lucide icon '{key}' not cached and lucide not importable — run build in the venv once to populate {_LUCIDE_CACHE_PATH}")
    svg = _lucide._render_icon(name, size)
    _lucide_cache[key] = svg
    return svg
def icon(name, size=18, cls="lic"):
    svg = _raw_icon(name, size)
    svg = svg.replace("<svg ", f'<svg class="{cls}" aria-hidden="true" focusable="false" ', 1)
    return " ".join(svg.split())
WORLD_JSON = open(os.path.join(ROOT, "data", "world-110m.json")).read()
QUESTIONS_JSON = open(os.path.join(ROOT, "data", "questions.json")).read()
_qs_path = os.path.join(ROOT, "data", "question_stats.json")
QSTATS_JSON = open(_qs_path).read() if os.path.exists(_qs_path) else "{}"
D3 = open(os.path.join(VENDOR, "d3.v7.min.js")).read()
TOPO = open(os.path.join(VENDOR, "topojson-client.min.js")).read()

g = data["global"]
g.setdefault("verticals", len(data["verticals"]))

# ---- helpers for A0 static render (progressive enhancement; works even if JS off) ----
def fmt(n): return f"{n:,}"

HTML = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KARTO Atlas — the current state of AI on Earth</title>
<meta name="description" content="A source-gated census of {fmt(g['deployments'])} AI deployments at {fmt(g['companies'])} of the world's largest listed companies across {g['countries']} countries. AI is deployed almost everywhere; evidence that it pays is scarce.">
<!-- Open Graph / Twitter share card -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="KARTO AI Atlas">
<meta property="og:title" content="KARTO Atlas — where AI is actually profitable">
<meta property="og:description" content="{fmt(g['deployments'])} named, source-linked AI deployments across {g['countries']} countries. Deployed almost everywhere; evidence it pays is scarce.">
<meta property="og:url" content="https://mehdi-dbx.github.io/karto-ai/">
<meta property="og:image" content="https://mehdi-dbx.github.io/karto-ai/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="KARTO Atlas — where AI is actually profitable">
<meta name="twitter:description" content="{fmt(g['deployments'])} named, source-linked AI deployments across {g['countries']} countries. Deployed almost everywhere; evidence it pays is scarce.">
<meta name="twitter:image" content="https://mehdi-dbx.github.io/karto-ai/og-card.png">
<style>
/* fonts: Archivo Narrow (headlines) + Source Serif 4 (body) — free, vendored, inlined.
   Closest open-license match to The Economist's condensed-grotesque + editorial-serif. */
{FONTS}
/* ============================================================
   KARTO Atlas — warm editorial cartography. Palette VALIDATED
   (validate_palette.js, light+dark). Do not alter hex without re-validating.
   ============================================================ */
:root {{
  --font-head: 'Archivo Narrow', system-ui, sans-serif;
  --font-body: 'Source Serif 4', Georgia, serif;
  --font-ui:   system-ui, -apple-system, "Segoe UI", sans-serif;
}}
:root, :root[data-theme="light"] {{
  color-scheme: light;
  --page:        #f4f0e6;
  --surface:     #faf7f0;
  --surface-2:   #f2ecdf;
  --ink:         #211d17;
  --ink-2:       #5c554a;
  --muted:       #8f8676;
  --grid:        #e7e1d3;
  --hair:        rgba(33,29,23,0.12);
  --land:        #e3dac2;         /* distinct warm tan — reads as land vs cream page */
  --land-edge:   #cdbf9f;
  --accent:      #bd7a26;         /* warm amber accent */
  --accent-soft: #e9d5b0;
  /* verdict status (always paired with glyph+label) */
  --v-strong:    #0ca30c;
  --v-active:    #b8820f;         /* amber, darkened for text legibility on cream */
  --v-unquantified: #5a7d99;      /* slate-blue: real activity, no numbers (distinct from red hype) */
  --v-talk:      #cf6b2f;          /* coral-orange: claimed, not confirmed — caution, not alarm */
  --v-empty:     #cfc7b5;
  /* sequential density ramp (light) */
  --d1:#f2ecdf; --d2:#dba85f; --d3:#cc9040; --d4:#bd7a26; --d5:#a4641b; --d6:#854c12; --d7:#6d3c09;
  --shadow: 0 1px 0 var(--hair);
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --page:        #141210;
  --surface:     #1c1a17;
  --surface-2:   #24211c;
  --ink:         #f5f1e8;
  --ink-2:       #c9c2b3;
  --muted:       #8f8676;
  --grid:        #302c26;
  --hair:        rgba(245,241,232,0.12);
  --land:        #34302a;         /* lifted warm grey — reads as land vs warm-dark page */
  --land-edge:   #454037;
  --accent:      #e0b06a;
  --accent-soft: #4a3c26;
  --v-strong:    #2fb62f;
  --v-active:    #fab219;
  --v-unquantified: #7fa6c4;      /* slate-blue, lifted for dark surface */
  --v-talk:      #e6934f;          /* coral-orange, lifted for dark surface */
  --v-empty:     #3a352d;
  --d1:#24211c; --d2:#9c5312; --d3:#b06a1c; --d4:#cc8a38; --d5:#e0b06a; --d6:#f0d4a0; --d7:#f0d4a0;
}}

.lic {{ display:inline-block; vertical-align:-.16em; width:1em; height:1em; stroke-width:2; flex:none; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  background: var(--page);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 16px; line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  transition: background .35s ease, color .35s ease;
}}
/* headlines & big figures = condensed grotesque; controls/tables/tooltip = crisp UI sans */
h1, h2, .brand, .hero .num, .kpi .num, .orbit .eyebrow {{ font-family: var(--font-head); }}
.topbar, .toggle, .seg-ctrl, .tip, .tabletwin, .legend, .crumbs, .descend {{ font-family: var(--font-ui); }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* ---- top chrome: breadcrumb + theme toggle ---- */
.topbar {{
  position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px clamp(20px, 5vw, 64px);
  background: color-mix(in srgb, var(--page) 88%, transparent);
  backdrop-filter: saturate(1.1) blur(6px);
  border-bottom: 1px solid var(--hair);
}}
.brand {{ font-weight: 620; letter-spacing: .14em; font-size: 13px; text-transform: uppercase; color: var(--ink-2); }}
.brand b {{ color: var(--ink); }}
.crumbs {{ font-size: 13px; color: var(--muted); display: flex; gap: 8px; align-items: center; }}
.crumbs .sep {{ opacity: .5; }}
.crumbs .here {{ color: var(--ink); }}
.topnav {{ display: flex; align-items: center; gap: 16px; }}
.navlink {{ font-family: var(--font-ui); font-size: 12.5px; color: var(--ink-2); text-decoration: none; letter-spacing: .02em; white-space: nowrap; }}
.navlink:hover {{ color: var(--accent); text-decoration: none; }}
.navlink.on {{ color: var(--ink); font-weight: 560; }}
/* global company omnibox (jump-to-company from anywhere) */
.omni-wrap {{ position: relative; }}
.omni-box {{ display: flex; align-items: center; gap: 6px; padding: 5px 9px; border: 1px solid var(--hair);
  border-radius: 8px; background: var(--surface); color: var(--muted); transition: border-color .15s; }}
.omni-box:focus-within {{ border-color: var(--accent); color: var(--ink-2); }}
.omni-box input {{ border: 0; outline: 0; background: transparent; font-family: var(--font-ui); font-size: 12.5px;
  color: var(--ink); width: 150px; }}
.omni-box input::placeholder {{ color: var(--muted); }}
.omni-results {{ position: absolute; top: calc(100% + 6px); right: 0; width: 340px; max-height: 60vh; overflow-y: auto;
  background: var(--surface); border: 1px solid var(--hair); border-radius: 10px; box-shadow: 0 12px 32px rgba(0,0,0,.18);
  z-index: 40; display: none; }}
.omni-results.open {{ display: block; }}
.omni-opt {{ display: flex; align-items: baseline; gap: 8px; padding: 9px 12px; cursor: pointer; border-bottom: 1px solid var(--hair); }}
.omni-opt:last-child {{ border-bottom: 0; }}
.omni-opt:hover, .omni-opt.active {{ background: color-mix(in srgb, var(--accent) 9%, var(--surface)); }}
.omni-opt .on {{ font-family: var(--font-body); font-size: 13.5px; color: var(--ink); }}
.omni-opt .om {{ font-family: var(--font-ui); font-size: 11.5px; color: var(--muted); margin-left: auto; white-space: nowrap; }}
.omni-opt .osilent {{ font-family: var(--font-ui); font-size: 10.5px; color: var(--muted); border: 1px solid var(--hair);
  border-radius: 5px; padding: 1px 5px; }}
.omni-empty {{ padding: 12px; font-family: var(--font-ui); font-size: 12.5px; color: var(--muted); }}
.filtersel {{ font-family: var(--font-ui); font-size: 12.5px; color: var(--ink); background: var(--surface);
  border: 1px solid var(--hair); border-radius: 8px; padding: 6px 10px; cursor: pointer; }}
.filtersel:hover {{ border-color: var(--muted); }}
/* D6 hype bars: announced (pale) with substantiated (accent) overlaid */
.hyperow {{ display:grid; grid-template-columns:190px 1fr 62px; align-items:center; gap:14px; padding:5px 0; }}
.hypetrack {{ position:relative; height:22px; }}
.hypebar {{ position:absolute; left:0; top:0; height:22px; border-radius:0 4px 4px 0; transition:width .5s cubic-bezier(.2,.7,.2,1); }}
.hypebar.announced {{ background:var(--accent-soft); }}
.hypebar.substant {{ background:var(--accent); }}
.hypebar.substant.warn {{ background:var(--v-talk); }}
.hypekey {{ display:flex; gap:22px; margin-top:16px; font-family:var(--font-ui); font-size:12px; color:var(--muted); }}
.hypekey i {{ display:inline-block; width:13px; height:13px; border-radius:3px; vertical-align:-2px; margin-right:6px; }}
.hypekey .sw-ann {{ background:var(--accent-soft); }} .hypekey .sw-sub {{ background:var(--accent); }}
.trendwrap {{ margin-top:20px; }} #trendsvg {{ width:100%; height:auto; display:block; }}
/* D1 company page */
.cprofile {{ display:flex; align-items:flex-start; justify-content:space-between; gap:20px; flex-wrap:wrap; margin-top:8px; }}
.mbadge {{ font-family:var(--font-ui); font-size:13px; font-weight:560; padding:8px 14px; border-radius:999px; white-space:nowrap; }}
.m-L0 {{ background:var(--surface-2); color:var(--muted); }}
.m-L1 {{ background:color-mix(in srgb,var(--v-talk) 16%,var(--surface)); color:var(--v-talk); }}
.m-L2 {{ background:color-mix(in srgb,var(--v-unquantified) 20%,var(--surface)); color:var(--v-unquantified); }}
.m-L3 {{ background:color-mix(in srgb,var(--v-active) 22%,var(--surface)); color:var(--v-active); }}
.m-L4 {{ background:color-mix(in srgb,var(--v-strong) 22%,var(--surface)); color:var(--v-strong); }}
.ckpis {{ display:flex; flex-wrap:wrap; gap:clamp(20px,4vw,52px); margin:26px 0 8px; }}
.ckpi .n {{ font-family:var(--font-head); font-size:32px; font-weight:340; letter-spacing:-.02em; }}
.ckpi .l {{ font-size:12px; color:var(--muted); margin-top:3px; }}
.csub {{ font-family:var(--font-head); font-weight:400; font-size:19px; margin:34px 0 14px; letter-spacing:-.01em; }}
.benchbox {{ max-width:520px; }}
.benchrow {{ display:grid; grid-template-columns:110px 1fr 44px; align-items:center; gap:12px; padding:5px 0; font-family:var(--font-ui); font-size:12.5px; color:var(--ink-2); }}
.benchtrack {{ height:16px; background:var(--surface-2); border-radius:8px; overflow:hidden; }}
.benchfill {{ height:16px; background:var(--accent); border-radius:8px; transition:width .5s cubic-bezier(.2,.7,.2,1); }}
.benchrow b {{ font-variant-numeric:tabular-nums; color:var(--ink); }}
.cdeps .co {{ padding:14px 0; }}
.cflags {{ display:flex; flex-direction:column; gap:10px; }}
.cflag {{ font-size:13px; color:var(--ink-2); line-height:1.5; padding:10px 14px; background:color-mix(in srgb,var(--v-talk) 8%,var(--surface)); border-radius:8px; border:1px solid var(--hair); }}
/* C1/D2 compare */
.cmp-pick {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-top:20px; }}
.cmp-chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
.cmp-chip {{ font-family:var(--font-ui); font-size:12.5px; background:var(--surface-2); border:1px solid var(--hair); border-radius:999px; padding:5px 12px; }}
.cmp-chip b {{ cursor:pointer; color:var(--muted); margin-left:6px; }} .cmp-chip b:hover {{ color:var(--v-talk); }}
.cmp-suggest {{ position:relative; }}
.cmp-opt {{ font-family:var(--font-ui); font-size:13px; padding:8px 12px; cursor:pointer; border-bottom:1px solid var(--hair); }}
.cmp-opt:hover {{ background:var(--surface-2); color:var(--accent); }}
#cmpTable {{ width:100%; border-collapse:collapse; margin-top:8px; }}
#cmpTable th, #cmpTable td {{ text-align:left; padding:9px 14px; border-bottom:1px solid var(--hair); font-size:13.5px; font-family:var(--font-ui); }}
#cmpTable th:first-child, #cmpTable td:first-child {{ color:var(--muted); }}
#cmpTable td.cmp-best {{ color:var(--v-strong); font-weight:600; }}
/* D2 — visual compare: overlaid radar (each company = one shape) */
.cmp-visual {{ margin-top:22px; display:flex; flex-wrap:wrap; gap:28px; align-items:flex-start; }}
.cmp-radar {{ flex:1 1 380px; max-width:520px; }}
.cmp-radar svg {{ width:100%; height:auto; overflow:visible; }}
.cmp-side {{ flex:0 1 260px; display:flex; flex-direction:column; gap:16px; }}
.cmp-legend {{ display:flex; flex-direction:column; gap:8px; font-family:var(--font-ui); font-size:13px; }}
.cmp-legend .k {{ display:flex; align-items:center; gap:9px; color:var(--ink-2); }}
.cmp-legend .k a {{ color:var(--ink-2); }} .cmp-legend .k a:hover {{ color:var(--accent); }}
.cmp-legend .sw {{ width:15px; height:15px; border-radius:4px; flex:none; }}
.cmp-note {{ font-family:var(--font-ui); font-size:11.5px; color:var(--muted); line-height:1.5; }}
.cmp-tags {{ display:flex; flex-wrap:wrap; gap:6px; }}
.cmp-tag {{ font-family:var(--font-ui); font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid var(--hair); color:var(--ink-2); background:var(--surface); }}
.radar-axis {{ stroke:var(--hair); stroke-width:1; }}
.radar-ring {{ fill:none; stroke:var(--hair); stroke-width:.6; }}
.radar-cat {{ cursor:help; }}
.radar-cat:hover .radar-alab, .radar-cat:focus .radar-alab {{ fill:var(--accent); }}
.radar-cat:focus {{ outline:none; }}
.radar-alab {{ font-family:var(--font-ui); font-size:10.5px; fill:var(--ink-2); font-weight:560; }}
.radar-max {{ font-family:var(--font-ui); font-size:9px; fill:var(--muted); }}
.radar-vlab {{ font-family:var(--font-ui); font-size:10.5px; font-weight:600; font-variant-numeric:tabular-nums; paint-order:stroke; stroke:var(--surface); stroke-width:3px; opacity:0; transition:opacity .12s; pointer-events:none; }}
.radar-shape {{ stroke-width:2; fill-opacity:.12; stroke-linejoin:round; pointer-events:none; }}
.radar-dot {{ r:3; pointer-events:none; }}
.radar-hit {{ fill:transparent; cursor:pointer; }}
.radar-pt:hover .radar-vlab, .radar-pt:focus .radar-vlab {{ opacity:1; }}
.radar-pt:hover .radar-dot, .radar-pt:focus .radar-dot {{ r:4.5; }}
.radar-pt:focus {{ outline:none; }}
/* D3 persona tiles */
.personas {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-top:44px; max-width:920px; }}
/* V3 question menu (home) */
.qmenu-intro {{ font-family:var(--font-ui); font-size:13px; color:var(--muted); margin:40px 0 18px; letter-spacing:.02em; }}
.qmenu {{ column-width:340px; column-gap:34px; }}
.qgroup {{ border:1px solid var(--hair); border-radius:14px; background:var(--surface); padding:20px 22px 6px; margin-bottom:34px; break-inside:avoid; }}
.qgroup-h {{ display:flex; align-items:center; gap:9px; font-family:var(--font-ui); font-size:12px; font-weight:560;
  text-transform:uppercase; letter-spacing:.08em; color:var(--ink-2); margin:0 0 8px; padding-bottom:12px; border-bottom:2px solid var(--accent-soft); }}
.qgroup-h .lic {{ color:var(--accent); }}
.qlink {{ display:flex; align-items:baseline; gap:8px; padding:9px 0; text-decoration:none; color:var(--ink);
  font-family:var(--font-body); font-size:15.5px; line-height:1.35; border-bottom:1px solid var(--hair); transition:color .15s ease; }}
.qlink:last-child {{ border-bottom:none; }}
.qlink:hover {{ color:var(--accent); text-decoration:none; }}
.qlink .qt {{ flex:1; }}
.qlink .qn {{ font-family:var(--font-head); font-weight:560; color:var(--accent); font-variant-numeric:tabular-nums; white-space:nowrap; }}
.qlink.soon {{ color:var(--muted); cursor:default; pointer-events:none; }}
.qlink.soon .qsoon {{ font-family:var(--font-ui); font-size:10px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); border:1px solid var(--hair); border-radius:4px; padding:1px 6px; }}
/* N2 Next-block */
.nextblock {{ margin-top:44px; padding-top:22px; border-top:1px solid var(--hair); }}
.nextblock .nb-h {{ font-family:var(--font-ui); font-size:11.5px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:12px; }}
.nextblock .nb-links {{ display:flex; flex-wrap:wrap; gap:12px; }}
.nextblock a {{ font-family:var(--font-body); font-size:14px; color:var(--ink); text-decoration:none;
  border:1px solid var(--hair); border-radius:999px; padding:8px 15px; transition:border-color .18s ease, color .18s ease; }}
.nextblock a:hover {{ border-color:var(--accent); color:var(--accent); text-decoration:none; }}
.coverage-note {{ margin-top:22px; font-family:var(--font-ui); font-size:11px; color:var(--muted); line-height:1.5; max-width:70ch; opacity:.85; }}
/* D9 use-case catalog */
/* D9b — use-case bar chart: companies found running each pattern (plain counts) */
.uc-bars {{ margin-top:22px; display:flex; flex-direction:column; gap:7px; }}
.uc-bars .uc-brow {{ display:grid; grid-template-columns:minmax(140px,220px) 1fr auto; align-items:center; gap:14px; cursor:pointer; text-decoration:none; }}
.uc-bars .uc-brow:hover .uc-bname {{ color:var(--accent); }}
.uc-bname {{ font-family:var(--font-ui); font-size:12.5px; color:var(--ink-2); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; transition:color .15s; }}
.uc-btrack {{ position:relative; height:18px; background:var(--surface-2); border-radius:5px; overflow:hidden; }}
.uc-bfill {{ position:absolute; inset:0 auto 0 0; height:100%; background:color-mix(in srgb, var(--accent) 26%, var(--surface)); border-radius:5px; }}
.uc-bnum {{ position:absolute; inset:0 auto 0 0; height:100%; background:var(--accent); border-radius:5px; }}
.uc-bval {{ font-family:var(--font-ui); font-variant-numeric:tabular-nums; font-size:12px; color:var(--ink-2); white-space:nowrap; }}
.uc-bval b {{ color:var(--ink); }}
.uc-bkey {{ display:flex; gap:16px; flex-wrap:wrap; font-family:var(--font-ui); font-size:11.5px; color:var(--muted); margin:4px 0 2px; }}
.uc-bkey .k {{ display:flex; align-items:center; gap:6px; }}
.uc-bkey .sw {{ width:16px; height:9px; border-radius:3px; }}
.uc-cards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; margin-top:32px; }}
.uc-card {{ display:block; padding:18px; border:1px solid var(--hair); border-radius:12px; background:var(--surface); text-decoration:none; transition:border-color .18s ease, transform .18s ease; }}
.uc-card:hover {{ border-color:var(--accent); transform:translateY(-2px); text-decoration:none; }}
.uc-name {{ font-family:var(--font-head); font-weight:560; font-size:16px; color:var(--ink); }}
.uc-desc {{ font-size:12.5px; color:var(--muted); margin-top:5px; line-height:1.5; }}
.uc-stats {{ display:flex; flex-wrap:wrap; gap:6px 14px; margin-top:12px; font-family:var(--font-ui); font-size:12px; color:var(--ink-2); }}
.uc-stats b {{ color:var(--ink); font-variant-numeric:tabular-nums; }}
.diffsvg {{ display:block; margin-top:10px; max-width:780px; height:auto; }}
.uc-diffusion {{ display:flex; flex-wrap:wrap; gap:8px; }}
.uc-diff {{ font-family:var(--font-ui); font-size:12px; color:var(--ink-2); background:var(--surface-2); border:1px solid var(--hair); border-radius:999px; padding:4px 11px; }}
.uc-diff b {{ color:var(--accent); font-variant-numeric:tabular-nums; }}
.uc-runners {{ font-family:var(--font-body); font-size:14px; line-height:1.9; color:var(--ink-2); }}
/* D10 vendor chips */
.vchips {{ display:flex; flex-wrap:wrap; gap:8px; }}
.vchip {{ font-family:var(--font-ui); font-size:12.5px; color:var(--ink-2); background:var(--surface-2);
  border:1px solid var(--hair); border-radius:999px; padding:5px 12px; text-decoration:none; }}
a.vchip:hover {{ border-color:var(--accent); color:var(--accent); text-decoration:none; }}
.expbtn {{ margin-top:24px; font-family:var(--font-ui); font-size:13px; color:var(--ink); background:var(--surface-2);
  border:1px solid var(--hair); border-radius:8px; padding:10px 18px; cursor:pointer; transition:border-color .2s ease, color .2s ease; }}
.expbtn:hover {{ border-color:var(--accent); color:var(--accent); }}
/* visible "data pending" marker (plumbing-first fallback rule; keys off data presence) */
.pending {{ font-family:var(--font-ui); font-size:12.5px; color:var(--ink-2); line-height:1.5;
  background:color-mix(in srgb,var(--v-unquantified) 12%,var(--surface)); border:1px solid var(--hair);
  border-radius:8px; padding:10px 14px; margin:14px 0; }}
.pending b {{ color:var(--ink); font-weight:560; }}
.pending .lic {{ color:var(--v-unquantified); vertical-align:-.16em; margin-right:4px; }}
.toggle {{
  border: 1px solid var(--hair); background: var(--surface); color: var(--ink-2);
  border-radius: 999px; padding: 6px 12px; font-size: 12px; cursor: pointer;
  display: inline-flex; gap: 6px; align-items: center; transition: all .2s ease;
}}
.toggle:hover {{ color: var(--ink); border-color: var(--muted); }}

/* ---- altitude sections ---- */
.altitude {{ display: none; }}
.altitude.active {{ display: block; animation: rise .4s cubic-bezier(.2,.7,.2,1); }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}

/* ============ A0 ORBIT ============ */
.orbit {{
  min-height: calc(100vh - 52px);
  display: flex; flex-direction: column; justify-content: center;
  padding: clamp(32px, 7vh, 90px) clamp(20px, 6vw, 96px);
  max-width: 1180px; margin: 0 auto;
}}
.orbit .eyebrow {{
  font-size: 13px; letter-spacing: .18em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 22px;
  display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap;
}}
.descend-mini {{
  font-family: var(--font-ui); background: none; border: 1px solid var(--hair); cursor: pointer;
  color: var(--ink-2); font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
  padding: 7px 15px; border-radius: 999px; display: inline-flex; align-items: center; gap: 8px;
  transition: color .2s ease, border-color .2s ease;
}}
.descend-mini:hover {{ color: var(--accent); border-color: var(--accent); }}
.descend-mini .arrow {{ display: inline-block; transition: transform .3s ease; }}
.descend-mini:hover .arrow {{ transform: translateY(3px); }}
.orbit h1 {{
  font-weight: 300; font-size: clamp(30px, 5vw, 62px); line-height: 1.08;
  letter-spacing: -.02em; margin: 0 0 8px; max-width: 16ch;
}}
.orbit h1 b {{ font-weight: 640; }}
.orbit .sub {{ font-size: clamp(16px,1.6vw,20px); color: var(--ink-2); max-width: 46ch; margin: 0 0 54px; font-weight: 350; }}
/* headline + globe two-column hero */
.orbit-hero {{ display: flex; align-items: center; gap: clamp(24px, 5vw, 72px); flex-wrap: wrap; }}
.orbit-copy {{ flex: 1 1 440px; min-width: 300px; }}
.orbit-copy .sub {{ margin-bottom: 0; }}
.globe-wrap {{ flex: 0 1 340px; position: relative; display: flex; flex-direction: column;
  justify-content: center; align-items: center; cursor: grab; border-radius: 50%; outline: none; }}
#globe {{ width: 100%; max-width: 360px; height: auto; display: block;
  transition: transform .35s cubic-bezier(.2,.7,.2,1), filter .35s ease; }}
.globe-wrap:hover #globe, .globe-wrap:focus-visible #globe {{ transform: scale(1.035); filter: drop-shadow(0 6px 22px rgba(189,122,38,.22)); }}
.globe-wrap.dragging {{ cursor: grabbing; }}
.globe-wrap.dragging #globe {{ transform: none; filter: none; }}
/* the fade-in cue pill */
.globe-cue {{
  position: absolute; bottom: 6%; left: 50%; transform: translate(-50%, 8px);
  font-family: var(--font-ui); font-size: 12px; letter-spacing: .06em; text-transform: uppercase;
  color: #fff; background: var(--accent); padding: 7px 15px; border-radius: 999px; white-space: nowrap;
  box-shadow: 0 4px 16px rgba(0,0,0,.18); opacity: 0; pointer-events: none; cursor: pointer;
  transition: opacity .28s ease, transform .28s cubic-bezier(.2,.7,.2,1);
}}
.globe-wrap:hover .globe-cue, .globe-wrap:focus-visible .globe-cue {{ pointer-events: auto; }}
.globe-wrap:hover .globe-cue, .globe-wrap:focus-visible .globe-cue {{ opacity: 1; transform: translate(-50%, 0); }}
.globe-wrap.dragging .globe-cue {{ opacity: 0; }}
.globe-cue .arrow {{ display: inline-block; transition: transform .3s ease; }}
.globe-wrap:hover .globe-cue .arrow {{ transform: translateX(3px); }}
.globe-sphere {{ fill: var(--page); stroke: var(--land-edge); stroke-width: .8; }}
.globe-halo {{ fill: var(--accent); opacity: .06; }}
.globe-land {{ fill: var(--land); stroke: var(--land-edge); stroke-width: .4; }}
.globe-grat {{ fill: none; stroke: var(--grid); stroke-width: .4; opacity: .5; }}
.globe-dot {{ fill: var(--accent); stroke: var(--surface); stroke-width: 1; }}
.globe-dot.back {{ opacity: .18; }}
@media (max-width: 720px) {{ .globe-wrap {{ flex-basis: 260px; }} }}

/* hero + KPI row */
.hero-row {{ display: flex; flex-wrap: wrap; align-items: flex-end; gap: clamp(28px, 5vw, 72px); margin-bottom: 56px; }}
.hero {{ display: flex; flex-direction: column; }}
.hero .num {{ font-size: clamp(64px, 11vw, 132px); font-weight: 300; line-height: .9; letter-spacing: -.03em; color: var(--ink); }}
.hero .lab {{ font-size: 15px; color: var(--muted); margin-top: 10px; letter-spacing: .02em; }}
.kpis {{ display: flex; flex-wrap: wrap; gap: clamp(20px, 3vw, 44px); padding-bottom: 8px; }}
.kpi .num {{ font-size: clamp(26px, 3.4vw, 40px); font-weight: 340; letter-spacing: -.02em; }}
.kpi .lab {{ font-size: 13px; color: var(--muted); margin-top: 4px; }}

/* the honest gap bar */
.gap {{ max-width: 760px; }}
.gap .cap {{ font-size: 14px; color: var(--ink-2); margin-bottom: 12px; }}
.gap .cap b {{ color: var(--ink); font-weight: 600; }}
.gapbar {{
  position: relative; height: 46px; border-radius: 7px; overflow: hidden;
  background: var(--surface-2); display: flex; align-items: stretch;
}}
.gapbar .seg {{ display: flex; align-items: center; padding: 0 14px; font-size: 12.5px; white-space: nowrap; }}
.gapbar .confirmed {{ background: var(--accent-soft); color: var(--ink); }}
.gapbar .proof {{ background: var(--accent); color: #fff; font-weight: 560; }}
.gaplabels {{ display: flex; justify-content: space-between; margin-top: 10px; font-size: 12px; color: var(--muted); }}
.footnote {{ font-size: 12.5px; color: var(--muted); margin-top: 30px; max-width: 60ch; }}
.methodology {{ margin-top: 16px; max-width: 68ch; font-family: var(--font-ui); }}
.methodology summary {{ cursor: pointer; font-size: 12.5px; color: var(--ink-2); letter-spacing: .02em; }}
.methodology summary:hover {{ color: var(--accent); }}
.methodology ul {{ margin: 12px 0 0; padding-left: 18px; }}
.methodology li {{ font-size: 12.5px; color: var(--muted); line-height: 1.6; margin-bottom: 6px; }}
.methodology b {{ color: var(--ink-2); font-weight: 560; }}

.descend {{
  margin-top: 60px; display: inline-flex; align-items: center; gap: 10px;
  font-size: 14px; letter-spacing: .04em; color: var(--ink-2);
  background: none; border: none; cursor: pointer; padding: 0;
}}
.descend:hover {{ color: var(--accent); }}
.descend .arrow {{ display: inline-block; transition: transform .3s ease; }}
.descend:hover .arrow {{ transform: translateY(4px); }}

/* credits / colophon */
.credits {{ margin-top: 72px; padding-top: 28px; border-top: 1px solid var(--hair);
  display: flex; flex-wrap: wrap; align-items: center; gap: 22px 40px; }}
.credit-card {{ display: flex; align-items: center; gap: 16px; }}
.credit-photo {{ width: 72px; height: 72px; border-radius: 50%; object-fit: cover;
  filter: grayscale(1) contrast(1.02); border: 1px solid var(--hair);
  box-shadow: 0 2px 10px rgba(0,0,0,.12); }}
.credit-eyebrow {{ font-family: var(--font-ui); font-size: 11px; letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }}
.credit-name {{ font-family: var(--font-head); font-size: 21px; font-weight: 560; letter-spacing: -.01em; color: var(--ink); }}
.credit-role {{ font-family: var(--font-ui); font-size: 13px; color: var(--ink-2); margin-top: 2px; }}
.credit-note {{ flex: 1 1 340px; min-width: 280px; font-size: 12.5px; color: var(--muted);
  max-width: 60ch; margin: 0; line-height: 1.6; }}

/* ============ A1 WORLD ============ */
.world {{ max-width: 1240px; margin: 0 auto; padding: clamp(24px,4vh,52px) clamp(20px,5vw,64px) 80px; }}
.world .head {{ display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom:8px; }}
.world h2 {{ font-weight:340; font-size:clamp(24px,3.2vw,38px); letter-spacing:-.02em; margin:0; }}
.world .lede {{ color:var(--ink-2); max-width:56ch; font-size:15px; margin:6px 0 0; }}
.world .controls {{ display:flex; gap:6px; align-items:center; }}
.seg-ctrl {{ display:inline-flex; background:var(--surface-2); border:1px solid var(--hair); border-radius:999px; padding:3px; }}
.seg-ctrl button {{ border:none; background:none; color:var(--ink-2); font-size:12.5px; padding:6px 13px; border-radius:999px; cursor:pointer; transition:all .18s ease; }}
.seg-ctrl button.on {{ background:var(--surface); color:var(--ink); box-shadow:var(--shadow); font-weight:560; }}
.mapwrap {{ position:relative; margin-top:22px; }}
#mapsvg {{ width:100%; height:auto; display:block; cursor:grab; touch-action:none; overflow:hidden; border-radius:8px; }}
#mapsvg:active {{ cursor:grabbing; }}
.zoomctl {{ position:absolute; top:12px; right:12px; display:flex; flex-direction:column; gap:6px; }}
.zoomctl button {{ width:32px; height:32px; border:1px solid var(--hair); background:color-mix(in srgb,var(--surface) 92%,transparent);
  backdrop-filter:blur(4px); color:var(--ink-2); font-size:17px; line-height:1; border-radius:7px; cursor:pointer;
  display:flex; align-items:center; justify-content:center; transition:color .18s ease, border-color .18s ease; font-family:var(--font-ui); }}
.zoomctl button:hover {{ color:var(--accent); border-color:var(--accent); }}
.zoomhint {{ position:absolute; left:12px; bottom:10px; font-family:var(--font-ui); font-size:11px; color:var(--muted);
  background:color-mix(in srgb,var(--surface) 78%,transparent); padding:3px 9px; border-radius:6px; pointer-events:none; }}
.land {{ fill:var(--land); stroke:var(--land-edge); stroke-width:.6; }}
.graticule {{ fill:none; stroke:var(--grid); stroke-width:.4; opacity:.35; }}
.bub {{ stroke:var(--surface); stroke-width:1.5; cursor:pointer; transition:opacity .2s; }}
.bub:hover {{ opacity:.85; }}
.bub-label {{ font-size:11px; fill:var(--ink-2); pointer-events:none; font-variant-numeric:tabular-nums; }}
.tip {{ position:fixed; z-index:50; pointer-events:none; background:var(--surface); color:var(--ink);
  border:1px solid var(--hair); border-radius:9px; padding:11px 13px; font-size:13px; box-shadow:0 6px 24px rgba(0,0,0,.14);
  opacity:0; transition:opacity .12s; max-width:250px; }}
.tip h4 {{ margin:0 0 6px; font-size:13.5px; }}
.tip .r {{ display:flex; justify-content:space-between; gap:18px; color:var(--ink-2); font-size:12.5px; }}
.tip .r b {{ color:var(--ink); font-variant-numeric:tabular-nums; }}
.tip .hint {{ margin-top:7px; font-size:11px; color:var(--muted); }}
/* legend */
.legend {{ display:flex; flex-wrap:wrap; gap:26px; align-items:center; margin-top:18px; font-size:12px; color:var(--muted); }}
.legend .ramp {{ display:flex; align-items:center; gap:8px; }}
.legend .ramp .bar {{ width:120px; height:9px; border-radius:5px;
  background:linear-gradient(90deg,var(--d2),var(--d4),var(--d6),var(--d7)); }}
.legend .sizes {{ display:flex; align-items:flex-end; gap:12px; }}
.legend .sizes svg {{ overflow:visible; }}
/* ranked-bar twin */
.barsview {{ margin-top:26px; }}
.barrow {{ display:grid; grid-template-columns:132px 1fr 62px; align-items:center; gap:14px; padding:5px 0; cursor:pointer; }}
.barrow:hover .barname {{ color:var(--ink); }}
.barrow:hover .bar {{ filter:brightness(1.04); }}
.barname {{ font-family:var(--font-ui); font-size:13px; color:var(--ink-2); text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bartrack {{ position:relative; height:22px; }}
.bar {{ height:22px; border-radius:0 4px 4px 0; transition:width .5s cubic-bezier(.2,.7,.2,1), background .3s; }}
.barval {{ font-family:var(--font-ui); font-size:13px; color:var(--ink); font-variant-numeric:tabular-nums; text-align:left; }}
.barval .u {{ color:var(--muted); font-size:11px; }}
/* table twin */
.tabletwin {{ margin-top:34px; }}
.tabletwin summary {{ cursor:pointer; color:var(--ink-2); font-size:13px; letter-spacing:.02em; }}
.tabletwin table {{ width:100%; border-collapse:collapse; margin-top:14px; font-size:13.5px; }}
.tabletwin th, .tabletwin td {{ text-align:right; padding:8px 12px; border-bottom:1px solid var(--hair); font-variant-numeric:tabular-nums; }}
.tabletwin th:first-child, .tabletwin td:first-child {{ text-align:left; font-variant-numeric:normal; }}
.tabletwin th {{ color:var(--muted); font-weight:560; font-size:12px; letter-spacing:.03em; cursor:pointer;
  white-space:nowrap; user-select:none; transition:color .15s; }}
.tabletwin th:hover {{ color:var(--ink-2); }}
/* sort affordance: a faint idle chevron on every sortable header, solid + directional on the active one */
.tabletwin th[data-k]::after {{ content:"↕"; margin-left:5px; font-size:10px; opacity:.32; }}
.tabletwin th[data-k].sort-asc {{ color:var(--ink); }}
.tabletwin th[data-k].sort-desc {{ color:var(--ink); }}
.tabletwin th[data-k].sort-asc::after {{ content:"↑"; opacity:1; color:var(--accent); }}
.tabletwin th[data-k].sort-desc::after {{ content:"↓"; opacity:1; color:var(--accent); }}
.tabletwin tbody tr {{ cursor:pointer; }}
.tabletwin tbody tr:hover {{ background:var(--surface-2); }}

/* ============ A2 TERRITORY (decision grid) ============ */
.terr {{ max-width:1240px; margin:0 auto; padding:clamp(24px,4vh,52px) clamp(20px,5vw,64px) 90px; }}
.terr .head {{ display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom:6px; }}
.terr h2 {{ font-weight:340; font-size:clamp(24px,3.2vw,38px); letter-spacing:-.02em; margin:0; }}
.terr h2 .scope {{ color:var(--accent); }}
.backup {{ font-family:var(--font-ui); background:none; border:none; cursor:pointer; padding:0; margin:0 0 10px;
  color:var(--ink-2); font-size:13px; letter-spacing:.02em; display:inline-flex; align-items:center; gap:6px; transition:color .18s ease; }}
.backup:hover {{ color:var(--accent); }}
.terr .lede {{ color:var(--ink-2); max-width:60ch; font-size:15px; margin:6px 0 0; }}
.terr .controls {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; }}
/* the grid */
.gridwrap {{ margin-top:26px; overflow-x:auto; }}
table.grid {{ border-collapse:separate; border-spacing:3px; }}
table.grid th {{ font-family:var(--font-ui); font-size:11.5px; font-weight:560; color:var(--muted); letter-spacing:.02em; padding:4px 6px; }}
table.grid th.col {{ height:104px; vertical-align:bottom; white-space:nowrap; padding:0; }}
table.grid th.col span {{ display:inline-block; transform:rotate(-45deg); transform-origin:left bottom; translate:14px 0; text-align:left; }}
table.grid th.row {{ text-align:right; white-space:nowrap; max-width:200px; overflow:hidden; text-overflow:ellipsis; font-family:var(--font-body); font-size:13.5px; color:var(--ink-2); font-weight:400; }}
table.grid td {{ width:64px; height:44px; border-radius:6px; text-align:center; vertical-align:middle; cursor:pointer; position:relative; transition:transform .12s ease, box-shadow .12s ease; }}
table.grid td.empty {{ background:transparent; cursor:default; box-shadow:inset 0 0 0 1px var(--hair); opacity:.4; }}
table.grid td.cell {{ box-shadow:inset 0 0 0 1px var(--hair); }}
table.grid td.cell:hover {{ transform:scale(1.08); box-shadow:0 3px 12px rgba(0,0,0,.18); z-index:2; }}
/* row/column emphasis: dim everything not in the hovered cell's row or column */
table.grid.emph td.cell {{ opacity:.26; transition:opacity .14s ease, transform .12s ease, box-shadow .12s ease; }}
table.grid.emph td.cell.lit {{ opacity:1; }}
table.grid.emph th.row.lit, table.grid.emph th.col.lit span {{ color:var(--ink); }}
table.grid td .glyph {{ font-size:13px; line-height:1; }}
table.grid td .cnt {{ font-family:var(--font-ui); font-size:11px; font-variant-numeric:tabular-nums; opacity:.9; }}
/* verdict fills (light bg tints; glyph+label carry meaning, never color alone) */
.v-strong {{ background:color-mix(in srgb, var(--v-strong) 22%, var(--surface)); color:var(--ink); }}
.v-proven {{ background:color-mix(in srgb, var(--v-strong) 22%, var(--surface)); color:var(--ink); }}
.v-active {{ background:color-mix(in srgb, var(--v-active) 26%, var(--surface)); color:var(--ink); }}
.v-unquantified {{ background:color-mix(in srgb, var(--v-unquantified) 24%, var(--surface)); color:var(--ink); }}
.v-talk   {{ background:color-mix(in srgb, var(--v-talk) 20%, var(--surface)); color:var(--ink); }}
.g-strong, .g-proven {{ color:var(--v-strong); }} .g-active {{ color:var(--v-active); }}
.g-unquantified {{ color:var(--v-unquantified); }} .g-talk {{ color:var(--v-talk); }}
/* magnitude mode uses sequential ramp inline */
.verdict-key {{ display:flex; flex-wrap:wrap; gap:20px; margin-top:20px; font-size:12.5px; color:var(--ink-2); font-family:var(--font-ui); }}
.verdict-key .k {{ display:inline-flex; align-items:center; gap:7px; }}
.verdict-key .sw {{ width:15px; height:15px; border-radius:4px; display:inline-flex; align-items:center; justify-content:center; font-size:10px; }}
/* per-vertical histogram (compare AI adoption across industries) */
.vhist-block {{ margin-top:52px; }}
.vhist-head {{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:14px; margin-bottom:18px; }}
.vhist-head h3 {{ font-family:var(--font-head); font-weight:360; font-size:clamp(18px,2.1vw,24px); letter-spacing:-.01em; margin:0; }}
.vhist-scope {{ color:var(--accent); }}
.vhist .vrow {{ display:grid; grid-template-columns:190px 1fr 96px; align-items:center; gap:14px; padding:4px 0; cursor:default; }}
.vhist .vname {{ font-family:var(--font-ui); font-size:13px; color:var(--ink-2); text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.vhist .vtrack {{ position:relative; height:20px; }}
.vhist .vbar {{ height:20px; border-radius:0 4px 4px 0; transition:width .55s cubic-bezier(.2,.7,.2,1), background .3s; }}
.vhist .vval {{ font-family:var(--font-ui); font-size:12.5px; color:var(--ink); font-variant-numeric:tabular-nums; }}
.vhist .vval .u {{ color:var(--muted); font-size:11px; }}
.vhist .vval .g {{ margin-left:6px; }}

/* ============ A3 STREET — slide-in company panel ============ */
#scrim {{ position:fixed; inset:0; background:rgba(20,18,16,.34); z-index:60; opacity:0; visibility:hidden; transition:opacity .26s ease; }}
#scrim.open {{ opacity:1; visibility:visible; }}
#panel {{ position:fixed; top:0; right:0; height:100vh; width:min(680px,94vw); z-index:61; background:var(--surface);
  box-shadow:-14px 0 44px rgba(0,0,0,.24); transform:translateX(100%); transition:transform .3s cubic-bezier(.22,.61,.36,1);
  display:flex; flex-direction:column; }}
#panel.open {{ transform:translateX(0); }}
#panel .phead {{ padding:22px clamp(20px,3vw,34px) 16px; border-bottom:1px solid var(--hair); flex:0 0 auto; }}
#panel .pcrumb {{ font-family:var(--font-ui); font-size:11.5px; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); margin-bottom:8px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
#panel .pcrumb .verdict-tag {{ font-family:var(--font-ui); text-transform:none; letter-spacing:0; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:560; }}
#panel h3 {{ font-family:var(--font-head); font-weight:360; font-size:clamp(20px,2.4vw,27px); letter-spacing:-.01em; margin:0; }}
#panel h3 .x {{ color:var(--accent); }}
#panel .psub {{ color:var(--ink-2); font-size:13.5px; margin:7px 0 0; }}
#panel .pclose {{ position:absolute; top:20px; right:clamp(16px,3vw,30px); background:var(--surface-2); border:1px solid var(--hair);
  border-radius:8px; width:32px; height:32px; cursor:pointer; color:var(--ink-2); font-size:17px; line-height:1; display:flex; align-items:center; justify-content:center; }}
#panel .pclose:hover {{ color:var(--ink); background:var(--surface); }}
#panel .pbody {{ overflow-y:auto; padding:8px clamp(20px,3vw,34px) 40px; flex:1 1 auto; }}
.co {{ padding:16px 0; border-bottom:1px solid var(--hair); }}
.co:last-child {{ border-bottom:none; }}
.co .top {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; }}
.co .name {{ font-family:var(--font-head); font-weight:540; font-size:16px; letter-spacing:.01em; }}
a.colink {{ color:var(--ink); text-decoration:none; }} a.colink:hover {{ color:var(--accent); text-decoration:underline; }}
.co .glyph {{ font-size:13px; }}
.co .use {{ color:var(--ink-2); font-size:13.5px; line-height:1.5; margin:6px 0 9px; font-family:var(--font-body); }}
.co .meta {{ display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; font-family:var(--font-ui); font-size:11.5px; color:var(--muted); }}
.co .chip {{ padding:2px 8px; border-radius:5px; background:var(--surface-2); border:1px solid var(--hair); font-weight:560; letter-spacing:.02em; }}
.freshbadge {{ padding:2px 7px; border-radius:5px; font-size:10.5px; font-weight:560; letter-spacing:.02em; }}
.fb-aging {{ color:var(--v-active); background:color-mix(in srgb,var(--v-active) 15%,var(--surface)); }}
.fb-stale {{ color:var(--v-active); background:color-mix(in srgb,var(--v-active) 18%,var(--surface)); }}
.co .chip.P {{ color:var(--v-strong); }} .co .chip.I {{ color:var(--accent); }} .co .chip.S {{ color:var(--muted); }}
.co .val {{ color:var(--ink-2); }}
.co a.src {{ color:var(--accent); text-decoration:none; font-weight:560; }}
.co a.src:hover {{ text-decoration:underline; }}
.co .exist {{ display:inline-flex; align-items:center; gap:5px; }}
.pbody .sortbar {{ display:flex; gap:8px; align-items:center; padding:10px 0 4px; font-family:var(--font-ui); font-size:11.5px; color:var(--muted); position:sticky; top:0; background:var(--surface); }}
.pbody .sortbar button {{ border:none; background:none; color:var(--ink-2); cursor:pointer; font-size:11.5px; padding:3px 7px; border-radius:5px; }}
.pbody .sortbar button.on {{ background:var(--surface-2); color:var(--ink); font-weight:560; }}

.stub {{ padding: 80px clamp(20px,6vw,96px); max-width: 1180px; margin: 0 auto; color: var(--muted); }}
</style>
</head>
<body>
<div class="topbar">
  <div class="brand" style="cursor:pointer" onclick="goRoute('a0')">KARTO&nbsp; <b>AI Atlas</b></div>
  <nav class="crumbs" id="crumbs"><span class="here">Orbit</span></nav>
  <div class="topnav">
    <a href="#/world" class="navlink" data-route="a1">World</a>
    <a href="#/grid" class="navlink" data-route="a2">Grid</a>
    <a href="#/usecases" class="navlink" data-route="usecases">Use&nbsp;cases</a>
    <a href="#/trends" class="navlink" data-route="trends">Trends</a>
    <a href="#/hype" class="navlink" data-route="hype">Adoption</a>
    <a href="#/compare" class="navlink" data-route="compare">Compare</a>
    <a href="#/silent" class="navlink" data-route="silent">Silent&nbsp;list</a>
    <div class="omni-wrap">
      <label class="omni-box" for="omni">{icon('search',14)}<input id="omni" type="search" autocomplete="off"
        spellcheck="false" placeholder="Find a company…" aria-label="Search companies"></label>
      <div class="omni-results" id="omniResults" role="listbox"></div>
    </div>
    <button class="toggle" id="themeToggle" aria-label="Toggle light/dark">
      <span id="themeIcon">{icon('moon',15)}</span><span id="themeLabel">Dark</span>
    </button>
  </div>
</div>

<!-- ============ ALTITUDE 0 — ORBIT ============ -->
<section class="altitude active" id="a0" data-alt="Orbit">
  <div class="orbit">
    <div class="eyebrow">
      <span>The current state of AI on Earth · a source-gated atlas</span>
      <button class="descend-mini" id="descendTop">Descend to the world <span class="arrow">↓</span></button>
    </div>
    <div class="orbit-hero">
      <div class="orbit-copy">
        <h1>AI adoption is <b>broad and confirmed</b>.<br>Independent evidence of value stays <b>scarce</b>.</h1>
        <p class="sub">A ground-up census of what {fmt(g['companies'])} of the world's largest listed companies
        actually do with AI — each deployment named, gated, and linked to its source.</p>
      </div>
      <div class="globe-wrap" id="globeWrap" role="button" tabindex="0"
           aria-label="Explore the world map — {g['countries']} countries surveyed">
        <svg id="globe" aria-hidden="true"></svg>
        <span class="globe-cue" id="globeCue">Explore the map <span class="arrow">→</span></span>
      </div>
    </div>

    <div class="hero-row">
      <div class="hero">
        <span class="num">{fmt(g['deployments'])}</span>
        <span class="lab">AI deployments found &amp; source-linked</span>
      </div>
      <div class="kpis">
        <div class="kpi"><div class="num">{fmt(g['companies'])}</div><div class="lab">companies</div></div>
        <div class="kpi"><div class="num">{g['countries']}</div><div class="lab">countries</div></div>
        <div class="kpi"><div class="num">{g['verticals']}</div><div class="lab">industry verticals</div></div>
      </div>
    </div>

    <div class="gap">
      <div class="cap">Adoption is broad — <b>{fmt(g['confirmed'])} of {fmt(g['deployments'])}</b> deployments
      ({round(100*g['confirmed']/g['deployments'])}%) are confirmed. Yet only
      <b>{fmt(g['with_value_number'])}</b> ({round(100*g['with_value_number']/g['deployments'])}%) carry any value number, and
      independent verification is rare. <b>On today's data, the gap is in evidence of value, not in adoption.</b></div>
      <div class="gapbar" role="img" aria-label="{fmt(g['confirmed'])} confirmed of {fmt(g['deployments'])}; {fmt(g['with_value_number'])} carry a value number">
        <div class="seg proof" style="width:{max(6,round(100*g['with_value_number']/g['deployments']))}%">{fmt(g['with_value_number'])} carry a value number</div>
        <div class="seg confirmed" style="width:{round(100*(g['confirmed']-g['with_value_number'])/g['deployments'])}%">confirmed, no number</div>
        <div class="seg" style="flex:1"></div>
      </div>
      <div class="gaplabels"><span>quantified value claim</span><span>unconfirmed / not found →</span></div>
    </div>

    <p class="footnote">Read it as a map: descend from here to the world, then to any country's
    industries, down to the individual companies and their sources. A disclosed-evidence sample —
    honest about what it can and cannot see.</p>
    <details class="methodology"><summary>Methodology &amp; how to read this</summary>
      <ul>
        <li><b>Source-gated.</b> Only company filings, own-disclosure, institutional reports, and credible
            press count. SEO blogs, vendor marketing and aggregators are rejected on sight.</li>
        <li><b>Absence is a finding.</b> Companies searched with zero disclosed AI are recorded, not dropped —
            "no confirmed deployment" is itself a data point.</li>
        <li><b>Existence tiers:</b> CONFIRMED (own disclosure) › CLAIMED (third-party) › SMOKE (rejected).</li>
        <li><b>Value is almost always self-reported.</b> "Carries a value number" ≠ audited. Independent
            verification is essentially absent — that gap is the study's central finding.</li>
        <li><b>Density</b> = confirmed deployments per company searched; deployment-level, so &gt;1× is normal.</li>
        <li><b>Two axes:</b> industry (vertical) × what the AI does (function). One deployment = one cell.</li>
      </ul>
    </details>

    <button class="descend" id="descend">Descend to the world <span class="arrow">↓</span></button>

    <div class="qmenu-intro">Ask a question — one click to the answer, pre-filtered and sourced.</div>
    <div class="qmenu" id="qmenu"></div>

    <div class="credits">
      <div class="credit-card">
        <img class="credit-photo" src="{MEHDI_IMG}" alt="Mehdi Lamrani" width="72" height="72">
        <div class="credit-who">
          <div class="credit-eyebrow">Research, method &amp; design</div>
          <div class="credit-name">Mehdi Lamrani</div>
          <div class="credit-role">AI Specialist · Databricks</div>
        </div>
      </div>
      <p class="credit-note">A source-gated study of where AI is actually profitable — conceived,
      directed and built by the Author. Data gathered under a strict evidence gate across {g['countries']} countries;
      atlas rendered from the canonical register. © 2026.</p>
    </div>
  </div>
</section>

<!-- ============ ALTITUDE 1 — WORLD ============ -->
<section class="altitude" id="a1" data-alt="World">
  <div class="world">
    <div class="head">
      <div>
        <h2>Where AI actually lands</h2>
        <p class="lede">Each of the {g['countries']} markets we searched. Bubble size = deployments found;
        color = <b title="Confirmed deployments per company searched. Companies can carry several, so values above 1× are normal — e.g. Norway 1.48× = 148 confirmed per 100 companies searched.">adoption density</b>
        (confirmed deployments per company searched — <span style="cursor:help" title="Companies can disclose several deployments, so density above 1× is expected, not a bug.">values above 1× are normal {icon('info',14)}</span>). Big isn't dense.</p>
      </div>
      <div class="controls">
        <div class="seg-ctrl" id="viewCtrl">
          <button data-view="map" class="on">Map</button>
          <button data-view="bars">Ranked</button>
        </div>
        <div class="seg-ctrl" id="metricCtrl">
          <button data-m="density" class="on">Density</button>
          <button data-m="deployments">Volume</button>
          <button data-m="proof_pct">Quantified&nbsp;%</button>
        </div>
      </div>
    </div>
    <div class="mapwrap" id="mapView">
      <svg id="mapsvg" viewBox="0 0 960 480" role="img" aria-label="World map of AI deployment by country"></svg>
      <div class="zoomctl" aria-label="Map zoom">
        <button id="zoomIn" title="Zoom in" aria-label="Zoom in">+</button>
        <button id="zoomOut" title="Zoom out" aria-label="Zoom out">−</button>
        <button id="zoomReset" title="Reset view" aria-label="Reset view">⤢</button>
      </div>
      <div class="zoomhint">scroll or +/− to zoom · drag to pan · double-click to reset</div>
    </div>
    <div class="barsview" id="barsView" hidden></div>
    <div class="legend">
      <div class="ramp"><span>low</span><span class="bar"></span><span>high density</span></div>
      <div class="sizes" id="sizeLegend"></div>
      <div>· click a country to descend →</div>
    </div>
    <details class="tabletwin">
      <summary>Table view (all {g['countries']} countries)</summary>
      <table id="worldTable">
        <thead><tr>
          <th data-k="name">Country</th><th data-k="deployments">Deployments</th>
          <th data-k="companies">Companies</th><th data-k="confirmed">Confirmed</th>
          <th data-k="density">Density&nbsp;×</th><th data-k="proof_pct">Quantified&nbsp;%</th>
        </tr></thead><tbody></tbody>
      </table>
    </details>
  </div>
</section>

<!-- ============ ALTITUDE 2 — TERRITORY (decision grid) ============ -->
<section class="altitude" id="a2" data-alt="Territory">
  <div class="terr">
    <div class="head">
      <div>
        <button class="backup" id="backWorld" hidden>← Back to the world</button>
        <h2>The decision grid — <span class="scope" id="scopeName">the world</span></h2>
        <p class="lede">Every industry (down) × what the AI does (across). Each cell judged by how much of it
        is <b>proven with metrics</b>, <b>active</b>, confirmed-only, or <b>unverified</b> in our sources. Click any cell for the companies.</p>
      </div>
      <div class="controls">
        <div class="seg-ctrl" id="modeCtrl">
          <button data-mode="verdict" class="on">Verdict</button>
          <button data-mode="magnitude">Volume</button>
        </div>
      </div>
    </div>
    <div class="gridwrap"><table class="grid" id="gridTable"></table></div>
    <div class="verdict-key" id="verdictKey">
      <span class="k"><span class="sw v-proven g-proven">●</span> Proven — ≥40% cite a value metric</span>
      <span class="k"><span class="sw v-active g-active">◐</span> Active — confirmed, some metrics (≥15%)</span>
      <span class="k"><span class="sw v-unquantified g-unquantified">◍</span> Unquantified — mostly confirmed, no metric found yet</span>
      <span class="k"><span class="sw v-talk g-talk">○</span> Unverified — claimed, not yet confirmed in our sources</span>
      <span class="k"><span class="sw" style="background:var(--surface-2)">·</span> Empty — none found</span>
    </div>
    <div class="vhist-block">
      <div class="vhist-head">
        <h3>AI adoption by industry <span class="vhist-scope" id="vhistScope"></span></h3>
        <div class="seg-ctrl" id="vhistMetric">
          <button data-vm="n" class="on">Deployments</button>
          <button data-vm="proof_pct">Quantified&nbsp;%</button>
        </div>
      </div>
      <div class="vhist" id="vhist"></div>
    </div>
    <details class="tabletwin">
      <summary>Table view (industry × function)</summary>
      <table id="gridTableTwin">
        <thead><tr>
          <th data-k="v">Industry</th><th data-k="h">Function</th>
          <th data-k="n">Deployments</th><th data-k="withnum">With a number</th>
          <th data-k="pct">Numbers&nbsp;%</th><th data-k="verdict">Verdict</th>
        </tr></thead><tbody></tbody>
      </table>
    </details>
  </div>
</section>


<!-- ============ COMPARE (C1/D2) ============ -->
<section class="altitude" id="compare" data-alt="Compare">
  <div class="terr">
    <div class="head">
      <div>
        <h2>Compare — <span class="scope">side by side</span></h2>
        <p class="lede">Pick 2–5 companies to line up their AI footprint: deployments, maturity,
        quantified rate, momentum, peer percentiles. Best-in-row is highlighted. The URL is shareable.</p>
      </div>
    </div>
    <div class="cmp-pick">
      <input id="cmpSearch" class="filtersel" style="min-width:260px" placeholder="type a company name…" autocomplete="off">
      <div id="cmpChips" class="cmp-chips"></div>
    </div>
    <div id="cmpSuggest" class="cmp-suggest"></div>
    <div id="cmpVisual" class="cmp-visual"></div>
    <details class="tabletwin" id="cmpTableWrap" style="margin-top:26px" hidden>
      <summary>Exact values (table)</summary>
      <table id="cmpTable"></table>
    </details>
  </div>
</section>

<!-- ============ COMPANY PAGE (D1) ============ -->
<section class="altitude" id="company" data-alt="Company">
  <div class="terr" id="companyBody"></div>
</section>

<!-- ============ TRENDS (D5 — deployments over time) ============ -->
<section class="altitude" id="trends" data-alt="Trends">
  <div class="terr">
    <div class="head">
      <div>
        <h2>Momentum — <span class="scope">AI deployment over time</span></h2>
        <p class="lede">When disclosed deployments were announced. Overlay any industry or country
        to compare trajectories — who moved early, who is catching up. Undated rows
        (<span id="undatedPct"></span>) are excluded from the curve, shown as a caveat.</p>
      </div>
      <div class="controls">
        <select id="trendOverlay" class="filtersel"><option value="">World total</option></select>
      </div>
    </div>
    <div class="trendwrap"><svg id="trendsvg" viewBox="0 0 900 380" role="img" aria-label="Deployments over time"></svg></div>
    <p class="footnote">Dates from company disclosures. Forward years (2027+) are announced future plans.
    Half the register is undated and omitted here — the curve is a lower bound on activity, not a census.</p>
  </div>
</section>

<!-- ============ HYPE DETECTOR (D6 — talk vs substantiation) ============ -->
<section class="altitude" id="hype" data-alt="Hype">
  <div class="terr">
    <div class="head">
      <div>
        <h2>Adoption — <span class="scope">vs. evidence, by industry</span></h2>
        <p class="lede">The study's central question, by sector. For each industry: how much is
        <b>announced</b> (deployments found) vs <b>substantiated</b> (rows citing a value metric).
        A short bar under a long one means few value metrics were found for that sector — a gap to explore, not a verdict.</p>
      </div>
    </div>
    <div id="hypeMoneyPending"></div>
    <div class="vhist" id="hypeChart" style="margin-top:24px"></div>
    <p class="footnote">Substantiation = share of that industry's deployments that cite any value number
    (self-reported, rarely audited). Investment figures regex-extracted from disclosure text.</p>
  </div>
</section>

<!-- ============ SILENT COMPANIES (D4 — the prospect list) ============ -->
<!-- ============ USE-CASE CATALOG (D9) ============ -->
<section class="altitude" id="usecases" data-alt="Use cases">
  <div class="terr">
    <div class="head">
      <div>
        <h2>Use-case catalog — <span class="scope">what AI actually does, by pattern</span></h2>
        <p class="lede">The register inverted: not "what does company X do" but "who runs claims automation,
        where, with what evidence". Each pattern shows its runners, industries, first-seen, and quantified rate.
        Click for runners, diffusion, and cross-industry transfer opportunities.</p>
      </div>
      <div class="controls">
        <select id="ucVert" class="filtersel"><option value="">All industries</option></select>
        <select id="ucSort" class="filtersel">
          <option value="runners">Most runners</option>
          <option value="proof_rate">Best quantified rate</option>
          <option value="first_seen">Earliest</option>
        </select>
      </div>
    </div>
    <div id="ucBars" class="uc-bars"></div>
    <div class="uc-cards" id="ucCards"></div>
  </div>
</section>

<!-- use-case detail -->
<section class="altitude" id="usecase" data-alt="Use case">
  <div class="terr" id="usecaseBody"></div>
</section>

<!-- vendor detail (D10) -->
<section class="altitude" id="vendor" data-alt="Vendor">
  <div class="terr" id="vendorBody"></div>
</section>

<!-- ============ COMPANIES (filterable list — question targets land here) ============ -->
<section class="altitude" id="companies" data-alt="Companies">
  <div class="terr">
    <div class="head">
      <div>
        <h2 id="companiesTitle">Companies</h2>
        <p class="lede" id="companiesLede"></p>
      </div>
      <div class="controls">
        <select id="companiesCC" class="filtersel"><option value="">All countries</option></select>
        <select id="companiesVert" class="filtersel"><option value="">All industries</option></select>
      </div>
    </div>
    <div class="tabletwin" style="margin-top:20px">
      <table id="companiesTable">
        <thead><tr>
          <th data-k="name">Company</th><th data-k="cc">Country</th><th data-k="vertical">Industry</th>
          <th data-k="deployments">Deploys</th><th data-k="confirmed">Confirmed</th>
          <th data-k="proof_rate">Quantified</th><th data-k="maturity">Maturity</th><th data-k="prospect_score">Prospect</th>
        </tr></thead><tbody></tbody>
      </table>
    </div>
    <p class="footnote" id="companiesCount"></p>
  </div>
</section>

<section class="altitude" id="silent" data-alt="Silent">
  <div class="terr">
    <div class="head">
      <div>
        <h2>The silent — <span class="scope">searched, nothing found yet</span></h2>
        <p class="lede">Companies in the searched universe with <b>no disclosed AI in our register yet</b>.
        Read this as a <b>coverage floor, not a verdict</b>: "silent" can mean genuinely no AI (often
        investment holdings), OR a company our sweep hasn't reached in its native-language sources.
        We re-sweep these continuously — a name here is a lead to verify, not a proven absence.
        Peer median = typical disclosed deployments among same-industry, same-country rivals.</p>
      </div>
      <div class="controls">
        <select id="silentCC" class="filtersel"><option value="">All countries</option></select>
        <select id="silentSector" class="filtersel"><option value="">All sectors</option></select>
      </div>
    </div>
    <div id="silentSizePending"></div>
    <div class="tabletwin" style="margin-top:20px">
      <table id="silentTable">
        <thead><tr>
          <th data-k="name">Company</th><th data-k="cc">Country</th>
          <th data-k="sector">Sector</th><th data-k="mktcap">Market cap</th>
          <th data-k="peer_median">Peer median</th>
        </tr></thead><tbody></tbody>
      </table>
    </div>
    <p class="footnote" id="silentCount"></p>
  </div>
</section>

<!-- ============ ALTITUDE 3 — STREET (slide-in company panel) ============ -->
<div id="scrim"></div>
<aside id="panel" aria-hidden="true" role="dialog" aria-label="Companies in this cell">
  <div class="phead">
    <button class="pclose" id="pclose" aria-label="Close">✕</button>
    <div class="pcrumb" id="pcrumb"></div>
    <h3 id="ptitle"></h3>
    <p class="psub" id="psub"></p>
  </div>
  <div class="pbody" id="pbody"></div>
</aside>

<div class="tip" id="tip"></div>

<script id="atlas-data" type="application/json">{DATA_JSON}</script>
<script id="questions-data" type="application/json">{QUESTIONS_JSON}</script>
<script id="qstats-data" type="application/json">{QSTATS_JSON}</script>
<script id="world-data" type="application/json">{WORLD_JSON}</script>
<script>{D3}</script>
<script>{TOPO}</script>
<script>
const ATLAS = JSON.parse(document.getElementById('atlas-data').textContent);

/* accent-blind normaliser for all search boxes: "loreal" matches "L'Oréal" */
const deaccent = s => (s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();

/* reflect current sort on a sortable table's headers (arrow + active state) */
function markSort(tableSel, key, dir) {{
  const t=document.querySelector(tableSel); if(!t) return;
  t.querySelectorAll('th[data-k]').forEach(th=>{{
    th.classList.toggle('sort-asc',  th.dataset.k===key && dir>0);
    th.classList.toggle('sort-desc', th.dataset.k===key && dir<0);
  }});
}}

/* theme toggle — persists, respects prior choice */
const root = document.documentElement;
const tBtn = document.getElementById('themeToggle');
const tIcon = document.getElementById('themeIcon'), tLab = document.getElementById('themeLabel');
const ICON_SUN=`{icon('sun',15)}`, ICON_MOON=`{icon('moon',15)}`;
function applyTheme(t) {{
  root.setAttribute('data-theme', t);
  tIcon.innerHTML = t === 'dark' ? ICON_SUN : ICON_MOON;
  tLab.textContent  = t === 'dark' ? 'Light' : 'Dark';
  if (!themeReady) return;   // skip repaint during first-load call (marks not built yet)
  // repaint colour-bearing marks that read CSS vars at draw time
  if (worldRendered) {{ paintBubbles(); refreshSizeLegend(); }}
  renderBars();
  if (document.getElementById('a2').classList.contains('active')) renderGrid();
}}
let themeReady = false;
// light is the default; the toggle switches to dark for the session
applyTheme('light');
themeReady = true;
tBtn.addEventListener('click', () => applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));

/* altitude navigation (stub for now — A0 only wired) */
const crumbs = document.getElementById('crumbs');
function goAltitude(id, label) {{
  document.querySelectorAll('.altitude').forEach(s => s.classList.toggle('active', s.id === id));
  crumbs.innerHTML = id === 'a0'
    ? '<span class="here">Orbit</span>'
    : '<span style="cursor:pointer" onclick="goAltitude(\\'a0\\')">Orbit</span> <span class="sep">›</span> <span class="here">'+label+'</span>';
  window.scrollTo({{top:0, behavior:'smooth'}});
}}
function toWorld() {{ goAltitude('a1','World'); renderWorld(); }}
document.getElementById('descend').addEventListener('click', toWorld);
document.getElementById('descendTop').addEventListener('click', toWorld);

/* ============ hash routing (WAY 1 — one file, shareable #routes) ============ */
const ROUTES = {{
  'a0':     {{hash:'',        label:'Orbit',  show:()=>goAltitude('a0')}},
  'a1':     {{hash:'/world',  label:'World',  show:toWorld}},
  'a2':     {{hash:'/grid',   label:'Grid',   show:()=>{{ if(!ATLAS.grid_global) return; gridScope=null; document.getElementById('scopeName')&&(document.getElementById('scopeName').textContent='the world'); const b=document.getElementById('backWorld'); if(b)b.hidden=true; renderGrid(); goAltitude('a2','World grid'); }}}},
  'trends': {{hash:'/trends', label:'Trends', show:renderTrends}},
  'hype':   {{hash:'/hype',   label:'Adoption',   show:renderHype}},
  'compare':{{hash:'/compare',label:'Compare',show:renderCompare}},
  'usecases':{{hash:'/usecases',label:'Use cases',show:renderUsecases}},
  'companies':{{hash:'/companies',label:'Companies',show:renderCompanies}},
  'silent': {{hash:'/silent', label:'Silent list', show:renderSilent}},
}};
function goRoute(id) {{ const r=ROUTES[id]; if(!r) return; if(location.hash!=='#'+r.hash) location.hash=r.hash; else applyRoute(); }}
function goCompany(slug) {{ location.hash='/company/'+slug; }}

/* ============ global company omnibox (jump-to-company from anywhere) ============ */
(function initOmni() {{
  const inp=document.getElementById('omni'), box=document.getElementById('omniResults');
  if(!inp||!box) return;
  const CCNAME={{}}; ATLAS.countries.forEach(c=>CCNAME[c.cc]=c.name);
  // search the WHOLE register — silent companies included (they have detail pages too)
  let hits=[], active=-1;
  function score(c,q) {{
    const n=deaccent(c.name), i=n.indexOf(q);
    if(i<0) return -1;
    return (i===0?0:(/\\s/.test(n[i-1])?1:2));   // prefix < word-start < mid-word
  }}
  function search(raw) {{
    const q=deaccent(raw.trim());
    if(q.length<2) {{ hits=[]; box.classList.remove('open'); box.innerHTML=''; return; }}
    hits=ATLAS.companies.map(c=>({{c,s:score(c,q)}})).filter(x=>x.s>=0)
      .sort((a,b)=> a.s-b.s || a.c.name.length-b.c.name.length || a.c.name.localeCompare(b.c.name))
      .slice(0,12).map(x=>x.c);
    active = hits.length?0:-1;
    render();
  }}
  function render() {{
    if(!hits.length) {{ box.innerHTML='<div class="omni-empty">No company matches — search covers the full register, so a miss means it is not in our universe yet.</div>'; box.classList.add('open'); return; }}
    box.innerHTML=hits.map((c,i)=>`<div class="omni-opt${{i===active?' active':''}}" role="option" data-slug="${{c.slug}}">`
      + `<span class="on">${{esc(c.name)}}</span>`
      + (c.silent?'<span class="osilent">no AI found yet</span>':'')
      + `<span class="om">${{esc(CCNAME[c.cc]||c.cc)}}${{c.vertical?' · '+esc(c.vertical):''}}</span></div>`).join('');
    box.classList.add('open');
  }}
  function go(i) {{ const c=hits[i]; if(!c) return; close(); inp.value=''; goCompany(c.slug); }}
  function close() {{ box.classList.remove('open'); box.innerHTML=''; hits=[]; active=-1; }}
  inp.addEventListener('input',()=>search(inp.value));
  inp.addEventListener('focus',()=>{{ if(inp.value.trim().length>=2) search(inp.value); }});
  inp.addEventListener('keydown',e=>{{
    if(!hits.length && e.key!=='Escape') return;
    if(e.key==='ArrowDown'){{ e.preventDefault(); active=(active+1)%hits.length; render(); }}
    else if(e.key==='ArrowUp'){{ e.preventDefault(); active=(active-1+hits.length)%hits.length; render(); }}
    else if(e.key==='Enter'){{ e.preventDefault(); go(active<0?0:active); }}
    else if(e.key==='Escape'){{ close(); inp.blur(); }}
  }});
  box.addEventListener('mousedown',e=>{{ const o=e.target.closest('.omni-opt'); if(!o) return; e.preventDefault();
    close(); inp.value=''; goCompany(o.dataset.slug); }});
  inp.addEventListener('blur',()=>setTimeout(close,150));
}})();

function applyRoute() {{
  const h=location.hash.replace(/^#/,'');
  if(h.startsWith('/company/')) {{ renderCompany(h.slice('/company/'.length));
    document.querySelectorAll('.navlink').forEach(a=>a.classList.remove('on')); return; }}
  if(h.startsWith('/usecase/')) {{ renderUsecase(decodeURIComponent(h.slice('/usecase/'.length).split('?')[0]));
    document.querySelectorAll('.navlink').forEach(a=>a.classList.toggle('on', a.dataset.route==='usecases'));
    setTimeout(()=>injectNext('usecases'),0); return; }}
  if(h.startsWith('/vendor/')) {{ renderVendor(decodeURIComponent(h.slice('/vendor/'.length).split('?')[0]));
    document.querySelectorAll('.navlink').forEach(a=>a.classList.remove('on')); return; }}
  const base=h.split('?')[0];
  const id=(Object.keys(ROUTES).find(k=>ROUTES[k].hash===base)) || 'a0';
  ROUTES[id].show();
  document.querySelectorAll('.navlink').forEach(a=>a.classList.toggle('on', a.dataset.route===id));
  // N2: every answer view ends with a Next block (home 'a0' excluded — it IS the menu)
  if(id!=='a0') setTimeout(()=>injectNext(id), 0);
}}
window.addEventListener('hashchange', applyRoute);

/* ============ N1/N2/N3 — question navigation engine ============ */
const QREG = JSON.parse(document.getElementById('questions-data').textContent);
const QSTATS = JSON.parse(document.getElementById('qstats-data').textContent);
const QBYID = {{}}; QREG.questions.forEach(q=>QBYID[q.id]=q);
const PERSONA_ICON = {{investor:`{icon('trending-up',15)}`, vendor:`{icon('search',15)}`, strategist:`{icon('scale',15)}`, consultant:`{icon('target',15)}`, exploring:`{icon('compass',15)}`}};
function renderQMenu() {{
  const host=document.getElementById('qmenu'); if(!host) return;
  host.innerHTML = QREG.groups.map(g=>{{
    const qs=QREG.questions.filter(q=>q.personas.includes(g.persona));
    if(!qs.length) return '';
    const links=qs.map(q=>{{
      const stat = q.teaser_metric && QSTATS[q.teaser_metric]!=null ? `<span class="qn">${{QSTATS[q.teaser_metric].toLocaleString()}}</span>` : '';
      if(q.enabled===false) return `<span class="qlink soon"><span class="qt">${{esc(q.text)}}</span><span class="qsoon">soon</span></span>`;
      return `<a class="qlink" href="${{q.target}}"><span class="qt">${{esc(q.text)}}</span>${{stat}}</a>`;
    }}).join('');
    return `<div class="qgroup"><div class="qgroup-h">${{PERSONA_ICON[g.persona]||''}} ${{esc(g.header)}}</div>${{links}}</div>`;
  }}).join('');
}}
// N2 — resolve the Next block for the current view/URL
function questionForHash(h) {{
  // match by target base path (ignore params) — first question whose target base matches
  const base=h.split('?')[0];
  return QREG.questions.find(q=>q.target.split('?')[0]===base);
}}
function currentParams() {{ const q=location.hash.split('?')[1]||''; return new URLSearchParams(q); }}
function renderNextBlock(viewId) {{
  // pick followups: from the matched question, else the view default
  const q=questionForHash('#'+location.hash.replace(/^#/,''));
  let ids = q ? q.followups : (QREG.view_default_followups[viewId]||[]);
  ids=(ids||[]).slice(0,3);
  if(!ids.length) return '';
  const p=currentParams(); const ctx=[]; ['country','vertical'].forEach(k=>{{ if(p.get(k)) ctx.push([k,p.get(k)]); }});
  const links=ids.map(id=>{{
    const fq=QBYID[id]; if(!fq) return '';
    // context substitution: carry country/vertical into the followup target if it accepts them
    let tgt=fq.target;
    ctx.forEach(([k,v])=>{{ if((fq.params_open||[]).includes(k)) tgt += (tgt.includes('?')?'&':'?')+k+'='+encodeURIComponent(v); }});
    const soon = fq.enabled===false;
    return soon ? `<span style="opacity:.5">${{esc(fq.text)}} (soon)</span>` : `<a href="${{tgt}}">${{esc(fq.text)}}</a>`;
  }}).filter(Boolean).join('');
  return `<div class="nextblock"><div class="nb-h">Next</div><div class="nb-links">${{links}}</div></div>`;
}}
// inject a Next block at the end of an altitude's .terr/.world container
function injectNext(viewId) {{
  const sec=document.querySelector('.altitude.active .terr, .altitude.active .world');
  if(!sec) return;
  let nb=sec.querySelector(':scope > .nextblock'); if(nb) nb.remove();
  const html=renderNextBlock(viewId); if(html) sec.insertAdjacentHTML('beforeend', html);
  injectCoverageNote(viewId, sec);
}}
// Standing coverage disclaimer on views where an ABSENCE is shown. The tool is a lower bound:
// "not found" never means "does not exist" — later passes may add more (the silent resweep proved it).
const ABSENCE_VIEWS={{silent:1,companies:1,hype:1,a2:1,usecases:1}};
function injectCoverageNote(viewId, sec) {{
  sec.querySelectorAll(':scope > .coverage-note').forEach(e=>e.remove());
  if(!ABSENCE_VIEWS[viewId]) return;
  sec.insertAdjacentHTML('beforeend',
    `<p class="coverage-note">Coverage note: figures reflect what our sourcing has found so far — a lower bound, not a census. "Not found" does not mean "does not exist"; our search can miss, and later passes may add more.</p>`);
}}

/* ============ D1 COMPANY PAGE ============ */
const MLAB={{L0:'Silent',L1:'Claimed',L2:'Pilot',L3:'Operating',L4:'Industrialized'}};
let COMP_BY_SLUG=null, ROWS_BY_COMPANY=null, SLUG_BY_NAME=null;
function indexCompanies() {{
  if(COMP_BY_SLUG) return;
  COMP_BY_SLUG={{}}; SLUG_BY_NAME={{}}; ATLAS.companies.forEach(c=>{{COMP_BY_SLUG[c.slug]=c; SLUG_BY_NAME[c.name+'|'+c.cc]=c.slug;}});
  ROWS_BY_COMPANY={{}};
  Object.values(ATLAS.cells).forEach(list=>list.forEach(e=>{{
    (ROWS_BY_COMPANY[e.company]=ROWS_BY_COMPANY[e.company]||[]).push(e);
  }}));
}}
function renderCompany(slug) {{
  indexCompanies(); goAltitude('company','Company');
  const c=COMP_BY_SLUG[slug];
  const host=document.getElementById('companyBody');
  if(!c){{ host.innerHTML='<h2>Company not found</h2><p class="lede">No entry for this slug. <a href="#/silent">Silent list</a> · <a href="#/grid">Grid</a></p>'; return; }}
  const cname=ATLAS.countries.find(x=>x.cc===c.cc); const cn=cname?cname.name:c.cc;
  const rr=(ROWS_BY_COMPANY[c.name]||[]).filter(e=>true);
  const bench=c.benchmarks||{{}};
  const findings=(ATLAS.findings||[]).filter(f=>f.cc===c.cc && f.vertical && c.vertical &&
      (f.vertical.toLowerCase().includes(c.vertical.toLowerCase().split(' ')[0]) || (c.vertical||'').toLowerCase().includes((f.vertical||'').toLowerCase().split(' ')[0])));
  crumbs.innerHTML='<span style="cursor:pointer" onclick="goRoute(\\'a0\\')">Orbit</span> <span class="sep">›</span> <span class="here">'+esc(c.name)+'</span>';
  const mlvl=c.maturity||'L0';
  const pctBar=(lab,val)=> val==null?'' : `<div class="benchrow"><span>${{lab}}</span><div class="benchtrack"><div class="benchfill" style="width:${{val}}%"></div></div><b>${{val}}${{val!=null?'th':''}}</b></div>`;
  let html=`
    <a class="backup" href="#/grid">← back to grid</a>
    <div class="cprofile">
      <div>
        <h2 style="margin:0">${{esc(c.name)}}</h2>
        <p class="lede" style="margin-top:6px">${{cn}} · ${{esc(c.vertical||'—')}}${{c.silent?' · <b>silent (no disclosed AI)</b>':''}}</p>
      </div>
      <div class="mbadge m-${{mlvl}}" title="${{(c.maturity_evidence||[]).join(', ')}}">${{mlvl}} · ${{MLAB[mlvl]}}</div>
    </div>`;
  if(c.silent){{
    html+=`<p class="footnote">Searched under the evidence gate; no AI deployment disclosed. Its peers may be active — see the <a href="#/grid">grid</a>.</p>`;
    host.innerHTML=html; return;
  }}
  // KPI row
  const fmtB=v=>v?(v>=1e9?'$'+(v/1e9).toFixed(0)+'B':v>=1e6?'$'+(v/1e6).toFixed(0)+'M':'$'+v):'—';
  html+=`<div class="ckpis">
    <div class="ckpi"><div class="n">${{c.deployments}}</div><div class="l">deployments</div></div>
    <div class="ckpi"><div class="n">${{c.confirmed}}</div><div class="l">confirmed</div></div>
    <div class="ckpi"><div class="n">${{Math.round((c.proof_rate||0)*100)}}%</div><div class="l">cite a number</div></div>
    <div class="ckpi"><div class="n">${{c.first_seen||'—'}}</div><div class="l">first seen</div></div>
    ${{c.mktcap?`<div class="ckpi"><div class="n">${{fmtB(c.mktcap)}}</div><div class="l">market cap</div></div>`:''}}
    ${{c.per_bn_revenue!=null?`<div class="ckpi"><div class="n">${{c.per_bn_revenue}}</div><div class="l">deploys / $B rev</div></div>`:''}}
  </div>`;
  // vendor stack (D10)
  if(c.stack&&c.stack.length){{
    if(!VENDOR_BY_SLUG){{ VENDOR_BY_SLUG={{}}; (ATLAS.vendors||[]).forEach(v=>VENDOR_BY_SLUG[v.slug]=v); }}
    const slugify=s=>s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    html+=`<h3 class="csub">AI stack</h3><div class="vchips">`+c.stack.map(vn=>{{
      const sl=slugify(vn); return VENDOR_BY_SLUG[sl]?`<a class="vchip" href="#/vendor/${{sl}}">${{esc(vn)}}</a>`:`<span class="vchip">${{esc(vn)}}</span>`;
    }}).join('')+`</div>`;
  }}
  // benchmarks
  if(bench.global_vertical){{
    const b=bench.global_vertical;
    html+=`<h3 class="csub">Percentile vs ${{b.n}} global ${{esc(c.vertical)}} peers</h3><div class="benchbox">
      ${{pctBar('deployments',b.deployments)}}${{pctBar('confirmed',b.confirmed)}}${{pctBar('quantified rate',b.proof_rate)}}</div>`;
  }}
  // deployments list
  html+=`<h3 class="csub">${{rr.length}} disclosed deployment${{rr.length!==1?'s':''}}</h3><div class="cdeps">`;
  rr.sort((a,b)=>(a.existence==='confirmed'?0:1)-(b.existence==='confirmed'?0:1));
  html+=rr.map(e=>{{
    const ex=e.existence||'none', tier=(e.tier||'').trim().toUpperCase();
    const val=(e.value||'').trim(); const showVal=val && !/^(none|n\\/a|—|-)/i.test(val);
    return `<div class="co"><div class="top"><span class="name">${{esc(e.use?e.use.split(';')[0].slice(0,70):'—')}}</span>
      <span class="exist"><span class="glyph ${{ex==='confirmed'?'g-proven':(ex==='claimed'?'g-talk':'')}}">${{ex==='confirmed'?'●':(ex==='claimed'?'○':'·')}}</span></span></div>
      <div class="meta">${{['P','I','S'].includes(tier)?`<span class="chip ${{tier}}">tier ${{tier}}</span>`:''}}
        ${{showVal?`<span class="val">${{esc(val)}}</span>`:''}}
        ${{e.date&&e.date!=='missing'?`<span>${{esc(e.date)}}</span>`:''}}
        ${{e.fresh&&e.fresh!=='fresh'&&e.fresh!=='undated'?`<span class="freshbadge fb-${{e.fresh}}" title="verified ${{esc(e.date||'?')}} — ${{e.fresh}}, re-check before citing">{icon('triangle-alert',12)}</span>`:''}}
        <span style="flex:1"></span>${{srcLinks(e.url)}}</div></div>`;
  }}).join('')+`</div>`;
  // findings flags
  if(findings.length){{
    html+=`<h3 class="csub">Context &amp; flags</h3><div class="cflags">`+findings.map(f=>
      `<div class="cflag">{icon('flag',14)} ${{esc(f.finding)}} ${{f.url?`<a class="src" href="${{esc(f.url)}}" target="_blank" rel="noopener">source ↗</a>`:''}}</div>`).join('')+`</div>`;
  }}
  html+=`<p class="footnote">Every number above traces to a source link or a documented rule (maturity: hover the badge). Data version ${{ATLAS.meta?ATLAS.meta.schema_version:''}}.</p>`;
  html+=`<button class="expbtn" onclick='exportBriefing("company",COMP_BY_SLUG["${{slug}}"])'>{icon('download',15)} Generate briefing (markdown)</button>`;
  host.innerHTML=html;
  window.scrollTo({{top:0,behavior:'smooth'}});
}}

/* ============ D7 markdown briefing export ============ */
/* D7 — markdown briefing export (client-side, download) */
function exportBriefing(kind, payload) {{
  const dv=ATLAS.meta?ATLAS.meta.schema_version:'2.0';
  let md=`# KARTO AI Atlas — ${{kind}} briefing\\n\\n_Data version ${{dv}} · ${{ATLAS.global.deployments}} deployments · ${{ATLAS.global.countries}} countries_\\n\\n`;
  if(kind==='company'){{
    const c=payload; md+=`## ${{c.name}}\\n- ${{c.cc}} · ${{c.vertical||'—'}}\\n- Maturity: **${{c.maturity}}** (${{(c.maturity_evidence||[]).join(', ')}})\\n`;
    md+=`- Deployments: ${{c.deployments}} · Confirmed: ${{c.confirmed}} · Quantified rate: ${{Math.round((c.proof_rate||0)*100)}}%\\n- Momentum: ${{c.momentum||'—'}} (first seen ${{c.first_seen||'—'}})\\n\\n`;
    const rr=(ROWS_BY_COMPANY[c.name]||[]);
    md+=`### Deployments (${{rr.length}})\\n`+rr.map((e,i)=>`${{i+1}}. ${{(e.use||'').split(';')[0]}} — ${{e.existence}}${{e.date&&e.date!=='missing'?' ('+e.date+')':''}} [${{e.url||'no source'}}]`).join('\\n');
  }} else if(kind==='compare'){{
    const cmp=payload; md+=`## Comparison\\n\\n| Metric | ${{cmp.entities.map(c=>c.name).join(' | ')}} |\\n|---|${{cmp.entities.map(()=>'---').join('|')}}|\\n`;
    cmp.metrics.forEach(m=>{{ md+=`| ${{m.label}} | ${{m.values.join(' | ')}} |\\n`; }});
  }}
  const blob=new Blob([md],{{type:'text/markdown'}}); const url=URL.createObjectURL(blob);
  const a=document.createElement('a'); a.href=url; a.download=`karto-${{kind}}-briefing.md`; a.click(); URL.revokeObjectURL(url);
}}

/* ============ C1 COMPARE (pure fn) + D2 view ============ */
function compareCompanies(slugs) {{
  indexCompanies();
  const cs=slugs.map(s=>COMP_BY_SLUG[s]).filter(Boolean);
  const g=c=>c.benchmarks&&c.benchmarks.global_vertical;
  const M={{L0:0,L1:1,L2:2,L3:3,L4:4}};
  return {{ entities:cs, metrics:[
    {{key:'deployments', label:'Deployments', values:cs.map(c=>c.deployments), best:'max'}},
    {{key:'confirmed', label:'Confirmed', values:cs.map(c=>c.confirmed), best:'max'}},
    {{key:'proof_rate', label:'Quantified rate', values:cs.map(c=>Math.round((c.proof_rate||0)*100)+'%'), raw:cs.map(c=>c.proof_rate||0), best:'max'}},
    {{key:'maturity', label:'Maturity', values:cs.map(c=>c.maturity||'L0'), raw:cs.map(c=>M[c.maturity]||0), best:'max'}},
    {{key:'momentum', label:'Momentum', values:cs.map(c=>(c.momentum||'—').replace(/,/g,', ')), best:'none'}},
    {{key:'first_seen', label:'First seen', values:cs.map(c=>c.first_seen||'—'), raw:cs.map(c=>c.first_seen||9999), best:'min'}},
    {{key:'pct_dep', label:'Pctile (peers)', values:cs.map(c=>g(c)?g(c).deployments+'th':'—'), raw:cs.map(c=>g(c)?g(c).deployments:-1), best:'max'}},
  ]}};
}}
let cmpSlugs=[];
function renderCompare() {{
  goAltitude('compare','Compare'); indexCompanies();
  const q=location.hash.split('?')[1]||'';
  const p=new URLSearchParams(q); const c=p.get('c');
  if(c && !cmpSlugs.length) cmpSlugs=c.split(',').filter(s=>COMP_BY_SLUG[s]).slice(0,5);
  const search=document.getElementById('cmpSearch');
  if(!search.dataset.wired){{
    search.dataset.wired='1';
    search.addEventListener('input',()=>cmpSuggest(search.value));
    search.addEventListener('blur',()=>setTimeout(()=>document.getElementById('cmpSuggest').innerHTML='',200));
  }}
  drawCompare();
}}
function cmpSuggest(q) {{
  const box=document.getElementById('cmpSuggest'); q=deaccent(q.trim());
  if(q.length<2){{ box.innerHTML=''; return; }}
  const hits=ATLAS.companies.filter(c=>!c.silent && deaccent(c.name).includes(q)).slice(0,8);
  box.innerHTML=hits.map(c=>`<div class="cmp-opt" onclick="cmpAdd('${{c.slug}}')">${{esc(c.name)}} <span style="color:var(--muted)">· ${{c.cc}} · ${{esc(c.vertical||'')}}</span></div>`).join('');
}}
function cmpAdd(slug) {{
  if(cmpSlugs.length>=5 || cmpSlugs.includes(slug)) return;
  cmpSlugs.push(slug); document.getElementById('cmpSearch').value=''; document.getElementById('cmpSuggest').innerHTML='';
  syncCmpUrl(); drawCompare();
}}
function cmpRemove(slug) {{ cmpSlugs=cmpSlugs.filter(s=>s!==slug); syncCmpUrl(); drawCompare(); }}
function syncCmpUrl() {{ const h='/compare'+(cmpSlugs.length?'?c='+cmpSlugs.join(','):''); if(location.hash!=='#'+h) history.replaceState(null,'','#'+h); }}
// CVD-safe qualitative series colors (Okabe–Ito), fixed order — color follows the entity slot
const CMP_SERIES=['#0072B2','#E69F00','#009E73','#CC79A7','#D55E00'];
// the 6 numeric axes that form the radar (ordinal maturity + percentile + first-seen year)
const RADAR_AXES=['deployments','confirmed','proof_rate','maturity','pct_dep','first_seen'];
// build the overlaid-radar SVG: one polygon per company, axes normalized to the set max
function radarSVG(cmp, byKey) {{
  const axes=RADAR_AXES.map(k=>byKey[k]).filter(Boolean);
  const N=axes.length, S=340, C=S/2, R=S/2-46;
  // per-axis max across the compared companies (min 1 to avoid /0)
  const rawOf=m=>(m.raw||m.values.map(Number)).map(v=>(typeof v==='number'&&!isNaN(v))?v:0);
  const maxes=axes.map(m=>Math.max(1,...rawOf(m)));
  // first-seen is a year: range-normalize across the set so the spread is visible (year/max would flatten to ~1)
  const yr=byKey['first_seen']?rawOf(byKey['first_seen']).filter(v=>v>0&&v<9999):[];
  const yMin=yr.length?Math.min(...yr):0, yMax=yr.length?Math.max(...yr):1;
  const normVal=(m,v)=>{{
    if(m.key==='first_seen'){{ if(!(v>0&&v<9999)) return 0;   // undated -> at centre
      return (yMax===yMin)?0.6:0.15+0.85*(v-yMin)/(yMax-yMin); }}   // earliest near centre, latest at edge
    return v/maxes[axes.indexOf(m)];
  }};
  const ang=i=>(-Math.PI/2)+i*(2*Math.PI/N);              // start at top, clockwise
  const pt=(i,t)=>[C+R*t*Math.cos(ang(i)), C+R*t*Math.sin(ang(i))];
  // rings + spokes
  let grid='';
  [0.25,0.5,0.75,1].forEach(t=>{{
    const pts=axes.map((_,i)=>pt(i,t).map(n=>n.toFixed(1)).join(',')).join(' ');
    grid+=`<polygon class="radar-ring" points="${{pts}}"/>`;
  }});
  axes.forEach((_,i)=>{{ const[x,y]=pt(i,1); grid+=`<line class="radar-axis" x1="${{C}}" y1="${{C}}" x2="${{x.toFixed(1)}}" y2="${{y.toFixed(1)}}"/>`; }});
  // axis labels (short) + the axis MAX (the scale endpoint) just outside the outer ring
  const short={{deployments:'Deployments',confirmed:'Confirmed',proof_rate:'Quantified',maturity:'Maturity',pct_dep:'Peer pctile',first_seen:'First seen'}};
  // plain-language definition per axis — shown on hover of the category label
  const AXDEF={{
    deployments:'Distinct AI deployments found for the company in our register (a lower bound — our sourcing can miss).',
    confirmed:'Deployments with confirmed existence (independently evidenced), as opposed to only claimed.',
    proof_rate:'Share of the company’s deployments that cite a value number (revenue, cost, %). Higher = more measured.',
    maturity:'Maturity level L0–L4: L0 silent · L1 claimed · L2 pilot · L3 operating · L4 industrialized.',
    pct_dep:'Percentile rank on deployment count vs global peers in the same industry. 99th = top 1%.',
    first_seen:'Year the company’s first AI deployment appears in our sources. Position is relative to the set (earliest near centre, latest at the edge).'
  }};
  const fmtV=(k,v)=> k==='proof_rate' ? Math.round(v*100)+'%' : k==='maturity' ? ('L'+v) : k==='pct_dep' ? (v+'th') : k==='first_seen' ? ((v>0&&v<9999)?String(v):'—') : String(v);
  // scale-endpoint caption per axis (a year axis shows its span, not a "max")
  const tipLab=(m)=> m.key==='first_seen' ? (yr.length?(yMin===yMax?String(yMin):yMin+'–'+yMax):'—') : ('max '+fmtV(m.key,maxes[axes.indexOf(m)]));
  let labs='';
  axes.forEach((m,i)=>{{ const[x,y]=pt(i,1.18); const a=ang(i);
    const anchor=Math.abs(Math.cos(a))<0.3?'middle':(Math.cos(a)>0?'start':'end');
    labs+=`<g class="radar-cat" tabindex="0"><title>${{esc(short[m.key]||m.label)}} — ${{esc(AXDEF[m.key]||'')}}</title>`
       +  `<text class="radar-alab" x="${{x.toFixed(1)}}" y="${{(y).toFixed(1)}}" text-anchor="${{anchor}}">${{short[m.key]||esc(m.label)}}</text>`
       +  `<text class="radar-max" x="${{x.toFixed(1)}}" y="${{(y+12).toFixed(1)}}" text-anchor="${{anchor}}">${{esc(tipLab(m))}}</text></g>`;
  }});
  // one shape per company; the value at each vertex appears only on hover of that point
  let shapes='', pts_g='';
  cmp.entities.forEach((c,ci)=>{{
    const col=CMP_SERIES[ci];
    const coords=axes.map((m,i)=>{{ const t=Math.max(0,Math.min(1, normVal(m, rawOf(m)[ci]))); return {{p:pt(i,t),t}}; }});
    const pts=coords.map(o=>o.p.map(n=>n.toFixed(1)).join(',')).join(' ');
    shapes+=`<polygon class="radar-shape" points="${{pts}}" stroke="${{col}}" fill="${{col}}"/>`;
    // per-vertex hover group: transparent hit target + dot + value label (hidden until hover)
    pts_g+=coords.map((o,i)=>{{ const a=ang(i); const lx=o.p[0]+9*Math.cos(a), ly=o.p[1]+9*Math.sin(a);
      const anchor=Math.abs(Math.cos(a))<0.3?'middle':(Math.cos(a)>0?'start':'end');
      const val=esc(fmtV(axes[i].key, rawOf(axes[i])[ci]));
      return `<g class="radar-pt" tabindex="0"><title>${{esc(c.name)}} · ${{esc(short[axes[i].key]||axes[i].label)}}: ${{val}}</title>`
        + `<circle class="radar-hit" cx="${{o.p[0].toFixed(1)}}" cy="${{o.p[1].toFixed(1)}}" r="12"/>`
        + `<circle class="radar-dot" cx="${{o.p[0].toFixed(1)}}" cy="${{o.p[1].toFixed(1)}}" fill="${{col}}"/>`
        + `<text class="radar-vlab" x="${{lx.toFixed(1)}}" y="${{(ly+3).toFixed(1)}}" text-anchor="${{anchor}}" fill="${{col}}">${{val}}</text></g>`;
    }}).join('');
  }});
  const vlabs=pts_g;
  shapes+=vlabs;   // draw value labels last so they sit above the fills
  return `<svg viewBox="0 0 ${{S}} ${{S}}" role="img" aria-label="Radar comparing ${{cmp.entities.map(c=>c.name).join(', ')}} across ${{axes.map(m=>m.label).join(', ')}}">`
    + grid + labs + shapes + `</svg>`;
}}
function drawCompare() {{
  document.getElementById('cmpChips').innerHTML=cmpSlugs.map((s,i)=>{{
    const c=COMP_BY_SLUG[s];
    return `<span class="cmp-chip"><span class="sw" style="display:inline-block;width:9px;height:9px;border-radius:2px;background:${{CMP_SERIES[i]}};margin-right:6px;vertical-align:middle"></span>${{esc(c.name)}} <b onclick="cmpRemove('${{s}}')">✕</b></span>`;
  }}).join('');
  const host=document.getElementById('cmpVisual'), tbl=document.getElementById('cmpTable'), wrap=document.getElementById('cmpTableWrap');
  if(cmpSlugs.length<2){{ host.innerHTML='<p class="cmp-note" style="padding:16px 0">Add at least two companies to compare.</p>'; wrap.hidden=true; return; }}
  const cmp=compareCompanies(cmpSlugs);
  const byKey={{}}; cmp.metrics.forEach(m=>byKey[m.key]=m);
  const bestOf=m=>{{ if(!m||m.best==='none') return -1;
    const arr=m.raw||m.values.map(Number); const valid=arr.map((v,i)=>[v,i]).filter(x=>typeof x[0]==='number'&&!isNaN(x[0]));
    if(!valid.length) return -1; valid.sort((a,b)=>m.best==='max'?b[0]-a[0]:a[0]-b[0]); return valid[0][1]; }};

  host.innerHTML = `<div class="cmp-radar">${{radarSVG(cmp,byKey)}}</div>`
    + `<div class="cmp-side">`
    +   `<div class="cmp-legend">` + cmp.entities.map((c,i)=>
          `<div class="k"><span class="sw" style="background:${{CMP_SERIES[i]}}"></span><a class="colink" href="#/company/${{c.slug}}">${{esc(c.name)}}</a></div>`).join('') + `</div>`
    +   `<p class="cmp-note">Each axis is normalized to the companies shown, so the radar compares shape and balance — read exact numbers in the table below. First-seen is positioned relative to the set (earliest near centre, latest at the edge).</p>`
    + `</div>`;

  // ---- exact-values table twin (a11y + precise numbers), collapsed by default ----
  let html='<thead><tr><th>Metric</th>'+cmp.entities.map(c=>`<th><a class="colink" href="#/company/${{c.slug}}">${{esc(c.name)}}</a></th>`).join('')+'</tr></thead><tbody>';
  cmp.metrics.forEach(m=>{{ const best=bestOf(m);
    html+=`<tr><td>${{m.label}}</td>`+m.values.map((v,i)=>`<td class="${{i===best?'cmp-best':''}}">${{v}}</td>`).join('')+'</tr>';
  }});
  tbl.innerHTML=html+'</tbody>'; wrap.hidden=false;

  let btn=document.getElementById('cmpExport');
  if(!btn){{ btn=document.createElement('button'); btn.id='cmpExport'; btn.className='expbtn'; btn.innerHTML='{icon("download",15)} Generate briefing (markdown)'; wrap.after(btn); }}
  btn.onclick=()=>exportBriefing('compare',compareCompanies(cmpSlugs));
}}

/* ============ D5 TRENDS VIEW (deployments over time, D3 line) ============ */
let trendsInit=false;
function renderTrends() {{
  goAltitude('trends','Trends');
  const sel=document.getElementById('trendOverlay');
  if(!trendsInit) {{
    trendsInit=true;
    ATLAS.momentum_country.slice().sort((a,b)=>a.name.localeCompare(b.name))
      .forEach(c=>sel.insertAdjacentHTML('beforeend',`<option value="cc:${{c.cc}}">${{c.name}}</option>`));
    ATLAS.momentum_vertical.forEach(v=>sel.insertAdjacentHTML('beforeend',`<option value="v:${{esc(v.v)}}">${{esc(v.v)}}</option>`));
    sel.onchange=drawTrends;
    // global undated %
    const tot=ATLAS.global.deployments, dated=ATLAS.timeline_global.reduce((s,t)=>s+t.n,0);
    document.getElementById('undatedPct').textContent = Math.round(100*(tot-dated)/tot)+'% undated';
  }}
  drawTrends();
}}
function drawTrends() {{
  const sel=document.getElementById('trendOverlay').value;
  let series=ATLAS.timeline_global.map(t=>({{year:t.year,n:t.n}}));
  let label='World total';
  if(sel.startsWith('cc:')) {{ const c=ATLAS.momentum_country.find(x=>x.cc===sel.slice(3)); series=c.by_year; label=c.name; }}
  else if(sel.startsWith('v:')) {{ const v=ATLAS.momentum_vertical.find(x=>x.v===sel.slice(2)); series=v.by_year; label=v.v; }}
  series=series.filter(p=>p.year>=2018 && p.year<=2027);   // focus the AI era, drop long tails
  const svg=d3.select('#trendsvg'); svg.selectAll('*').remove();
  const W=900,H=380,m={{t:24,r:24,b:40,l:48}};
  const xs=d3.scaleLinear().domain(d3.extent(series,d=>d.year)).range([m.l,W-m.r]);
  const ys=d3.scaleLinear().domain([0,d3.max(series,d=>d.n)||1]).nice().range([H-m.b,m.t]);
  // gridlines + axes (recessive)
  const yt=ys.ticks(5);
  svg.append('g').selectAll('line').data(yt).join('line')
    .attr('x1',m.l).attr('x2',W-m.r).attr('y1',d=>ys(d)).attr('y2',d=>ys(d))
    .attr('stroke',cssv('--grid')).attr('stroke-width',.5);
  svg.append('g').selectAll('text').data(yt).join('text').attr('x',m.l-8).attr('y',d=>ys(d)+3)
    .attr('text-anchor','end').attr('font-size',11).attr('fill',cssv('--muted')).attr('font-family','var(--font-ui)').text(d=>d);
  svg.append('g').selectAll('text').data(series).join('text').attr('x',d=>xs(d.year)).attr('y',H-m.b+18)
    .attr('text-anchor','middle').attr('font-size',11).attr('fill',cssv('--muted')).attr('font-family','var(--font-ui)').text(d=>("'"+String(d.year).slice(2)));
  const line=d3.line().x(d=>xs(d.year)).y(d=>ys(d.n)).curve(d3.curveMonotoneX);
  const area=d3.area().x(d=>xs(d.year)).y0(H-m.b).y1(d=>ys(d.n)).curve(d3.curveMonotoneX);
  svg.append('path').datum(series).attr('d',area).attr('fill',cssv('--accent')).attr('opacity',.10);
  svg.append('path').datum(series).attr('d',line).attr('fill','none').attr('stroke',cssv('--accent')).attr('stroke-width',2.5);
  svg.selectAll('circle.pt').data(series).join('circle').attr('class','pt')
    .attr('cx',d=>xs(d.year)).attr('cy',d=>ys(d.n)).attr('r',3.5).attr('fill',cssv('--accent'))
    .append('title').text(d=>`${{d.year}}: ${{d.n}}`);
  svg.append('text').attr('x',m.l).attr('y',m.t-6).attr('font-size',13).attr('font-family','var(--font-head)')
    .attr('fill',cssv('--ink')).text(label+' — deployments announced per year');
}}

/* ============ D6 HYPE DETECTOR VIEW ============ */
function renderHype() {{
  goAltitude('hype','Adoption');
  // money-IN axis (committed capital) is pending until the Step 12 dedicated collection.
  // Marker keys off data presence (global.commitments) so it self-clears when data lands.
  const mp=document.getElementById('hypeMoneyPending');
  if(mp) mp.innerHTML = (ATLAS.global.commitments||0)===0
    ? `<div class="pending">{icon('info',14)} Committed-capital data (investments, acquisitions, partnerships) is still being collected. Shown here: disclosed value claims only.</div>`
    : '';
  const host=document.getElementById('hypeChart'); if(!host||!ATLAS.hype_by_vertical) return;
  const data=[...ATLAS.hype_by_vertical].filter(h=>h.announced>0).sort((a,b)=>b.announced-a.announced);
  const max=Math.max(...data.map(h=>h.announced));
  host.innerHTML = data.map(h=>{{
    const aw=100*h.announced/max, sw=100*h.substantiated/max;
    const rate=Math.round(h.substantiation_rate*100);
    const warn = rate<15;
    return `<div class="hyperow" title="${{esc(h.v)}} — ${{h.announced}} announced, ${{h.substantiated}} with a value number (${{rate}}%)${{h.investments?', '+h.investments+' investment claims':''}}">
      <div class="vname">${{esc(h.v)}}</div>
      <div class="hypetrack">
        <div class="hypebar announced" style="width:${{aw}}%"></div>
        <div class="hypebar substant ${{warn?'warn':''}}" style="width:${{sw}}%"></div>
      </div>
      <div class="vval">${{rate}}<span class="u">%</span></div>
    </div>`;
  }}).join('')
    + `<div class="hypekey"><span><i class="sw-ann"></i> announced (deployments)</span><span><i class="sw-sub"></i> substantiated (cite a number)</span></div>`;
}}

/* ============ D4 SILENT COMPANIES VIEW ============ */
let silentSort={{k:'peer_median',dir:-1}};
/* ============ D10 VENDOR PAGE ============ */
let VENDOR_BY_SLUG=null;
function renderVendor(slug) {{
  goAltitude('vendor','Vendor'); indexCompanies();
  if(!VENDOR_BY_SLUG){{ VENDOR_BY_SLUG={{}}; (ATLAS.vendors||[]).forEach(v=>VENDOR_BY_SLUG[v.slug]=v); }}
  const v=VENDOR_BY_SLUG[slug]; const host=document.getElementById('vendorBody');
  if(!v){{ host.innerHTML='<h2>Vendor not found</h2><p class="lede"><a href="#/usecases">← use case catalog</a></p>'; return; }}
  crumbs.innerHTML='<span style="cursor:pointer" onclick="goRoute(\\'a0\\')">Orbit</span> <span class="sep">›</span> <span class="here">'+esc(v.vendor)+'</span>';
  const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
  let html=`<a class="backup" href="#/usecases">← use case catalog</a>
    <h2 style="margin:0">${{esc(v.vendor)}} <span style="font-size:14px;color:var(--muted)">· ${{esc(v.type)}}</span></h2>
    <p class="lede" style="margin-top:6px">Named on <b>${{v.deployments}}</b> deployments across <b>${{v.customers}}</b> companies,
    ${{v.verticals.length}} industries, ${{v.countries.length}} countries. Source-linked — nobody else has this map.</p>
    <div class="ckpis">
      <div class="ckpi"><div class="n">${{v.customers}}</div><div class="l">customers</div></div>
      <div class="ckpi"><div class="n">${{v.deployments}}</div><div class="l">deployments</div></div>
      <div class="ckpi"><div class="n">${{v.verticals.length}}</div><div class="l">industries</div></div>
    </div>
    <h3 class="csub">Customers (from the register)</h3><div class="uc-runners">`
    + (v.customer_list||[]).map(cn=>{{ const co=ATLAS.companies.find(c=>c.name===cn); const slug=co?co.slug:null;
        return slug?`<a class="colink" href="#/company/${{slug}}">${{esc(cn)}}</a>`:`<span>${{esc(cn)}}</span>`; }}).join(' · ')
    + `</div><p class="footnote">Industries: ${{v.verticals.map(esc).join(' · ')}}. Disclosure bias: vendors are named selectively — "not disclosed" is common and never inferred.</p>`;
  host.innerHTML=html; window.scrollTo({{top:0,behavior:'smooth'}});
}}

/* ============ D9 USE-CASE CATALOG + DETAIL ============ */
let ucWired=false;
function renderUsecases() {{
  goAltitude('usecases','Use cases'); indexCompanies();
  const vSel=document.getElementById('ucVert'), sSel=document.getElementById('ucSort');
  if(!ucWired){{ ucWired=true;
    const vs=[...new Set((ATLAS.usecases||[]).flatMap(u=>u.verticals))].sort();
    vs.forEach(v=>vSel.insertAdjacentHTML('beforeend',`<option value="${{esc(v)}}">${{esc(v)}}</option>`));
    vSel.onchange=sSel.onchange=drawUsecases;
    // honor ?vertical= / ?gap= from question targets
    const p=currentParams(); if(p.get('vertical')) vSel.value=p.get('vertical');
  }}
  drawUsecases();
}}
// ranked bars: how many companies we FOUND running each pattern (a lower bound, not a census).
// light bar = companies (runners); dark inset = how many of those cite a value number. Both plain counts.
function drawUcBars(list) {{
  const host=document.getElementById('ucBars'); if(!host) return;
  const rows=[...list].sort((a,b)=>b.runners-a.runners);
  if(!rows.length){{ host.innerHTML=''; return; }}
  const max=Math.max(...rows.map(u=>u.runners),1);
  host.innerHTML =
    `<div class="uc-bkey"><span class="k"><span class="sw" style="background:color-mix(in srgb,var(--accent) 26%,var(--surface))"></span>companies found running it</span>`
    + `<span class="k"><span class="sw" style="background:var(--accent)"></span>of those, cite a value number</span></div>`
    + rows.map(u=>{{
      const w=Math.max(2,100*u.runners/max), wn=100*(u.with_value_number||0)/max;
      return `<a class="uc-brow" href="#/usecase/${{encodeURIComponent(u.pattern_id)}}" title="${{esc(u.name)}} — ${{u.runners}} companies found; ${{u.with_value_number||0}} cite a value number">`
        + `<span class="uc-bname">${{esc(u.name)}}</span>`
        + `<span class="uc-btrack"><span class="uc-bfill" style="width:${{w}}%"></span><span class="uc-bnum" style="width:${{wn}}%"></span></span>`
        + `<span class="uc-bval"><b>${{u.runners}}</b> · ${{u.with_value_number||0}}</span></a>`;
    }}).join('')
    + `<p class="cmp-note" style="margin-top:10px">Each row: companies our sourcing <b>found</b> running the pattern · how many of those cite a value number. A lower bound, not a census.</p>`;
}}
function drawUsecases() {{
  const v=document.getElementById('ucVert').value, sort=document.getElementById('ucSort').value||'runners';
  let list=[...(ATLAS.usecases||[])];
  if(v) list=list.filter(u=>u.verticals.includes(v));
  drawUcBars(list);
  list.sort((a,b)=> sort==='first_seen' ? ((a.first_seen||9999)-(b.first_seen||9999)) : (b[sort]-a[sort]));
  document.getElementById('ucCards').innerHTML = list.map(u=>`
    <a class="uc-card" href="#/usecase/${{encodeURIComponent(u.pattern_id)}}">
      <div class="uc-name">${{esc(u.name)}}</div>
      <div class="uc-desc">${{esc(u.description||'')}}</div>
      <div class="uc-stats">
        <span><b>${{u.runners}}</b> runners</span>
        <span><b>${{u.verticals.length}}</b> industries</span>
        <span><b>${{Math.round((u.proof_rate||0)*100)}}%</b> quantified</span>
        ${{u.first_seen?`<span>since <b>${{u.first_seen}}</b></span>`:''}}
      </div>
    </a>`).join('') || '<p class="lede">No patterns for this filter.</p>';
}}
// diffusion timeline strip: SVG, year to scale on x, a dot per country at first_seen,
// dots stacked vertically on year collisions, small labels. Discrete dots (no curve) =
// honest about estimate-grade data. Shows the shape a sorted list hides.
const DIFF_SHORT={{'United Arab Emirates':'UAE','United States':'USA','United Kingdom':'UK','South Korea':'S. Korea','South Africa':'S. Africa','Saudi Arabia':'Saudi Arabia','Netherlands':'Netherlands'}};
function diffusionStrip(diff) {{
  const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
  const pts=diff.filter(d=>d.first_year).map(d=>{{const nm=names[d.cc]||d.cc; return {{cc:d.cc, y:d.first_year, name:DIFF_SHORT[nm]||nm}};}});
  if(!pts.length) return '';
  const yrs=pts.map(p=>p.y); let y0=Math.min(...yrs), y1=Math.max(...yrs);
  if(y1===y0) y1=y0+1;                       // avoid zero-width axis for single-year patterns
  const W=760, padL=40, padR=120, axisY=54, rowH=22, dotR=5;
  const x=y=>padL+(y-y0)/(y1-y0)*(W-padL-padR);
  // group by year, stack within a year
  const byYear={{}}; pts.sort((a,b)=>a.y-b.y||a.name.localeCompare(b.name));
  pts.forEach(p=>{{ (byYear[p.y]=byYear[p.y]||[]).push(p); }});
  const maxStack=Math.max(...Object.values(byYear).map(a=>a.length));
  const H=axisY+maxStack*rowH+16;
  let dots='', labels='';
  Object.entries(byYear).forEach(([yr,arr])=>{{
    arr.forEach((p,i)=>{{
      const cx=x(+yr), cy=axisY+8+i*rowH;
      dots+=`<line x1="${{cx}}" y1="${{axisY}}" x2="${{cx}}" y2="${{cy}}" stroke="var(--hair)" stroke-width="1"/>`
          + `<circle cx="${{cx}}" cy="${{cy}}" r="${{dotR}}" fill="var(--accent)"/>`;
      labels+=`<text x="${{cx+9}}" y="${{cy+4}}" font-size="11.5" fill="var(--ink-2)" font-family="var(--font-ui)">${{esc(p.name)}}</text>`;
    }});
  }});
  // year ticks (integer years across the span)
  let ticks='';
  for(let yy=y0; yy<=y1; yy++){{
    const tx=x(yy);
    ticks+=`<line x1="${{tx}}" y1="${{axisY-5}}" x2="${{tx}}" y2="${{axisY}}" stroke="var(--muted)" stroke-width="1"/>`
         + `<text x="${{tx}}" y="${{axisY-10}}" text-anchor="middle" font-size="11" fill="var(--muted)" font-family="var(--font-ui)" font-variant-numeric="tabular-nums">${{yy}}</text>`;
  }}
  return `<svg class="diffsvg" viewBox="0 0 ${{W}} ${{H}}" width="100%" role="img" aria-label="Diffusion timeline: first-seen year by country">
    <line x1="${{padL}}" y1="${{axisY}}" x2="${{W-padR+40}}" y2="${{axisY}}" stroke="var(--grid)" stroke-width="1"/>
    ${{ticks}}${{dots}}${{labels}}
  </svg>
  <p class="coverage-note" style="margin-top:6px">First-seen years are estimates from disclosure dates; spacing is to scale.</p>`;
}}

function renderUsecase(pid) {{
  goAltitude('usecase','Use case'); indexCompanies();
  const u=(ATLAS.usecases||[]).find(x=>x.pattern_id===pid);
  const host=document.getElementById('usecaseBody');
  if(!u){{ host.innerHTML='<h2>Pattern not found</h2><p class="lede"><a href="#/usecases">← use case catalog</a></p>'; return; }}
  crumbs.innerHTML='<span style="cursor:pointer" onclick="goRoute(\\'a0\\')">Orbit</span> <span class="sep">›</span> <span style="cursor:pointer" onclick="goRoute(\\'usecases\\')">Use cases</span> <span class="sep">›</span> <span class="here">'+esc(u.name)+'</span>';
  const transfer=(ATLAS.transfer_opportunities||[]).find(t=>t.pattern_id===pid);
  // runner rows: register rows tagged with this pattern -> company + cc
  let html=`<a class="backup" href="#/usecases">← use case catalog</a>
    <h2 style="margin:0">${{esc(u.name)}}</h2>
    <p class="lede" style="margin-top:6px">${{esc(u.description||'')}} · <b>${{u.runners}}</b> runners across <b>${{u.verticals.length}}</b> industries, <b>${{u.countries.length}}</b> countries${{u.first_seen?`, since <b>${{u.first_seen}}</b>`:''}}.</p>
    <div class="ckpis">
      <div class="ckpi"><div class="n">${{u.runners}}</div><div class="l">runners</div></div>
      <div class="ckpi"><div class="n">${{u.deployments}}</div><div class="l">deployments</div></div>
      <div class="ckpi"><div class="n">${{Math.round((u.proof_rate||0)*100)}}%</div><div class="l">cite a number</div></div>
      <div class="ckpi"><div class="n">${{u.first_seen||'—'}}</div><div class="l">first seen</div></div>
    </div>`;
  // diffusion timeline — horizontal strip, year-scaled x, one dot per country, stacked on ties
  if(u.diffusion&&u.diffusion.length){{
    html+=`<h3 class="csub">Diffusion (first seen by country — estimates)</h3>${{diffusionStrip(u.diffusion)}}`;
  }}
  // full deployment entries (same data as the register, entered by pattern instead of by company)
  const ents=(u.entries||[]).slice().sort((a,b)=>(a.existence==='confirmed'?0:1)-(b.existence==='confirmed'?0:1) || a.company.localeCompare(b.company));
  if(ents.length){{
    html+=`<h3 class="csub">${{ents.length}} deployment${{ents.length!==1?'s':''}}</h3><div class="cdeps">`
      + ents.map(e=>{{
        const ex=e.existence||'none', tier=(e.tier||'').trim().toUpperCase();
        const val=(e.value||'').trim(); const showVal=val && !/^(none|n\\/a|—|-)/i.test(val);
        const slug=SLUG_BY_NAME[e.company+'|'+e.cc];
        const nm=slug?`<a class="name colink" href="#/company/${{slug}}">${{esc(e.company)}}</a>`:`<span class="name">${{esc(e.company)}}</span>`;
        return `<div class="co"><div class="top">${{nm}} <span style="color:var(--muted);font-size:11.5px">· ${{esc(e.cc)}} · ${{esc(e.vertical||'')}}</span>`
          + `<span style="flex:1"></span><span class="exist"><span class="glyph ${{ex==='confirmed'?'g-proven':(ex==='claimed'?'g-talk':'')}}">${{ex==='confirmed'?'●':(ex==='claimed'?'○':'·')}}</span></span></div>`
          + `<div class="use">${{esc(e.use?e.use.split(';')[0]:'—')}}</div>`
          + `<div class="meta">${{['P','I','S'].includes(tier)?`<span class="chip ${{tier}}">tier ${{tier}}</span>`:''}}`
          + `${{showVal?`<span class="val">${{esc(val)}}</span>`:'<span class="val" style="opacity:.6">no value number</span>'}}`
          + `${{e.date&&e.date!=='missing'?`<span>${{esc(e.date)}}</span>`:''}}`
          + `<span style="flex:1"></span>${{srcLinks(e.url)}}</div></div>`;
      }}).join('')+`</div>`;
  }}
  html+=`<p class="footnote">Industries: ${{u.verticals.map(esc).join(' · ')}}. Entries are the same register rows, entered by pattern rather than by company — a lower bound on what our sourcing found.</p>`;
  // transfer opportunity
  if(transfer){{
    html+=`<h3 class="csub">Transfer opportunity</h3><div class="cflag" style="background:color-mix(in srgb,var(--v-unquantified) 10%,var(--surface))">
      Proven in <b>${{transfer.proven_in.map(esc).join(', ')}}</b> — <b>absent</b> in ${{transfer.absent_in.map(esc).join(', ')}}. Those are greenfield targets, with the proven industries as reference cases.</div>`;
  }}
  host.innerHTML=html; window.scrollTo({{top:0,behavior:'smooth'}});
}}

/* ============ COMPANIES filterable list (question targets) ============ */
let compSort={{k:'prospect_score',dir:-1}}, compWired=false;
const MLAB_SHORT={{L0:'L0',L1:'L1',L2:'L2',L3:'L3',L4:'L4'}};
function renderCompanies() {{
  goAltitude('companies','Companies'); indexCompanies();
  const p=currentParams();
  compSort.k = p.get('sort')||'prospect_score'; compSort.dir=-1;
  document.getElementById('companiesTitle').textContent =
    (p.get('existence')==='confirmed' && p.get('has_value_number')==='false') ? 'Confirmed AI, no value number' : 'Companies';
  document.getElementById('companiesLede').textContent =
    (p.get('existence')==='confirmed' && p.get('has_value_number')==='false')
    ? 'Companies running confirmed AI that disclose no value number — active but unmeasured. Sorted by prospect score.'
    : 'All companies with disclosed AI.';
  const ccSel=document.getElementById('companiesCC'), vSel=document.getElementById('companiesVert');
  if(!compWired){{ compWired=true;
    const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
    [...new Set(ATLAS.companies.filter(c=>!c.silent).map(c=>c.cc))].sort().forEach(cc=>ccSel.insertAdjacentHTML('beforeend',`<option value="${{cc}}">${{names[cc]||cc}}</option>`));
    ATLAS.verticals.forEach(v=>vSel.insertAdjacentHTML('beforeend',`<option value="${{esc(v)}}">${{esc(v)}}</option>`));
    ccSel.onchange=vSel.onchange=()=>drawCompanies();
    document.querySelectorAll('#companiesTable th').forEach(th=>th.addEventListener('click',()=>{{
      const k=th.dataset.k; compSort.dir=(compSort.k===k)?-compSort.dir:-1; compSort.k=k; drawCompanies(); }}));
  }}
  drawCompanies();
}}
function drawCompanies() {{
  const p=currentParams();
  const wantConf=p.get('existence')==='confirmed', wantNoNum=p.get('has_value_number')==='false';
  const cc=document.getElementById('companiesCC').value, vv2=document.getElementById('companiesVert').value;
  const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
  let rows=ATLAS.companies.filter(c=>!c.silent);
  if(wantConf) rows=rows.filter(c=>c.confirmed>0);
  if(wantNoNum) rows=rows.filter(c=>c.with_value_number===0);
  if(cc) rows=rows.filter(c=>c.cc===cc);
  if(vv2) rows=rows.filter(c=>c.vertical===vv2);
  rows.sort((a,b)=>{{ let A=a[compSort.k],B=b[compSort.k]; if(A==null)A=-1; if(B==null)B=-1;
    return ((typeof A==='string')?A.localeCompare(B):(A>B?1:A<B?-1:0))*compSort.dir; }});
  document.querySelector('#companiesTable tbody').innerHTML = rows.slice(0,300).map(c=>`<tr>
    <td><a class="colink" href="#/company/${{c.slug}}">${{esc(c.name)}}</a></td>
    <td>${{names[c.cc]||c.cc}}</td><td>${{esc(c.vertical||'—')}}</td>
    <td>${{c.deployments}}</td><td>${{c.confirmed}}</td><td>${{Math.round((c.proof_rate||0)*100)}}%</td>
    <td>${{MLAB_SHORT[c.maturity]||c.maturity||'—'}}</td><td>${{c.prospect_score!=null?c.prospect_score:'—'}}</td></tr>`).join('');
  document.getElementById('companiesCount').textContent =
    `${{rows.length}} compan${{rows.length===1?'y':'ies'}}${{rows.length>300?' (showing top 300)':''}}.`;
  markSort('#companiesTable', compSort.k, compSort.dir);
}}

function renderSilent() {{
  goAltitude('silent','Silent list');
  // size sort requested but size data pending (Step 12) -> visible fallback marker.
  // keys off data presence: any silent row carrying a size value clears it automatically.
  const wantSize=(currentParams().get('sort')==='size_desc');
  const hasSize=ATLAS.silent.some(s=>s.mktcap||s.revenue||s.employees);
  const smp=document.getElementById('silentSizePending');
  if(smp) smp.innerHTML = (wantSize && !hasSize)
    ? `<div class="pending">{icon('info',14)} <b>Size data pending</b> — sorted by <b>peer gap</b> (median deployments of same-industry rivals) instead of company size. The Step 12 enrichment flips this to a true size sort with zero code changes.</div>` : '';
  const ccSel=document.getElementById('silentCC'), secSel=document.getElementById('silentSector');
  if(ccSel && ccSel.options.length<2) {{
    const ccs=[...new Set(ATLAS.silent.map(s=>s.cc))].sort();
    const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
    ccs.forEach(cc=>ccSel.insertAdjacentHTML('beforeend',`<option value="${{cc}}">${{names[cc]||cc}}</option>`));
    const secs=[...new Set(ATLAS.silent.map(s=>s.sector).filter(Boolean))].sort();
    secs.forEach(s=>secSel.insertAdjacentHTML('beforeend',`<option value="${{esc(s)}}">${{esc(s)}}</option>`));
    ccSel.onchange=secSel.onchange=drawSilent;
    document.querySelectorAll('#silentTable th').forEach(th=>th.addEventListener('click',()=>{{
      const k=th.dataset.k; silentSort.dir=(silentSort.k===k)?-silentSort.dir:-1; silentSort.k=k; drawSilent();
    }}));
  }}
  // if the question asked for size_desc and size now exists, honor it (self-flips post-resweep)
  const hasSizeNow=ATLAS.silent.some(s=>s.mktcap);
  if(currentParams().get('sort')==='size_desc' && hasSizeNow && silentSort.k==='peer_median'){{ silentSort.k='mktcap'; silentSort.dir=-1; }}
  drawSilent();
}}
function fmtUSD(v){{ if(!v) return '—'; return v>=1e9?('$'+(v/1e9).toFixed(0)+'B'):v>=1e6?('$'+(v/1e6).toFixed(0)+'M'):('$'+v); }}
function drawSilent() {{
  const cc=document.getElementById('silentCC').value, sec=document.getElementById('silentSector').value;
  const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
  let rows=ATLAS.silent.filter(s=>(!cc||s.cc===cc)&&(!sec||s.sector===sec));
  rows.sort((a,b)=>{{ let A=a[silentSort.k],B=b[silentSort.k];
    if(A==null)A=-1; if(B==null)B=-1;
    return ((typeof A==='string')?A.localeCompare(B):(A>B?1:A<B?-1:0))*silentSort.dir; }});
  document.querySelector('#silentTable tbody').innerHTML = rows.map(s=>`<tr>
    <td><a class="colink" href="#/company/${{s.slug}}">${{esc(s.name)}}</a></td><td>${{names[s.cc]||s.cc}}</td><td>${{esc(s.sector||'—')}}</td>
    <td>${{fmtUSD(s.mktcap)}}</td><td>${{s.peer_median!=null?s.peer_median:'—'}}</td></tr>`).join('');
  document.getElementById('silentCount').textContent =
    `${{rows.length}} silent compan${{rows.length===1?'y':'ies'}} shown · ${{ATLAS.silent.length}} total searched with zero disclosed AI.`;
  markSort('#silentTable', silentSort.k, silentSort.dir);
}}

/* ============ A1 WORLD (D3) ============ */
const world = JSON.parse(document.getElementById('world-data').textContent);
const tip = document.getElementById('tip');
const cssv = n => getComputedStyle(root).getPropertyValue(n).trim();
let worldRendered = false, curMetric = 'density';

const METRIC_LABEL = {{density:'Density (confirmed / searched)', deployments:'Deployments found', proof_pct:'Cite a value number'}};

/* ============ A0 GLOBE — stylized rotating earth (world-map palette) ============ */
(function initGlobe() {{
  const GW=360, GC=GW/2, R=GC-14;
  const svg = d3.select('#globe').attr('viewBox', `0 0 ${{GW}} ${{GW}}`);
  const proj = d3.geoOrthographic().scale(R).translate([GC,GC]).clipAngle(90).rotate([-10, -12, 0]);
  const path = d3.geoPath(proj);
  const land = topojson.feature(world, world.objects.land);
  const grat = d3.geoGraticule10();

  svg.append('circle').attr('class','globe-halo').attr('cx',GC).attr('cy',GC).attr('r',R+8);
  svg.append('circle').attr('class','globe-sphere').attr('cx',GC).attr('cy',GC).attr('r',R);
  const gGrat = svg.append('path').attr('class','globe-grat');
  const gLand = svg.append('path').attr('class','globe-land');
  const gDots = svg.append('g');

  // one marker per surveyed country (echoes the world map — "deployed almost everywhere")
  const pts = ATLAS.countries.map(c=>({{cc:c.cc, ll:c.ll, dep:c.deployments}}));
  const rDot = d3.scaleSqrt().domain([0, d3.max(pts,d=>d.dep)]).range([1.6, 5]);

  function draw() {{
    gGrat.attr('d', path(grat));
    gLand.attr('d', path(land));
    const geoDist = d3.geoDistance;
    const center = [-proj.rotate()[0], -proj.rotate()[1]];
    const sel = gDots.selectAll('circle').data(pts);
    sel.join('circle')
      .attr('class', d=>{{ const back = geoDist(d.ll, center) > Math.PI/2; return 'globe-dot'+(back?' back':''); }})
      .attr('r', d=>rDot(d.dep))
      .each(function(d){{
        const xy = proj(d.ll); const el=d3.select(this);
        if(xy){{ el.attr('cx',xy[0]).attr('cy',xy[1]).style('display',null); }}
        else el.style('display','none');
      }});
  }}
  draw();
  window.__redrawGlobe = draw;   // repaint on theme change (colors read via CSS classes, but dots recompute)

  // slow auto-spin, pausable by drag
  let t0=null, spinning=true, raf=null;
  function tick(t) {{
    if(t0===null) t0=t;
    if(spinning) {{ const r=proj.rotate(); proj.rotate([r[0] + (t-t0)*0.006, r[1], r[2]]); draw(); }}
    t0=t; raf=requestAnimationFrame(tick);
  }}
  raf=requestAnimationFrame(tick);

  // interaction: click = descend to world map · drag = spin (disambiguated by movement)
  const wrap = document.getElementById('globeWrap');
  let dragging=false, last=null, moved=0;
  const DRAG_THRESH=6;   // px of total travel before it counts as a spin, not a click
  wrap.addEventListener('pointerdown', e=>{{
    dragging=true; spinning=false; moved=0; last=[e.clientX,e.clientY]; wrap.setPointerCapture(e.pointerId);
  }});
  wrap.addEventListener('pointermove', e=>{{
    if(!dragging)return;
    const dx=e.clientX-last[0], dy=e.clientY-last[1];
    moved += Math.abs(dx)+Math.abs(dy);
    if(moved>DRAG_THRESH) wrap.classList.add('dragging');
    const r=proj.rotate(); proj.rotate([r[0]+dx*0.4, r[1]-dy*0.4, r[2]]); last=[e.clientX,e.clientY]; draw();
  }});
  function release() {{
    if(!dragging) return;
    const wasClick = moved<=DRAG_THRESH;
    dragging=false; wrap.classList.remove('dragging');
    if(wasClick) {{ toWorld(); return; }}          // barely moved -> treat as a click -> descend
    setTimeout(()=>spinning=true, 2600);            // resume auto-spin after a real drag
  }}
  wrap.addEventListener('pointerup', release);
  wrap.addEventListener('pointercancel', ()=>{{ dragging=false; wrap.classList.remove('dragging'); setTimeout(()=>spinning=true,2600); }});
  wrap.addEventListener('keydown', e=>{{ if(e.key==='Enter'||e.key===' '){{ e.preventDefault(); toWorld(); }} }});
}})();

function densityColor(v, max) {{
  // sequential warm ramp, validated. map 0..max -> d2..d7
  const steps = ['--d2','--d3','--d4','--d5','--d6','--d7'].map(cssv);
  const t = max ? v/max : 0;
  const i = Math.min(steps.length-1, Math.floor(t*steps.length));
  return steps[i];
}}

let mapZoom = null, mapK = 1;
function renderWorld() {{
  if (worldRendered) {{ paintBubbles(); return; }}
  worldRendered = true;
  const svg = d3.select('#mapsvg');
  const W=960, H=480;
  const proj = d3.geoNaturalEarth1().fitExtent([[8,8],[W-8,H-8]], topojson.feature(world, world.objects.land));
  const path = d3.geoPath(proj);
  // everything that pans/zooms lives in one group
  const g = svg.append('g').attr('class','mapg');
  g.append('path').attr('class','graticule').attr('d', path(d3.geoGraticule10()));
  g.append('path').attr('class','land').attr('d', path(topojson.feature(world, world.objects.land)));
  g.append('g').attr('class','bubs');
  g.append('g').attr('class','labs');
  paintBubbles();

  // pan + zoom (Europe is a dense cluster — let people zoom in)
  mapZoom = d3.zoom().scaleExtent([1, 12])
    .translateExtent([[0,0],[W,H]]).extent([[0,0],[W,H]])
    .on('zoom', (ev)=>{{ mapK = ev.transform.k; g.attr('transform', ev.transform); rescaleMap(); }});
  svg.call(mapZoom).on('dblclick.zoom', null);   // dbl-click handled by our reset instead
  svg.on('dblclick', ()=> svg.transition().duration(450).call(mapZoom.transform, d3.zoomIdentity));
  wireZoomButtons(svg);

  refreshSizeLegend();
  buildWorldTable();
}}
// keep bubble/label/stroke sizes constant on screen regardless of zoom k
function rescaleMap() {{
  const svg = d3.select('#mapsvg');
  const maxDep = d3.max(ATLAS.countries, d=>d.deployments);
  const rS = d3.scaleSqrt().domain([0,maxDep]).range([0,34]);
  svg.selectAll('.bubs circle').attr('r', d=>rS(d.deployments)/mapK).attr('stroke-width', 1.5/mapK);
  svg.selectAll('.labs text').attr('font-size', (11/mapK)+'px')
     .attr('y', d=>d.xy[1]-rS(d.deployments)/mapK-4/mapK);
  svg.select('.graticule').attr('stroke-width', 0.4/mapK);
  svg.select('.land').attr('stroke-width', 0.6/mapK);
}}
function wireZoomButtons(svg) {{
  const z=(f)=>svg.transition().duration(300).call(mapZoom.scaleBy, f);
  const zi=document.getElementById('zoomIn'), zo=document.getElementById('zoomOut'), zr=document.getElementById('zoomReset');
  if(zi) zi.onclick=()=>z(1.6);
  if(zo) zo.onclick=()=>z(1/1.6);
  if(zr) zr.onclick=()=>svg.transition().duration(450).call(mapZoom.transform, d3.zoomIdentity);
}}

function refreshSizeLegend() {{
  const maxDep = d3.max(ATLAS.countries, d=>d.deployments);
  const rS = d3.scaleSqrt().domain([0,maxDep]).range([0,34]);
  const legvals = [50,200,500].filter(v=>v<=maxDep);
  const sl = d3.select('#sizeLegend'); sl.selectAll('*').remove();
  sl.append('span').text('deployments:').style('color',cssv('--muted'));
  const slh=70;
  const slsvg = sl.append('svg').attr('width',160).attr('height',slh);
  legvals.forEach(v=>{{
    const r=rS(v); const cx=r+2; const base=slh-4;
    slsvg.append('circle').attr('cx',cx).attr('cy',base-r).attr('r',r)
      .attr('fill','none').attr('stroke',cssv('--muted')).attr('stroke-width',1);
    slsvg.append('text').attr('x',cx).attr('y',base-2*r-4).attr('text-anchor','middle')
      .attr('font-size',10).attr('fill',cssv('--muted')).text(v);
  }});
}}

function paintBubbles() {{
  const svg = d3.select('#mapsvg');
  const W=960,H=480;
  const proj = d3.geoNaturalEarth1().fitExtent([[8,8],[W-8,H-8]], topojson.feature(world, world.objects.land));
  const maxDep = d3.max(ATLAS.countries, d=>d.deployments);
  const rS = d3.scaleSqrt().domain([0,maxDep]).range([0,34]);
  const maxMetric = d3.max(ATLAS.countries, d=>d[curMetric]);
  const cs = ATLAS.countries.map(d=>({{...d, xy: proj(d.ll)}})).filter(d=>d.xy);

  const k = mapK || 1;
  const bl = svg.select('.bubs');
  const j = bl.selectAll('circle').data(cs, d=>d.cc);
  j.join(
    enter => enter.append('circle').attr('class','bub')
      .attr('cx',d=>d.xy[0]).attr('cy',d=>d.xy[1])
      .on('mousemove', showTip).on('mouseleave', hideTip)
      .on('click', (e,d)=>descendCountry(d)),
    update => update
  ).attr('r', d=>rS(d.deployments)/k).attr('stroke-width', 1.5/k)
   .transition().duration(400)
      .attr('fill', d=>densityColor(d[curMetric], maxMetric));

  // labels only for the biggest few (avoid clutter — selective, per anti-patterns)
  const top = [...cs].sort((a,b)=>b.deployments-a.deployments).slice(0,6);
  const ll = svg.select('.labs');
  const lj = ll.selectAll('text').data(top, d=>d.cc);
  lj.join(
    enter=>enter.append('text').attr('class','bub-label').attr('text-anchor','middle')
      .attr('x',d=>d.xy[0]).text(d=>d.cc),
    u=>u, ex=>ex.remove()
  ).attr('y',d=>d.xy[1]-rS(d.deployments)/k-4/k).attr('font-size',(11/k)+'px');
}}

function showTip(e,d) {{
  tip.innerHTML = `<h4>${{d.name}}</h4>
    <div class="r"><span>deployments</span><b>${{d.deployments}}</b></div>
    <div class="r"><span>companies</span><b>${{d.companies}}/${{d.searched}}</b></div>
    <div class="r"><span>density</span><b>${{d.density}}×</b></div>
    <div class="r"><span>carry a number</span><b>${{d.proof_pct}}%</b></div>
    <div class="hint">click to descend →</div>`;
  tip.style.opacity=1;
  const pad=14; let x=e.clientX+pad, y=e.clientY+pad;
  if (x+240>innerWidth) x=e.clientX-240; if (y+140>innerHeight) y=e.clientY-140;
  tip.style.left=x+'px'; tip.style.top=y+'px';
}}
function hideTip() {{ tip.style.opacity=0; }}

/* metric toggle — repaints whichever view is showing */
document.getElementById('metricCtrl').addEventListener('click', e=>{{
  const b=e.target.closest('button'); if(!b) return;
  document.querySelectorAll('#metricCtrl button').forEach(x=>x.classList.toggle('on', x===b));
  curMetric=b.dataset.m; paintBubbles(); renderBars();
}});

/* view toggle — Map ⇄ Ranked bars (two linked views, one metric) */
let curView='map';
document.getElementById('viewCtrl').addEventListener('click', e=>{{
  const b=e.target.closest('button'); if(!b) return;
  document.querySelectorAll('#viewCtrl button').forEach(x=>x.classList.toggle('on', x===b));
  curView=b.dataset.view;
  const mapOn = curView==='map';
  document.getElementById('mapView').hidden = !mapOn;
  document.getElementById('barsView').hidden = mapOn;
  document.querySelector('.legend').style.display = mapOn ? 'flex' : 'none';
  if(!mapOn) renderBars();
}});

const METRIC_UNIT = {{density:'×', deployments:'', proof_pct:'%'}};
function renderBars() {{
  const host=document.getElementById('barsView'); if(host.hidden) return;
  const rows=[...ATLAS.countries].sort((a,b)=>b[curMetric]-a[curMetric]);
  const max=d3.max(rows, d=>d[curMetric])||1;
  const unit=METRIC_UNIT[curMetric];
  host.innerHTML = rows.map(d=>{{
    const w=Math.max(2, 100*d[curMetric]/max);
    const col=densityColor(d[curMetric], max);
    return `<div class="barrow" onclick='__descend("${{d.cc}}")' title="${{d.name}} — click to descend">
      <div class="barname">${{d.name}}</div>
      <div class="bartrack"><div class="bar" style="width:${{w}}%;background:${{col}}"></div></div>
      <div class="barval">${{d[curMetric]}}<span class="u">${{unit}}</span></div>
    </div>`;
  }}).join('');
}}

/* table twin */
let tSort={{k:'deployments',dir:-1}};
function buildWorldTable() {{
  const tb=document.querySelector('#worldTable tbody');
  const rows=[...ATLAS.countries].sort((a,b)=>(a[tSort.k]>b[tSort.k]?1:-1)*tSort.dir);
  tb.innerHTML=rows.map(d=>`<tr onclick='__descend("${{d.cc}}")'>
    <td>${{d.name}}</td><td>${{d.deployments}}</td><td>${{d.companies}}</td>
    <td>${{d.confirmed}}</td><td>${{d.density}}</td><td>${{d.proof_pct}}</td></tr>`).join('');
  markSort('#worldTable', tSort.k, tSort.dir);
}}
document.querySelectorAll('#worldTable th').forEach(th=>th.addEventListener('click',()=>{{
  const k=th.dataset.k; tSort.dir = (tSort.k===k)? -tSort.dir : -1; tSort.k=k; buildWorldTable();
}}));

/* ============ A2 TERRITORY (decision grid) ============ */
let gridScope = null;   // null = world, else cc
let gridMode = 'verdict';
// 4-state verdict_v2 (B3). ◍ = confirmed-but-unquantified (real activity, no numbers).
const VERDICT_GLYPH = {{proven:'●', active:'◐', unquantified:'◍', talk:'○', empty:'·',
                        strong:'●'}};  // 'strong' alias for any stale refs
const VERDICT_CLASS = {{proven:'v-proven', active:'v-active', unquantified:'v-unquantified',
                        talk:'v-talk', empty:'empty', strong:'v-proven'}};
const VLAB4 = {{proven:'Proven', active:'Active', unquantified:'Unquantified', talk:'Unverified', strong:'Proven'}};
const vv = c => c.verdict_v2 || c.verdict;   // prefer 4-state, fall back

function descendCountry(d) {{
  gridScope = d ? d.cc : null;
  document.getElementById('scopeName').textContent = d ? d.name : 'the world';
  document.getElementById('backWorld').hidden = !d;   // only show when scoped to a country
  renderGrid();
  goAltitude('a2', d ? d.name : 'World grid');
  // breadcrumb: Orbit › World › [Country]
  crumbs.innerHTML = '<span style="cursor:pointer" onclick="goAltitude(\\'a0\\')">Orbit</span> <span class="sep">›</span>'
    + '<span style="cursor:pointer" onclick="backToWorld()">World</span> <span class="sep">›</span>'
    + '<span class="here">'+(d?d.name:'Grid')+'</span>';
}}
window.__descend = cc => descendCountry(ATLAS.countries.find(c=>c.cc===cc));
function backToWorld() {{ goAltitude('a1','World'); renderWorld(); }}
document.getElementById('backWorld').addEventListener('click', backToWorld);

function gridData() {{
  return gridScope ? (ATLAS.grid_by_country[gridScope]||[]) : ATLAS.grid_global;
}}
function renderGrid() {{
  const g = gridData();
  const cells = {{}}; let maxN=0;
  g.forEach(c=>{{ cells[c.v+'|'+c.h]=c; if(c.n>maxN)maxN=c.n; }});
  // only show verticals that have any deployment in this scope, keep global order
  const activeV = ATLAS.verticals.filter(v => ATLAS.horizontals.some(h=>cells[v+'|'+h]));
  const H = ATLAS.horizontals;
  const seq = ['--d2','--d3','--d4','--d5','--d6','--d7'].map(cssv);

  let html = '<thead><tr><th></th>' + H.map((h,ci)=>`<th class="col" data-ci="${{ci}}"><span>${{h}}</span></th>`).join('') + '</tr></thead><tbody>';
  activeV.forEach((v,ri)=>{{
    html += `<tr><th class="row" data-ri="${{ri}}" title="${{v}}">${{v}}</th>`;
    H.forEach((h,ci)=>{{
      const c = cells[v+'|'+h];
      if(!c){{ html += '<td class="empty"></td>'; return; }}
      const attrs = `data-v="${{v}}" data-h="${{h}}" data-ri="${{ri}}" data-ci="${{ci}}"`;
      if(gridMode==='verdict'){{
        const V=vv(c);
        html += `<td class="cell ${{VERDICT_CLASS[V]}}" ${{attrs}}>`
              + `<span class="glyph g-${{V}}">${{VERDICT_GLYPH[V]}}</span>`
              + `<div class="cnt">${{c.n}}</div></td>`;
      }} else {{
        const t = maxN? c.n/maxN : 0;
        const col = seq[Math.min(seq.length-1, Math.floor(t*seq.length))];
        const light = t>0.55; // dark fill -> light text
        html += `<td class="cell" style="background:${{col}};color:${{light?'#fff':'var(--ink)'}}" ${{attrs}}>`
              + `<div class="cnt" style="opacity:1;font-size:12px">${{c.n}}</div></td>`;
      }}
    }});
    html += '</tr>';
  }});
  html += '</tbody>';
  const t = document.getElementById('gridTable'); t.innerHTML = html;
  document.getElementById('verdictKey').style.display = gridMode==='verdict' ? 'flex' : 'none';
  // cell interactions
  t.querySelectorAll('td.cell').forEach(td=>{{
    td.addEventListener('mouseenter', ()=>emphasize(t, td.dataset.ri, td.dataset.ci));
    td.addEventListener('mousemove', e=>{{
      const v=td.dataset.v, h=td.dataset.h, c=cells[v+'|'+h];
      tip.innerHTML = `<h4>${{v}}</h4><div class="r"><span>${{h}}</span><b>${{c.n}}</b></div>`
        + `<div class="r"><span>with a number</span><b>${{c.withnum||0}} (${{c.n?Math.round(100*(c.withnum||0)/c.n):0}}%)</b></div>`
        + (gridMode==='verdict'?`<div class="r"><span>verdict</span><b class="g-${{vv(c)}}">${{VLAB4[vv(c)]||vv(c)}}</b></div>`:'')
        + `<div class="hint">click for companies →</div>`;
      tip.style.opacity=1; let x=e.clientX+14,y=e.clientY+14;
      if(x+230>innerWidth)x=e.clientX-230; if(y+120>innerHeight)y=e.clientY-120;
      tip.style.left=x+'px'; tip.style.top=y+'px';
    }});
    td.addEventListener('mouseleave', ()=>{{ hideTip(); }});
    td.addEventListener('click', ()=>openCell(td.dataset.v, td.dataset.h));
  }});
  t.addEventListener('mouseleave', ()=>clearEmph(t));
  buildGridTwin();
  renderVHist();
}}
function emphasize(table, ri, ci) {{
  table.classList.add('emph');
  table.querySelectorAll('.lit').forEach(el=>el.classList.remove('lit'));
  table.querySelectorAll(`td.cell[data-ri="${{ri}}"], td.cell[data-ci="${{ci}}"]`).forEach(el=>el.classList.add('lit'));
  const rh=table.querySelector(`th.row[data-ri="${{ri}}"]`); if(rh)rh.classList.add('lit');
  const ch=table.querySelector(`th.col[data-ci="${{ci}}"]`); if(ch)ch.classList.add('lit');
}}
function clearEmph(table) {{ table.classList.remove('emph'); table.querySelectorAll('.lit').forEach(el=>el.classList.remove('lit')); }}

/* per-vertical histogram — compare AI adoption across industries (respects country scope) */
let vhistMetric='n';
function vhistData() {{
  return gridScope ? (ATLAS.vert_totals_by_country[gridScope]||[]) : ATLAS.vert_totals_global;
}}
function renderVHist() {{
  const host=document.getElementById('vhist'); if(!host) return;
  const data=[...vhistData()].sort((a,b)=> b[vhistMetric]-a[vhistMetric] || b.n-a.n);
  const max=Math.max(1, ...data.map(d=>d[vhistMetric]));
  const unit = vhistMetric==='proof_pct' ? '%' : '';
  document.getElementById('vhistScope').textContent = gridScope
    ? '— '+((ATLAS.countries.find(c=>c.cc===gridScope)||{{}}).name||'') : '— the world';
  host.innerHTML = data.map(d=>{{
    const w=Math.max(2, 100*d[vhistMetric]/max); const V=vv(d);
    return `<div class="vrow" title="${{esc(d.v)}} — ${{d.n}} deployments · ${{d.proof_pct}}% carry a number · ${{VLAB4[V]||V}}">
      <div class="vname">${{esc(d.v)}}</div>
      <div class="vtrack"><div class="vbar v-${{V}}" style="width:${{w}}%;background:color-mix(in srgb, var(--v-${{V==='proven'?'strong':V}}) 55%, var(--surface))"></div></div>
      <div class="vval">${{d[vhistMetric]}}<span class="u">${{unit}}</span><span class="g g-${{V}}">${{VERDICT_GLYPH[V]}}</span></div>
    </div>`;
  }}).join('');
}}
document.getElementById('vhistMetric').addEventListener('click', e=>{{
  const b=e.target.closest('button'); if(!b) return;
  document.querySelectorAll('#vhistMetric button').forEach(x=>x.classList.toggle('on',x===b));
  vhistMetric=b.dataset.vm; renderVHist();
}});

/* A2 table twin (a11y) */
let gtSort={{k:'n',dir:-1}};
function buildGridTwin() {{
  const tb=document.querySelector('#gridTableTwin tbody'); if(!tb) return;
  const rows=gridData().map(c=>({{...c, pct: c.n? Math.round(100*(c.withnum||0)/c.n):0}}));
  rows.sort((a,b)=>{{ const A=a[gtSort.k],B=b[gtSort.k];
    return ((typeof A==='string')?A.localeCompare(B):(A>B?1:A<B?-1:0))*gtSort.dir; }});
  tb.innerHTML=rows.map(c=>`<tr onclick='openCell(${{JSON.stringify(c.v)}},${{JSON.stringify(c.h)}})'>
    <td>${{c.v}}</td><td>${{c.h}}</td><td>${{c.n}}</td><td>${{c.withnum||0}}</td>
    <td>${{c.pct}}</td><td><span class="g-${{vv(c)}}">${{VERDICT_GLYPH[vv(c)]}}</span> ${{VLAB4[vv(c)]||vv(c)}}</td></tr>`).join('');
  markSort('#gridTableTwin', gtSort.k, gtSort.dir);
}}
document.querySelectorAll('#gridTableTwin th').forEach(th=>th.addEventListener('click',()=>{{
  const k=th.dataset.k; gtSort.dir=(gtSort.k===k)?-gtSort.dir:-1; gtSort.k=k; buildGridTwin();
}}));
document.getElementById('modeCtrl').addEventListener('click', e=>{{
  const b=e.target.closest('button'); if(!b)return;
  document.querySelectorAll('#modeCtrl button').forEach(x=>x.classList.toggle('on',x===b));
  gridMode=b.dataset.mode; renderGrid();
}});

/* ============ A3 STREET — company drill panel ============ */
const scrim=document.getElementById('scrim'), panel=document.getElementById('panel');
const EX_GLYPH={{confirmed:'●', claimed:'○', none:'·'}};
const EX_CLASS={{confirmed:'g-strong', claimed:'g-talk', none:''}};
const EX_LABEL={{confirmed:'confirmed', claimed:'claimed', none:'not found'}};
const EX_RANK={{confirmed:0, claimed:1, none:2}};
const TIER_RANK={{P:0, I:1, S:2, '':3}};
let panelRows=[], panelSort='evidence';

function cellCompanies(v,h) {{
  // world scope: merge every country's key for this v|h; else just the scoped country
  const ccs = gridScope ? [gridScope] : ATLAS.countries.map(c=>c.cc);
  let out=[];
  ccs.forEach(cc=>{{ const k=cc+'|'+v+'|'+h; if(ATLAS.cells[k]) out=out.concat(ATLAS.cells[k].map(e=>({{...e,cc}}))); }});
  return out;
}}
function sortPanel(rows) {{
  const r=[...rows];
  if(panelSort==='evidence') r.sort((a,b)=> (EX_RANK[a.existence]-EX_RANK[b.existence]) || (TIER_RANK[tierOf(a)]-TIER_RANK[tierOf(b)]) || a.company.localeCompare(b.company));
  else if(panelSort==='name') r.sort((a,b)=>a.company.localeCompare(b.company));
  else if(panelSort==='tier') r.sort((a,b)=> (TIER_RANK[tierOf(a)]-TIER_RANK[tierOf(b)]) || a.company.localeCompare(b.company));
  return r;
}}
function tierOf(e) {{ const t=(e.tier||'').trim().toUpperCase(); return ['P','I','S'].includes(t)?t:''; }}
function valueOf(e) {{ // value col holds the quantified claim; hide the null-ish placeholders
  const v=(e.value||'').trim(); if(!v||/^(none|n\\/a|—|-|see row)/i.test(v)) return ''; return v;
}}
function srcLinks(url) {{
  return (url||'').split(/\\s*\\/\\s+(?=https?:)/i).filter(u=>/^https?:/i.test(u.trim()))
    .map((u,i)=>`<a class="src" href="${{u.trim()}}" target="_blank" rel="noopener">source${{i?(' '+(i+1)):''}} ↗</a>`).join(' ') || '<span style="color:var(--muted)">no link</span>';
}}
function renderPanelBody() {{
  const rows=sortPanel(panelRows);
  let html='<div class="sortbar">sort <button data-s="evidence" class="'+(panelSort==='evidence'?'on':'')+'">by evidence</button>'
    +'<button data-s="tier" class="'+(panelSort==='tier'?'on':'')+'">by tier</button>'
    +'<button data-s="name" class="'+(panelSort==='name'?'on':'')+'">A–Z</button></div>';
  indexCompanies();
  html += rows.map(e=>{{
    const ex=e.existence||'none', tier=tierOf(e), val=valueOf(e), scope=gridScope?'':(' · '+e.cc);
    const slug=SLUG_BY_NAME[e.company+'|'+e.cc];
    const nameHtml=slug?`<a class="name colink" href="#/company/${{slug}}">${{esc(e.company)}}</a>${{scope}}`:`<span class="name">${{esc(e.company)}}${{scope}}</span>`;
    return `<div class="co"><div class="top">${{nameHtml}}`
      + `<span class="exist"><span class="glyph ${{EX_CLASS[ex]}}">${{EX_GLYPH[ex]}}</span><span style="color:var(--muted);font-size:11.5px">${{EX_LABEL[ex]}}</span></span></div>`
      + `<div class="use">${{esc(e.use||'')}}</div>`
      + `<div class="meta">`
      + (tier?`<span class="chip ${{tier}}">tier ${{tier}}</span>`:'')
      + (val?`<span class="val">${{esc(val)}}</span>`:'<span class="val" style="opacity:.6">no value number</span>')
      + (e.date&&e.date!=='missing'?`<span>${{esc(e.date)}}</span>`:'')
      + (e.fresh&&e.fresh!=='fresh'&&e.fresh!=='undated'?`<span class="freshbadge fb-${{e.fresh}}" title="verified ${{esc(e.date||'?')}} — ${{e.fresh}}, re-check before citing">{icon('triangle-alert',12)}</span>`:'')
      + `<span style="flex:1"></span>${{srcLinks(e.url)}}</div></div>`;
  }}).join('');
  document.getElementById('pbody').innerHTML=html;
  document.querySelectorAll('.sortbar button').forEach(b=>b.addEventListener('click',()=>{{ panelSort=b.dataset.s; renderPanelBody(); }}));
}}
function esc(s) {{ return String(s).replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c])); }}

function openCell(v,h) {{
  panelRows=cellCompanies(v,h); panelSort='evidence';
  const g=gridData().find(c=>c.v===v&&c.h===h);
  const scopeLabel=gridScope?(ATLAS.countries.find(c=>c.cc===gridScope)||{{}}).name:'the world';
  const verdict=g?vv(g):'';
  document.getElementById('pcrumb').innerHTML=`${{esc(scopeLabel)}} <span style="opacity:.5">›</span> ${{esc(h)}}`
    + (verdict?` <span class="verdict-tag v-${{verdict}} g-${{verdict}}">${{VERDICT_GLYPH[verdict]}} ${{VLAB4[verdict]||verdict}}</span>`:'');
  document.getElementById('ptitle').innerHTML=`${{esc(v)}} <span class="x">×</span> ${{esc(h)}}`;
  const conf=panelRows.filter(e=>e.existence==='confirmed').length;
  const withNum=panelRows.filter(e=>valueOf(e)).length;
  document.getElementById('psub').textContent=`${{panelRows.length}} deployment${{panelRows.length!==1?'s':''}} · ${{conf}} confirmed · ${{withNum}} with a value number`;
  renderPanelBody();
  document.getElementById('pbody').scrollTop=0;
  scrim.classList.add('open'); panel.classList.add('open'); panel.setAttribute('aria-hidden','false');
}}
function closePanel() {{ scrim.classList.remove('open'); panel.classList.remove('open'); panel.setAttribute('aria-hidden','true'); }}
scrim.addEventListener('click',closePanel);
document.getElementById('pclose').addEventListener('click',closePanel);
document.addEventListener('keydown',e=>{{ if(e.key==='Escape'&&panel.classList.contains('open'))closePanel(); }});

/* render the question menu on the home screen (N1) */
renderQMenu();
indexCompanies();
/* honor a deep-link hash on first load (e.g. someone opens #/silent directly) */
if (location.hash && location.hash!=='#') applyRoute();
</script>
</body>
</html>"""

open(OUT, "w").write(HTML)
# also emit index.html at repo root so GitHub Pages serves the atlas at the site root
open(os.path.join(ROOT, "index.html"), "w").write(HTML)
# persist the lucide SVG cache so future builds don't need the lucide package
if _lucide is not None:
    json.dump(_lucide_cache, open(_LUCIDE_CACHE_PATH, "w"), ensure_ascii=False, indent=0)
print(f"built {OUT} ({len(HTML):,} bytes) — A0 Orbit · A1 World · A2 Grid · A3 Street")
print("also wrote index.html (GitHub Pages entry point)")
print("open it in a browser to review the full atlas.")
