#!/usr/bin/env python3
"""
KARTO — render the social-share card (Open Graph / Twitter thumbnail).
1200x630 PNG in the atlas warm palette. Self-contained; regenerable.
    python3 scripts/build_og_card.py   ->  og-card.png (repo root)
Uses PIL + system fonts (Avenir Next Condensed echoes the headline face,
Georgia echoes the body serif). Real raster file so social scrapers can fetch it.
"""
import os, math, json
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "og-card.png")
ATLAS = json.load(open(os.path.join(ROOT, "data", "atlas.json")))

W, H = 1200, 630
SS = 2                      # supersample for crisp text, downscale at the end
W2, H2 = W*SS, H*SS

# ---- atlas palette (light) ----
PAGE   = (244,240,230)      # #f4f0e6
SURF   = (250,247,240)      # #faf7f0
INK    = (33,29,23)         # #211d17
INK2   = (92,85,74)         # #5c554a
MUTED  = (143,134,118)      # #8f8676
LAND   = (227,218,194)      # #e3dac2
LANDE  = (205,191,159)      # #cdbf9f
ACCENT = (189,122,38)       # #bd7a26
HAIR   = (33,29,23,32)

def font(path, size):
    return ImageFont.truetype(path, size*SS)

AV  = "/System/Library/Fonts/Avenir Next Condensed.ttc"
AVN = "/System/Library/Fonts/Avenir Next.ttc"
GEO = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEOB= "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"

f_eyebrow = ImageFont.truetype(AVN, 20*SS)
f_head    = ImageFont.truetype(AV, 54*SS)      # condensed grotesque headline
f_hero    = ImageFont.truetype(AVN, 150*SS)
f_herolab = ImageFont.truetype(AVN, 22*SS)
f_kpi     = ImageFont.truetype(AVN, 30*SS)
f_kpilab  = ImageFont.truetype(GEO, 19*SS)
f_brand   = ImageFont.truetype(AVN, 24*SS)

img = Image.new("RGB", (W2, H2), PAGE)
d = ImageDraw.Draw(img, "RGBA")

def tracked(draw, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking*SS
    return x

PAD = 70*SS

# ---- left column: the argument ----
# eyebrow
tracked(d, (PAD, 64*SS), "THE CURRENT STATE OF AI ON EARTH", f_eyebrow, MUTED, tracking=3)
d.line([(PAD, 100*SS), (PAD+430*SS, 100*SS)], fill=ACCENT, width=2*SS)

# headline (two lines, weight via accent on the swing words)
hy = 150*SS
d.text((PAD, hy), "AI is deployed", font=f_head, fill=INK)
w1 = d.textlength("AI is deployed ", font=f_head)
d.text((PAD+w1, hy), "almost everywhere.", font=f_head, fill=ACCENT)
hy2 = hy + 78*SS
d.text((PAD, hy2), "Proof it pays is", font=f_head, fill=INK)
w2 = d.textlength("Proof it pays is ", font=f_head)
d.text((PAD+w2, hy2), "almost nowhere.", font=f_head, fill=ACCENT)

# hero number + label
hyN = 330*SS
d.text((PAD, hyN), f"{ATLAS['global']['deployments']:,}", font=f_hero, fill=INK)
numw = d.textlength(f"{ATLAS['global']['deployments']:,}", font=f_hero)
d.text((PAD+numw+22*SS, hyN+64*SS), "AI deployments,", font=f_herolab, fill=INK2)
d.text((PAD+numw+22*SS, hyN+92*SS), "each named & source-linked", font=f_herolab, fill=MUTED)

# KPI strip
g = ATLAS["global"]
kpis = [(f"{g['companies']:,}", "companies"), (str(g['countries']), "countries"),
        (str(len(ATLAS['verticals'])), "industries"),
        (f"{round(100*g['confirmed']/g['deployments'])}%", "confirmed")]
kx = PAD
ky = 505*SS
for num, lab in kpis:
    d.text((kx, ky), num, font=f_kpi, fill=INK)
    d.text((kx, ky+40*SS), lab, font=f_kpilab, fill=MUTED)
    kx += max(d.textlength(num, font=f_kpi), d.textlength(lab, font=f_kpilab)) + 54*SS

# brand mark bottom-left
tracked(d, (PAD, H2-58*SS), "KARTO", f_brand, INK, tracking=4)
bw = d.textlength("KARTO", font=f_brand) + 5*4*SS
tracked(d, (PAD+bw+16*SS, H2-58*SS), "AI ATLAS", f_brand, MUTED, tracking=4)

# ---- right column: the globe motif (orthographic, warm) ----
CX, CY, R = int(W2*0.855), int(H2*0.52), int(128*SS)
# halo
d.ellipse([CX-R-18*SS, CY-R-18*SS, CX+R+18*SS, CY+R+18*SS], fill=(189,122,38,16))
# sphere
d.ellipse([CX-R, CY-R, CX+R, CY+R], fill=SURF, outline=LANDE, width=2*SS)

# graticule: meridians + parallels via simple orthographic projection
rot = math.radians(-25)  # tilt
def project(lon, lat):
    lon = math.radians(lon); lat = math.radians(lat)
    x = math.cos(lat)*math.sin(lon)
    y = math.cos(rot)*math.sin(lat) - math.sin(rot)*math.cos(lat)*math.cos(lon)
    z = math.sin(rot)*math.sin(lat) + math.cos(rot)*math.cos(lat)*math.cos(lon)
    return x, y, z
def to_px(x, y):
    return CX + x*R, CY - y*R

GRAT = (231,225,211)
# parallels
for lat in range(-60, 61, 30):
    pts = []
    for lon in range(-180, 181, 4):
        x,y,z = project(lon, lat)
        if z >= 0: pts.append(to_px(x,y))
    if len(pts) > 1: d.line(pts, fill=GRAT, width=1*SS, joint="curve")
# meridians
for lon in range(-180, 181, 30):
    pts = []
    for lat in range(-90, 91, 4):
        x,y,z = project(lon, lat)
        if z >= 0: pts.append(to_px(x,y))
    if len(pts) > 1: d.line(pts, fill=GRAT, width=1*SS, joint="curve")

# country markers (front hemisphere only), sized by deployments
maxdep = max(c["deployments"] for c in ATLAS["countries"])
for c in ATLAS["countries"]:
    lon, lat = c["ll"]
    x,y,z = project(lon, lat)
    if z < 0: continue
    px, py = to_px(x,y)
    r = (6 + 16*math.sqrt(c["deployments"]/maxdep))*SS
    d.ellipse([px-r, py-r, px+r, py+r], fill=(189,122,38,235), outline=SURF, width=1*SS)

# downscale (antialias) and save
img = img.resize((W, H), Image.Resampling.LANCZOS)
img.save(OUT, "PNG")
print(f"built {OUT} ({os.path.getsize(OUT):,} bytes, {W}x{H})")
