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
  --v-unquantified: #5a7d99;      /* slate-blue: real activity, no numbers (distinct from red hype) */
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
  --v-unquantified: #7fa6c4;      /* slate-blue, lifted for dark surface */
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
.topnav {{ display: flex; align-items: center; gap: 16px; }}
.navlink {{ font-family: var(--font-ui); font-size: 12.5px; color: var(--ink-2); text-decoration: none; letter-spacing: .02em; white-space: nowrap; }}
.navlink:hover {{ color: var(--accent); text-decoration: none; }}
.navlink.on {{ color: var(--ink); font-weight: 560; }}
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
/* D3 persona tiles */
.personas {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-top:44px; max-width:920px; }}
.ptile {{ display:block; padding:20px; border:1px solid var(--hair); border-radius:12px; background:var(--surface); text-decoration:none; transition:border-color .2s ease, transform .2s ease; }}
.ptile:hover {{ border-color:var(--accent); transform:translateY(-2px); text-decoration:none; }}
.ptile .pt-ico {{ font-size:22px; }} .ptile .pt-t {{ font-family:var(--font-head); font-weight:560; font-size:17px; color:var(--ink); margin-top:8px; }}
.ptile .pt-d {{ font-size:12.5px; color:var(--muted); margin-top:5px; line-height:1.5; }}
/* B7 insights feed */
.insfeed {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; margin-top:24px; }}
.inscard {{ border:1px solid var(--hair); border-radius:12px; padding:18px; background:var(--surface); }}
.ins-h {{ display:flex; align-items:center; gap:8px; font-family:var(--font-ui); font-size:11.5px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
.ins-ico {{ font-size:15px; }}
.ins-score {{ font-variant-numeric:tabular-nums; color:var(--accent); font-weight:600; }}
.ins-find {{ font-family:var(--font-body); font-size:15px; color:var(--ink); margin:10px 0; line-height:1.5; }}
.ins-act {{ font-size:13px; color:var(--ink-2); line-height:1.5; }}
.ins-act b {{ color:var(--accent); }}
.ins-ent {{ margin-top:10px; font-family:var(--font-ui); font-size:12.5px; }}
.expbtn {{ margin-top:24px; font-family:var(--font-ui); font-size:13px; color:var(--ink); background:var(--surface-2);
  border:1px solid var(--hair); border-radius:8px; padding:10px 18px; cursor:pointer; transition:border-color .2s ease, color .2s ease; }}
.expbtn:hover {{ border-color:var(--accent); color:var(--accent); }}
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
.fb-stale {{ color:var(--v-talk); background:color-mix(in srgb,var(--v-talk) 13%,var(--surface)); }}
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
    <a href="#/trends" class="navlink" data-route="trends">Trends</a>
    <a href="#/hype" class="navlink" data-route="hype">Hype</a>
    <a href="#/insights" class="navlink" data-route="insights">Insights</a>
    <a href="#/compare" class="navlink" data-route="compare">Compare</a>
    <a href="#/silent" class="navlink" data-route="silent">Silent&nbsp;list</a>
    <button class="toggle" id="themeToggle" aria-label="Toggle light/dark">
      <span id="themeIcon">◐</span><span id="themeLabel">Dark</span>
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

    <div class="personas">
      <a class="ptile" href="#/silent"><div class="pt-ico">🎯</div><div class="pt-t">Consultant</div><div class="pt-d">White-space &amp; the silent-company prospect list — documented gaps next to peers' activity.</div></a>
      <a class="ptile" href="#/trends"><div class="pt-ico">📈</div><div class="pt-t">Investor</div><div class="pt-d">Momentum over time — who moved early, who's catching up, who went quiet.</div></a>
      <a class="ptile" href="#/compare"><div class="pt-ico">⚖️</div><div class="pt-t">Strategist</div><div class="pt-d">Line up rivals side by side — maturity, proof rate, peer percentiles.</div></a>
      <a class="ptile" href="#/hype"><div class="pt-ico">🔍</div><div class="pt-t">Vendor</div><div class="pt-d">Talk vs proof by industry — find the confirmed-but-unmeasured buyers.</div></a>
    </div>

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
        (confirmed deployments per company searched — <span style="cursor:help" title="Companies can disclose several deployments, so density above 1× is expected, not a bug.">values above 1× are normal ⓘ</span>). Big isn't dense.</p>
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
      <span class="k"><span class="sw v-proven g-proven">●</span> Proven — ≥40% cite a value number</span>
      <span class="k"><span class="sw v-active g-active">◐</span> Active — confirmed, some numbers (≥15%)</span>
      <span class="k"><span class="sw v-unquantified g-unquantified">◍</span> Unquantified — mostly confirmed, no numbers yet</span>
      <span class="k"><span class="sw v-talk g-talk">○</span> Talk — unconfirmed / hype</span>
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

<!-- ============ INSIGHTS FEED (B7) ============ -->
<section class="altitude" id="insights" data-alt="Insights">
  <div class="terr">
    <div class="head">
      <div>
        <h2>Insights — <span class="scope">the data speaking first</span></h2>
        <p class="lede">Machine-generated cards, each with a finding <b>and an action</b>.
        Rule-based and deterministic — no black box. Filter by who it's for.</p>
      </div>
      <div class="controls">
        <div class="seg-ctrl" id="insPersona">
          <button data-p="" class="on">All</button>
          <button data-p="consultant">Consultant</button>
          <button data-p="investor">Investor</button>
          <button data-p="vendor">Vendor</button>
        </div>
      </div>
    </div>
    <div id="insFeed" class="insfeed"></div>
  </div>
</section>

<!-- ============ COMPARE (C1/D2) ============ -->
<section class="altitude" id="compare" data-alt="Compare">
  <div class="terr">
    <div class="head">
      <div>
        <h2>Compare — <span class="scope">side by side</span></h2>
        <p class="lede">Pick 2–5 companies to line up their AI footprint: deployments, maturity,
        proof rate, momentum, peer percentiles. Best-in-row is highlighted. The URL is shareable.</p>
      </div>
    </div>
    <div class="cmp-pick">
      <input id="cmpSearch" class="filtersel" style="min-width:260px" placeholder="type a company name…" autocomplete="off">
      <div id="cmpChips" class="cmp-chips"></div>
    </div>
    <div id="cmpSuggest" class="cmp-suggest"></div>
    <div class="tabletwin" style="margin-top:8px"><table id="cmpTable"></table></div>
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
        <h2>Talk vs proof — <span class="scope">the hype gap by industry</span></h2>
        <p class="lede">The study's founding thesis, automated. For each industry: how much is
        <b>announced</b> (deployments) vs <b>substantiated</b> (rows citing a value number).
        A short bar under a long one = an industry deploying AI blind.</p>
      </div>
    </div>
    <div class="vhist" id="hypeChart" style="margin-top:24px"></div>
    <p class="footnote">Substantiation = share of that industry's deployments that cite any value number
    (self-reported, rarely audited). Investment figures regex-extracted from disclosure text.</p>
  </div>
</section>

<!-- ============ SILENT COMPANIES (D4 — the prospect list) ============ -->
<section class="altitude" id="silent" data-alt="Silent">
  <div class="terr">
    <div class="head">
      <div>
        <h2>The silent — searched, <span class="scope">nothing disclosed</span></h2>
        <p class="lede">Companies we searched under the same evidence gate that disclose <b>no AI at all</b>.
        Absence is a finding: each row is a documented gap sitting next to its peers' activity.
        Peer median = typical disclosed deployments among same-industry, same-country rivals.</p>
      </div>
      <div class="controls">
        <select id="silentCC" class="filtersel"><option value="">All countries</option></select>
        <select id="silentSector" class="filtersel"><option value="">All sectors</option></select>
      </div>
    </div>
    <div class="tabletwin" style="margin-top:20px">
      <table id="silentTable">
        <thead><tr>
          <th data-k="name">Company</th><th data-k="cc">Country</th>
          <th data-k="sector">Sector</th><th data-k="index">Index</th>
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

/* ============ hash routing (WAY 1 — one file, shareable #routes) ============ */
const ROUTES = {{
  'a0':     {{hash:'',        label:'Orbit',  show:()=>goAltitude('a0')}},
  'a1':     {{hash:'/world',  label:'World',  show:toWorld}},
  'a2':     {{hash:'/grid',   label:'Grid',   show:()=>{{ if(!ATLAS.grid_global) return; gridScope=null; document.getElementById('scopeName')&&(document.getElementById('scopeName').textContent='the world'); const b=document.getElementById('backWorld'); if(b)b.hidden=true; renderGrid(); goAltitude('a2','World grid'); }}}},
  'trends': {{hash:'/trends', label:'Trends', show:renderTrends}},
  'hype':   {{hash:'/hype',   label:'Hype',   show:renderHype}},
  'compare':{{hash:'/compare',label:'Compare',show:renderCompare}},
  'insights':{{hash:'/insights',label:'Insights',show:renderInsights}},
  'silent': {{hash:'/silent', label:'Silent list', show:renderSilent}},
}};
function goRoute(id) {{ const r=ROUTES[id]; if(!r) return; if(location.hash!=='#'+r.hash) location.hash=r.hash; else applyRoute(); }}
function goCompany(slug) {{ location.hash='/company/'+slug; }}
function applyRoute() {{
  const h=location.hash.replace(/^#/,'');
  if(h.startsWith('/company/')) {{ renderCompany(h.slice('/company/'.length));
    document.querySelectorAll('.navlink').forEach(a=>a.classList.remove('on')); return; }}
  const base=h.split('?')[0];
  const id=(Object.keys(ROUTES).find(k=>ROUTES[k].hash===base)) || 'a0';
  ROUTES[id].show();
  document.querySelectorAll('.navlink').forEach(a=>a.classList.toggle('on', a.dataset.route===id));
}}
window.addEventListener('hashchange', applyRoute);

/* ============ D1 COMPANY PAGE ============ */
const MLAB={{L0:'Silent',L1:'Talk',L2:'Pilot',L3:'Operating',L4:'Industrialized'}};
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
  html+=`<div class="ckpis">
    <div class="ckpi"><div class="n">${{c.deployments}}</div><div class="l">deployments</div></div>
    <div class="ckpi"><div class="n">${{c.confirmed}}</div><div class="l">confirmed</div></div>
    <div class="ckpi"><div class="n">${{Math.round((c.proof_rate||0)*100)}}%</div><div class="l">cite a number</div></div>
    <div class="ckpi"><div class="n">${{c.first_seen||'—'}}</div><div class="l">first seen</div></div>
    <div class="ckpi"><div class="n" style="font-size:16px">${{esc((c.momentum||'').replace(/,/g,', '))||'—'}}</div><div class="l">momentum</div></div>
  </div>`;
  // benchmarks
  if(bench.global_vertical){{
    const b=bench.global_vertical;
    html+=`<h3 class="csub">Percentile vs ${{b.n}} global ${{esc(c.vertical)}} peers</h3><div class="benchbox">
      ${{pctBar('deployments',b.deployments)}}${{pctBar('confirmed',b.confirmed)}}${{pctBar('proof rate',b.proof_rate)}}</div>`;
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
        ${{e.fresh&&e.fresh!=='fresh'&&e.fresh!=='undated'?`<span class="freshbadge fb-${{e.fresh}}">⚠ ${{e.fresh}}</span>`:''}}
        <span style="flex:1"></span>${{srcLinks(e.url)}}</div></div>`;
  }}).join('')+`</div>`;
  // findings flags
  if(findings.length){{
    html+=`<h3 class="csub">Context &amp; flags</h3><div class="cflags">`+findings.map(f=>
      `<div class="cflag">⚑ ${{esc(f.finding)}} ${{f.url?`<a class="src" href="${{esc(f.url)}}" target="_blank" rel="noopener">source ↗</a>`:''}}</div>`).join('')+`</div>`;
  }}
  html+=`<p class="footnote">Every number above traces to a source link or a documented rule (maturity: hover the badge). Data version ${{ATLAS.meta?ATLAS.meta.schema_version:''}}.</p>`;
  html+=`<button class="expbtn" onclick='exportBriefing("company",COMP_BY_SLUG["${{slug}}"])'>⭳ Generate briefing (markdown)</button>`;
  host.innerHTML=html;
  window.scrollTo({{top:0,behavior:'smooth'}});
}}

/* ============ B7 INSIGHTS FEED + D7 export ============ */
let insPersona='';
const ICON={{silent_giant:'🎯',contradiction:'⚠️',whitespace:'🗺️',outlier:'📊',momentum_break:'⏱️'}};
function renderInsights() {{
  goAltitude('insights','Insights');
  const ctrl=document.getElementById('insPersona');
  if(!ctrl.dataset.wired){{ ctrl.dataset.wired='1';
    ctrl.addEventListener('click',e=>{{ const b=e.target.closest('button'); if(!b)return;
      ctrl.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b)); insPersona=b.dataset.p; drawInsights(); }});
  }}
  drawInsights();
}}
function drawInsights() {{
  const feed=document.getElementById('insFeed');
  const cards=(ATLAS.insights||[]).filter(c=>!insPersona || (c.persona||[]).includes(insPersona));
  feed.innerHTML = cards.map(c=>{{
    const co=(c.entities||[]).map(sl=>{{const x=COMP_BY_SLUG&&COMP_BY_SLUG[sl]; return x?`<a class="colink" href="#/company/${{sl}}">${{esc(x.name)}}</a>`:'';}}).filter(Boolean).join(', ');
    return `<div class="inscard">
      <div class="ins-h"><span class="ins-ico">${{ICON[c.type]||'•'}}</span><span class="ins-type">${{c.type.replace(/_/g,' ')}}</span>
        <span style="flex:1"></span><span class="ins-score" title="surprise score">${{c.surprise_score}}</span></div>
      <div class="ins-find">${{esc(c.finding)}}</div>
      <div class="ins-act"><b>Action:</b> ${{esc(c.action)}}</div>
      ${{co?`<div class="ins-ent">${{co}}</div>`:''}}
    </div>`;
  }}).join('') || '<p class="lede">No insights for this persona.</p>';
}}
/* D7 — markdown briefing export (client-side, download) */
function exportBriefing(kind, payload) {{
  const dv=ATLAS.meta?ATLAS.meta.schema_version:'2.0';
  let md=`# KARTO AI Atlas — ${{kind}} briefing\\n\\n_Data version ${{dv}} · ${{ATLAS.global.deployments}} deployments · ${{ATLAS.global.countries}} countries_\\n\\n`;
  if(kind==='company'){{
    const c=payload; md+=`## ${{c.name}}\\n- ${{c.cc}} · ${{c.vertical||'—'}}\\n- Maturity: **${{c.maturity}}** (${{(c.maturity_evidence||[]).join(', ')}})\\n`;
    md+=`- Deployments: ${{c.deployments}} · Confirmed: ${{c.confirmed}} · Proof rate: ${{Math.round((c.proof_rate||0)*100)}}%\\n- Momentum: ${{c.momentum||'—'}} (first seen ${{c.first_seen||'—'}})\\n\\n`;
    const rr=(ROWS_BY_COMPANY[c.name]||[]);
    md+=`### Deployments (${{rr.length}})\\n`+rr.map((e,i)=>`${{i+1}}. ${{(e.use||'').split(';')[0]}} — ${{e.existence}}${{e.date&&e.date!=='missing'?' ('+e.date+')':''}} [${{e.url||'no source'}}]`).join('\\n');
  }} else if(kind==='compare'){{
    const cmp=payload; md+=`## Comparison\\n\\n| Metric | ${{cmp.entities.map(c=>c.name).join(' | ')}} |\\n|---|${{cmp.entities.map(()=>'---').join('|')}}|\\n`;
    cmp.metrics.forEach(m=>{{ md+=`| ${{m.label}} | ${{m.values.join(' | ')}} |\\n`; }});
  }} else if(kind==='insights'){{
    (ATLAS.insights||[]).forEach((c,i)=>{{ md+=`### ${{i+1}}. ${{c.type}}\\n${{c.finding}}\\n\\n**Action:** ${{c.action}}\\n\\n`; }});
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
    {{key:'proof_rate', label:'Proof rate', values:cs.map(c=>Math.round((c.proof_rate||0)*100)+'%'), raw:cs.map(c=>c.proof_rate||0), best:'max'}},
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
  const box=document.getElementById('cmpSuggest'); q=q.trim().toLowerCase();
  if(q.length<2){{ box.innerHTML=''; return; }}
  const hits=ATLAS.companies.filter(c=>!c.silent && c.name.toLowerCase().includes(q)).slice(0,8);
  box.innerHTML=hits.map(c=>`<div class="cmp-opt" onclick="cmpAdd('${{c.slug}}')">${{esc(c.name)}} <span style="color:var(--muted)">· ${{c.cc}} · ${{esc(c.vertical||'')}}</span></div>`).join('');
}}
function cmpAdd(slug) {{
  if(cmpSlugs.length>=5 || cmpSlugs.includes(slug)) return;
  cmpSlugs.push(slug); document.getElementById('cmpSearch').value=''; document.getElementById('cmpSuggest').innerHTML='';
  syncCmpUrl(); drawCompare();
}}
function cmpRemove(slug) {{ cmpSlugs=cmpSlugs.filter(s=>s!==slug); syncCmpUrl(); drawCompare(); }}
function syncCmpUrl() {{ const h='/compare'+(cmpSlugs.length?'?c='+cmpSlugs.join(','):''); if(location.hash!=='#'+h) history.replaceState(null,'','#'+h); }}
function drawCompare() {{
  document.getElementById('cmpChips').innerHTML=cmpSlugs.map(s=>{{
    const c=COMP_BY_SLUG[s]; return `<span class="cmp-chip">${{esc(c.name)}} <b onclick="cmpRemove('${{s}}')">✕</b></span>`;
  }}).join('');
  const tbl=document.getElementById('cmpTable');
  if(cmpSlugs.length<2){{ tbl.innerHTML='<tbody><tr><td style="color:var(--muted);padding:16px 0">Add at least two companies to compare.</td></tr></tbody>'; return; }}
  const cmp=compareCompanies(cmpSlugs);
  let html='<thead><tr><th>Metric</th>'+cmp.entities.map(c=>`<th><a class="colink" href="#/company/${{c.slug}}">${{esc(c.name)}}</a></th>`).join('')+'</tr></thead><tbody>';
  cmp.metrics.forEach(m=>{{
    let bestIdx=-1;
    if(m.best!=='none'){{ const arr=m.raw||m.values.map(Number); const valid=arr.map((v,i)=>[v,i]).filter(x=>typeof x[0]==='number'&&!isNaN(x[0]));
      if(valid.length){{ valid.sort((a,b)=>m.best==='max'?b[0]-a[0]:a[0]-b[0]); bestIdx=valid[0][1]; }} }}
    html+=`<tr><td>${{m.label}}</td>`+m.values.map((v,i)=>`<td class="${{i===bestIdx?'cmp-best':''}}">${{v}}</td>`).join('')+'</tr>';
  }});
  tbl.innerHTML=html+'</tbody>';
  let btn=document.getElementById('cmpExport');
  if(!btn){{ btn=document.createElement('button'); btn.id='cmpExport'; btn.className='expbtn'; btn.textContent='⭳ Generate briefing (markdown)'; tbl.after(btn); }}
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
  goAltitude('hype','Hype');
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
function renderSilent() {{
  goAltitude('silent','Silent list');
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
  drawSilent();
}}
function drawSilent() {{
  const cc=document.getElementById('silentCC').value, sec=document.getElementById('silentSector').value;
  const names={{}}; ATLAS.countries.forEach(c=>names[c.cc]=c.name);
  let rows=ATLAS.silent.filter(s=>(!cc||s.cc===cc)&&(!sec||s.sector===sec));
  rows.sort((a,b)=>{{ let A=a[silentSort.k],B=b[silentSort.k];
    if(A==null)A=-1; if(B==null)B=-1;
    return ((typeof A==='string')?A.localeCompare(B):(A>B?1:A<B?-1:0))*silentSort.dir; }});
  document.querySelector('#silentTable tbody').innerHTML = rows.map(s=>`<tr>
    <td><a class="colink" href="#/company/${{s.slug}}">${{esc(s.name)}}</a></td><td>${{names[s.cc]||s.cc}}</td><td>${{esc(s.sector||'—')}}</td>
    <td>${{esc(s.index||'—')}}</td><td>${{s.peer_median!=null?s.peer_median:'—'}}</td></tr>`).join('');
  document.getElementById('silentCount').textContent =
    `${{rows.length}} silent compan${{rows.length===1?'y':'ies'}} shown · ${{ATLAS.silent.length}} total searched with zero disclosed AI.`;
}}

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
const VLAB4 = {{proven:'Proven', active:'Active', unquantified:'Unquantified', talk:'Talk', strong:'Proven'}};
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
      + (e.fresh&&e.fresh!=='fresh'&&e.fresh!=='undated'?`<span class="freshbadge fb-${{e.fresh}}" title="verified ${{esc(e.date||'?')}} — re-check before citing">⚠ ${{e.fresh}}</span>`:'')
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

/* honor a deep-link hash on first load (e.g. someone opens #/silent directly) */
if (location.hash && location.hash!=='#') applyRoute();
</script>
</body>
</html>"""

open(OUT, "w").write(HTML)
# also emit index.html at repo root so GitHub Pages serves the atlas at the site root
open(os.path.join(ROOT, "index.html"), "w").write(HTML)
print(f"built {OUT} ({len(HTML):,} bytes) — A0 Orbit · A1 World · A2 Grid · A3 Street")
print("also wrote index.html (GitHub Pages entry point)")
print("open it in a browser to review the full atlas.")
