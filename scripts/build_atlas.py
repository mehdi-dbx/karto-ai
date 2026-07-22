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
WORLD_JSON = open(os.path.join(ROOT, "data", "world-110m.json")).read()
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
<meta name="description" content="A source-gated census of {fmt(g['deployments'])} AI deployments at {fmt(g['companies'])} of the world's largest listed companies across {g['countries']} countries. AI is deployed almost everywhere; proof that it pays is almost nowhere.">
<!-- Open Graph / Twitter share card -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="KARTO AI Atlas">
<meta property="og:title" content="KARTO Atlas — where AI is actually profitable">
<meta property="og:description" content="{fmt(g['deployments'])} named, source-linked AI deployments across {g['countries']} countries. Deployed almost everywhere; proof it pays is almost nowhere.">
<meta property="og:url" content="https://mehdi-dbx.github.io/karto-ai/">
<meta property="og:image" content="https://mehdi-dbx.github.io/karto-ai/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="KARTO Atlas — where AI is actually profitable">
<meta name="twitter:description" content="{fmt(g['deployments'])} named, source-linked AI deployments across {g['countries']} countries. Deployed almost everywhere; proof it pays is almost nowhere.">
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
  --v-talk:      #d03b3b;
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
  --v-talk:      #e66767;
  --v-empty:     #3a352d;
  --d1:#24211c; --d2:#9c5312; --d3:#b06a1c; --d4:#cc8a38; --d5:#e0b06a; --d6:#f0d4a0; --d7:#f0d4a0;
}}

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
#mapsvg {{ width:100%; height:auto; display:block; }}
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
.tabletwin th {{ color:var(--muted); font-weight:560; font-size:12px; letter-spacing:.03em; cursor:pointer; }}
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
.v-active {{ background:color-mix(in srgb, var(--v-active) 26%, var(--surface)); color:var(--ink); }}
.v-talk   {{ background:color-mix(in srgb, var(--v-talk) 20%, var(--surface)); color:var(--ink); }}
.g-strong {{ color:var(--v-strong); }} .g-active {{ color:var(--v-active); }} .g-talk {{ color:var(--v-talk); }}
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
.co .glyph {{ font-size:13px; }}
.co .use {{ color:var(--ink-2); font-size:13.5px; line-height:1.5; margin:6px 0 9px; font-family:var(--font-body); }}
.co .meta {{ display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; font-family:var(--font-ui); font-size:11.5px; color:var(--muted); }}
.co .chip {{ padding:2px 8px; border-radius:5px; background:var(--surface-2); border:1px solid var(--hair); font-weight:560; letter-spacing:.02em; }}
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
  <div class="brand">KARTO&nbsp; <b>AI Atlas</b></div>
  <nav class="crumbs" id="crumbs"><span class="here">Orbit</span></nav>
  <button class="toggle" id="themeToggle" aria-label="Toggle light/dark">
    <span id="themeIcon">◐</span><span id="themeLabel">Dark</span>
  </button>
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
        <h1>AI is deployed <b>almost everywhere</b>.<br>Proof that it pays is <b>almost nowhere</b>.</h1>
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
      <div class="cap">Adoption is real and near-universal — <b>{fmt(g['confirmed'])} of {fmt(g['deployments'])}</b> deployments
      ({round(100*g['confirmed']/g['deployments'])}%) are confirmed. But value is not proven: only
      <b>{fmt(g['with_value_number'])}</b> ({round(100*g['with_value_number']/g['deployments'])}%) attach any value number at all —
      and virtually none is independently audited. <b>The gap is proof, not deployment.</b></div>
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

    <button class="descend" id="descend">Descend to the world <span class="arrow">↓</span></button>

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
        color = <b>adoption density</b> (confirmed deployments per company searched). Big isn't dense.</p>
      </div>
      <div class="controls">
        <div class="seg-ctrl" id="viewCtrl">
          <button data-view="map" class="on">Map</button>
          <button data-view="bars">Ranked</button>
        </div>
        <div class="seg-ctrl" id="metricCtrl">
          <button data-m="density" class="on">Density</button>
          <button data-m="deployments">Volume</button>
          <button data-m="proof_pct">Proof&nbsp;%</button>
        </div>
      </div>
    </div>
    <div class="mapwrap" id="mapView">
      <svg id="mapsvg" viewBox="0 0 960 480" role="img" aria-label="World map of AI deployment by country"></svg>
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
          <th data-k="density">Density&nbsp;×</th><th data-k="proof_pct">Proof&nbsp;%</th>
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
        is <b>proven with numbers</b> vs merely <b>active</b> vs just <b>talk</b>. Click any cell for the companies.</p>
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
      <span class="k"><span class="sw v-strong g-strong">●</span> Proven — ≥40% cite a value number</span>
      <span class="k"><span class="sw v-active g-active">◐</span> Active — confirmed, few numbers (≥15%)</span>
      <span class="k"><span class="sw v-talk g-talk">○</span> Talk — unconfirmed or almost no numbers</span>
      <span class="k"><span class="sw" style="background:var(--surface-2)">·</span> Empty — none found</span>
    </div>
    <div class="vhist-block">
      <div class="vhist-head">
        <h3>AI adoption by industry <span class="vhist-scope" id="vhistScope"></span></h3>
        <div class="seg-ctrl" id="vhistMetric">
          <button data-vm="n" class="on">Deployments</button>
          <button data-vm="proof_pct">Proof&nbsp;%</button>
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
<script id="world-data" type="application/json">{WORLD_JSON}</script>
<script>{D3}</script>
<script>{TOPO}</script>
<script>
const ATLAS = JSON.parse(document.getElementById('atlas-data').textContent);

