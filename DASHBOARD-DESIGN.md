# KARTO Atlas — design plan (craftsman spec)

> A sober, prize-grade data visualization of 1,628 AI deployments across 14 countries.
> "A map you fall into." Built to the `dataviz` method: **form → color(validated) → marks →
> hover → a11y → render-and-look.** Color is computed & validated, never eyeballed. No slop.

---

## I. Design intent (the north star)

**Sober WARM editorial cartography, not a dashboard-template.** Think aged-paper atlas /
warm FT-graphics — cream surfaces, warm charcoal ink, amber accents. Calm, confident, generous
whitespace, warm-monochrome-first with color used *only* where it carries meaning. Nothing
decorative. Every mark earns its place. The "wow" comes from clarity and craft, not effects.
Warmth = the mood; it must never cost contrast or CVD-safety (validator still gates every color).

**Restraint rules (self-imposed, prize-grade):**
- One typeface (system sans), a strict type scale, tabular-nums only in tables/axes.
- Monochrome canvas; color reserved for the ONE semantic job on each screen.
- Generous margins, hairline rules, no borders-as-separators, no drop-shadows-as-decoration.
- Motion is functional only: 200–300ms ease transitions between altitudes; nothing bounces.
- Dark mode is a first-class, separately-validated theme (not an inverted flip).

---

## II. Palette (from the validated reference; will re-run validate_palette.js before build)

Surfaces & ink — WARM (light / dark), pending validation:
- surface `#faf7f0` (warm cream) / `#1c1a17` (warm dark) · page `#f4f0e6` / `#141210`
- ink primary `#211d17` (warm charcoal) / `#f5f1e8` · secondary `#5c554a` / `#c9c2b3` · muted `#8f8676`
- gridline `#e7e1d3` / `#302c26` · hairline border warm rgba
- (these are TARGET warm values; validator confirms contrast on the cream/warm-dark surfaces before use)

**Color jobs, one per screen (this is the discipline):**
- **A1 World — sequential (magnitude), WARM hue.** Amber/orange ramp light→dark for density
  (e.g. `#f6e6c8 → #7a3d0a`), one hue, NOT categorical. Snapped to nearest validator-passing warm
  steps. (choosing-a-form: "compare magnitude → sequential one hue".)
- **A2 Grid — status (state), the decision verdict.** Reserved status palette, icon+label always:
  - strong = good `#0ca30c` · active = warning `#fab219` · talk = critical `#d03b3b` · empty = muted/neutral
  - Status colors ship with a glyph (● strong / ◐ active / ○ talk / · empty) so never color-alone.
- **A0 & A3 — warm-monochrome**; one accent (amber) for the single emphasis mark.
- **Existence in drill-down** — a small ordinal: confirmed (ink) · claimed (muted) · none (hairline).
- Will `node scripts/validate_palette.js` the sequential ramp (--ordinal) + status set, light AND
  dark, against the real surfaces, and fix any FAIL before writing chart code.

---

## III. The four altitudes (form chosen by data job)