/* theme toggle — persists, respects prior choice */
const root = document.documentElement;
const tBtn = document.getElementById('themeToggle');
const tIcon = document.getElementById('themeIcon'), tLab = document.getElementById('themeLabel');
function applyTheme(t) {{
  root.setAttribute('data-theme', t);
  tIcon.textContent = t === 'dark' ? '☀' : '◐';
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

/* ============ A1 WORLD (D3) ============ */
const world = JSON.parse(document.getElementById('world-data').textContent);
const tip = document.getElementById('tip');
const cssv = n => getComputedStyle(root).getPropertyValue(n).trim();
let worldRendered = false, curMetric = 'density';

const METRIC_LABEL = {{density:'Density (confirmed / searched)', deployments:'Deployments found', proof_pct:'Carry a hard number'}};

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

function renderWorld() {{
  if (worldRendered) {{ paintBubbles(); return; }}
  worldRendered = true;
  const svg = d3.select('#mapsvg');
  const W=960, H=480;
  const proj = d3.geoNaturalEarth1().fitExtent([[8,8],[W-8,H-8]], topojson.feature(world, world.objects.land));
  const path = d3.geoPath(proj);
  // graticule
  svg.append('path').attr('class','graticule').attr('d', path(d3.geoGraticule10()));
  // land
  svg.append('path').attr('class','land').attr('d', path(topojson.feature(world, world.objects.land)));
  // bubble layer
  svg.append('g').attr('class','bubs');
  svg.append('g').attr('class','labs');
  paintBubbles();

  refreshSizeLegend();
  buildWorldTable();
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

  const bl = svg.select('.bubs');
  const j = bl.selectAll('circle').data(cs, d=>d.cc);
  j.join(
    enter => enter.append('circle').attr('class','bub')
      .attr('cx',d=>d.xy[0]).attr('cy',d=>d.xy[1]).attr('r',d=>rS(d.deployments))
      .on('mousemove', showTip).on('mouseleave', hideTip)
      .on('click', (e,d)=>descendCountry(d)),
    update => update
  ).transition().duration(400)
      .attr('r', d=>rS(d.deployments))
      .attr('fill', d=>densityColor(d[curMetric], maxMetric));

  // labels only for the biggest few (avoid clutter — selective, per anti-patterns)
  const top = [...cs].sort((a,b)=>b.deployments-a.deployments).slice(0,6);
  const ll = svg.select('.labs');
  const lj = ll.selectAll('text').data(top, d=>d.cc);
  lj.join(
    enter=>enter.append('text').attr('class','bub-label').attr('text-anchor','middle')
      .attr('x',d=>d.xy[0]).attr('y',d=>d.xy[1]-rS(d.deployments)-4).text(d=>d.cc),
    u=>u, ex=>ex.remove()
  );
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
}}
document.querySelectorAll('#worldTable th').forEach(th=>th.addEventListener('click',()=>{{
  const k=th.dataset.k; tSort.dir = (tSort.k===k)? -tSort.dir : -1; tSort.k=k; buildWorldTable();
}}));

/* ============ A2 TERRITORY (decision grid) ============ */
let gridScope = null;   // null = world, else cc
let gridMode = 'verdict';
const VERDICT_GLYPH = {{strong:'●', active:'◐', talk:'○', empty:'·'}};
const VERDICT_CLASS = {{strong:'v-strong', active:'v-active', talk:'v-talk', empty:'empty'}};

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
        html += `<td class="cell ${{VERDICT_CLASS[c.verdict]}}" ${{attrs}}>`
              + `<span class="glyph g-${{c.verdict}}">${{VERDICT_GLYPH[c.verdict]}}</span>`
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
        + (gridMode==='verdict'?`<div class="r"><span>verdict</span><b class="g-${{c.verdict}}">${{c.verdict}}</b></div>`:'')
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
    const w=Math.max(2, 100*d[vhistMetric]/max);
    return `<div class="vrow" title="${{esc(d.v)}} — ${{d.n}} deployments · ${{d.proof_pct}}% carry a number">
      <div class="vname">${{esc(d.v)}}</div>
      <div class="vtrack"><div class="vbar v-${{d.verdict}}" style="width:${{w}}%;background:color-mix(in srgb, var(--v-${{d.verdict}}) 55%, var(--surface))"></div></div>
      <div class="vval">${{d[vhistMetric]}}<span class="u">${{unit}}</span><span class="g g-${{d.verdict}}">${{VERDICT_GLYPH[d.verdict]}}</span></div>
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
const VLAB={{strong:'Proven',active:'Active',talk:'Talk'}};
function buildGridTwin() {{
  const tb=document.querySelector('#gridTableTwin tbody'); if(!tb) return;
  const rows=gridData().map(c=>({{...c, pct: c.n? Math.round(100*(c.withnum||0)/c.n):0}}));
  rows.sort((a,b)=>{{ const A=a[gtSort.k],B=b[gtSort.k];
    return ((typeof A==='string')?A.localeCompare(B):(A>B?1:A<B?-1:0))*gtSort.dir; }});
  tb.innerHTML=rows.map(c=>`<tr onclick='openCell(${{JSON.stringify(c.v)}},${{JSON.stringify(c.h)}})'>
    <td>${{c.v}}</td><td>${{c.h}}</td><td>${{c.n}}</td><td>${{c.withnum||0}}</td>
    <td>${{c.pct}}</td><td><span class="g-${{c.verdict}}">${{VERDICT_GLYPH[c.verdict]}}</span> ${{VLAB[c.verdict]||c.verdict}}</td></tr>`).join('');
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
  html += rows.map(e=>{{
    const ex=e.existence||'none', tier=tierOf(e), val=valueOf(e), scope=gridScope?'':(' · '+e.cc);
    return `<div class="co"><div class="top"><span class="name">${{esc(e.company)}}${{scope}}</span>`
      + `<span class="exist"><span class="glyph ${{EX_CLASS[ex]}}">${{EX_GLYPH[ex]}}</span><span style="color:var(--muted);font-size:11.5px">${{EX_LABEL[ex]}}</span></span></div>`
      + `<div class="use">${{esc(e.use||'')}}</div>`
      + `<div class="meta">`
      + (tier?`<span class="chip ${{tier}}">tier ${{tier}}</span>`:'')
      + (val?`<span class="val">${{esc(val)}}</span>`:'<span class="val" style="opacity:.6">no value number</span>')
      + (e.date&&e.date!=='missing'?`<span>${{esc(e.date)}}</span>`:'')
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
  const verdict=g?g.verdict:'';
  const VLAB={{strong:'Proven',active:'Active',talk:'Talk'}};
  document.getElementById('pcrumb').innerHTML=`${{esc(scopeLabel)}} <span style="opacity:.5">›</span> ${{esc(h)}}`
    + (verdict?` <span class="verdict-tag v-${{verdict}} g-${{verdict}}">${{VERDICT_GLYPH[verdict]}} ${{VLAB[verdict]||verdict}}</span>`:'');
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
</script>
</body>
</html>"""

open(OUT, "w").write(HTML)
# also emit index.html at repo root so GitHub Pages serves the atlas at the site root
open(os.path.join(ROOT, "index.html"), "w").write(HTML)
print(f"built {OUT} ({len(HTML):,} bytes) — A0 Orbit · A1 World · A2 Grid · A3 Street")
print("also wrote index.html (GitHub Pages entry point)")
print("open it in a browser to review the full atlas.")