### A0 — ORBIT (thesis). Own screen. Job: land the argument in one breath.
- **Form: hero figure + KPI stat-tile row** (choosing-a-form: "handful of headline numbers → KPI
  row of stat tiles"; "the one number → hero figure ≥48px sans"). NOT a chart.
- Hero: **1,628** deployments. Tiles: 1,385 companies · 14 countries · 761 confirmed · 468 hard-proof.
- **One honest gap mark**: a single horizontal part-to-whole bar — of all deployments, the confirmed
  slice, and within it the hard-proof sliver. Monochrome + one accent. Caption states it plainly
  ("most value is self-reported"). No drama, the proportion IS the argument.
- A quiet "Descend ↓" affordance into A1.

### A1 — WORLD (continents). Job: magnitude + the visibility-skew, across 14 countries.
- **Form: two linked views, a toggle between them (NOT a dual-axis chart — anti-pattern #1):**
  1. **Map** — self-contained SVG world (vendored simplified geo). 14 country marks. **Size = deployments,
     color = density (sequential blue).** So "big but pale" (US) vs "small but deep" (Japan/CH) is
     instantly legible — the skew, visually.
  2. **Ranked bar (default/fallback)** — countries sorted; emphasis form (bar length = a chosen metric,
     one hue). A metric toggle: Deployments · Density · Proof% (each its own single-hue bar, re-sorted).
- Hover → tooltip (name, deploys, density, proof%). Click a country → descend to A2 for that country.
- Table-view twin (a11y): the same numbers as a sortable table.

### A2 — TERRITORY (the interactive heart). Job: compare across country × industry, decide.
- **Form: heatmap grid** (choosing-a-form: "compare magnitude in a grid → heatmap"). This is the
  **decision-grid**: rows = 20 verticals, columns = 6 horizontals (functions).
- **Two modes, one control (the pivot):**
  - *Verdict mode* (default): each cell = status color + glyph (strong/active/talk/empty) — the
    "where good / hype / avoid / white-space" decision map.
  - *Magnitude mode*: each cell = sequential blue by deployment count.
- **Scope control** (one filter row, above the grid — never per-cell): All countries | pick one country.
  Switching re-renders the same grid against that slice (color follows meaning, not rank).
- Cell hover → count + verdict + top company. Cell click → A3 (that cell's companies).
- Row/column emphasis on hover (highlight one vertical or one function, gray the rest).
- Table-view twin.

### A3 — STREET (companies). Job: identity + evidence. Every one of the 1,628 rows lives here.
- **Form: a crafted table/list** (choosing-a-form: ">7 classes carrying meaning → a table"). Not a chart.
- Columns: company · use-case · existence (glyph) · value (self-claimed) · tier (P/I/S chip) · date · source↗.
- Sortable; existence + tier shown as glyph/chip (not color-alone); source is a real link.
- Sits in a panel that slides in from the grid; breadcrumb back up (World › Country › Vertical×Horizontal).

---

## IV. Navigation & shell
- **Linked drill-down** (locked): A0 → A1 → A2 → A3, each a crafted view; 200–300ms transitions;
  persistent **breadcrumb** for going back up. Not one infinite-zoom canvas.
- Single **filter row** convention (dataviz interaction rule): scope controls live above content,
  never inside a card.
- **Theme toggle** (light/dark), both validated. Respects OS, toggle wins.
- Everything keyboard-reachable; focus states mirror hover; every chart has a table twin.

## V. Tech (self-contained, durable)
- **D3.js vendored locally** into the HTML (no CDN — opens offline forever). SVG for map + grid.
- Data: `data/atlas.json` embedded inline at build → one standalone `karto-atlas.html`.
- Built by `scripts/build_atlas.py` (reads atlas.json, emits the HTML). Repo-owned, regenerable.

## VI. Build order (incremental, review each)
1. Shell + palette CSS vars + validate palette (light+dark) + theme toggle.
2. A0 orbit (hero + tiles + gap bar).
3. A1 world (map + ranked-bar toggle + tooltip + table twin).
4. A2 decision-grid (verdict/magnitude modes + scope filter + emphasis + table twin).
5. A3 street (drill table + breadcrumb + transitions).
6. Render-and-look pass on each; check against anti-patterns.md.

## VII. Anti-slop checklist (from anti-patterns.md — enforce on every screen)
- [ ] no dual-axis · [ ] color follows entity not rank · [ ] ≤8 categorical, ordered
- [ ] sequential = one hue · [ ] status = reserved + icon+label · [ ] thin marks, hairline grid
- [ ] no number on every mark (selective labels) · [ ] 2px surface gaps not borders
- [ ] tooltips enhance not gate · [ ] table twin exists · [ ] hero = sans, proportional figures
- [ ] validate_palette.js run + passing, light AND dark, before ship
- [ ] render & eyeball for collisions/overflow

## VALIDATED PALETTE (run through validate_palette.js — do not change without re-validating)
- Surfaces: light cream `#faf7f0` · dark `#1c1a17`
- Density ramp (A1 sequential, ordinal) LIGHT: `#dba85f,#cc9040,#bd7a26,#a4641b,#854c12,#6d3c09` (PASS on cream)
- Density ramp DARK: `#f0d4a0,#e0b06a,#cc8a38,#b06a1c,#9c5312` (PASS on warm-dark)
- Verdict status (A2): strong `#0ca30c` · active `#fab219` · talk `#d03b3b` (CVD ΔE 27.6 PASS; amber sub-3:1 → relief rule: ALWAYS glyph ●◐○ + label, never color-alone)
- Ink: primary `#211d17`/`#f5f1e8` · secondary `#5c554a`/`#c9c2b3` · muted `#8f8676`
- gridline `#e7e1d3`/`#302c26`

## Status
- [x] Concept, architecture, data cooked (atlas.json w/ verdicts + dates)
- [x] Design plan (this doc)
- [x] Warm palette validated (light + dark), verdict set CVD-safe
- [ ] build A0 → A1 → A2 → A3
