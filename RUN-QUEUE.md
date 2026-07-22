# KARTO SWEEP — autonomous run queue (do NOT stop until ALL done)

USER DIRECTIVE (standing): keep sweeping through Wave 1 AND Wave 2 to the very end.
As soon as one country agent finishes, spin up the next queued country. Keep ~6 concurrent.
Do NOT ask questions, do NOT stall, do NOT wait for the user. Run to the real end AT ALL COSTS.

## Concurrency target: ~6 sweep agents at once (proven safe with internal pacing)

## WAVE 1 (12 countries) — universe files EXIST in data/universe/
- [x] NL Netherlands — DONE (32 rows, 23 confirmed)
- [x] SA Saudi Arabia — DONE (63 rows, 26 confirmed)
- [x] AU Australia — DONE (55 rows, 34 confirmed)
- [x] SE Sweden — DONE (42 rows, 30 confirmed)
- [x] IL Israel — DONE (45 rows, 28 confirmed)
- [x] SG Singapore — DONE (45 rows, 24 confirmed)
- [x] DK Denmark — DONE (40 rows, 19 confirmed)
- [x] TW Taiwan — DONE (81 rows, 54 confirmed) — WAVE 1 COMPLETE
- [x] CA Canada — DONE (66 rows, 32 confirmed) — ALL 23 COMPLETE
- [x] AE UAE — DONE (44 rows, 33 confirmed) — WAVE 1 fully done bar CA
- [x] HK Hong Kong — DONE (127 rows, 105 confirmed)
- [x] ZA South Africa — DONE (55 rows, 29 confirmed)

## WAVE 2 (11 countries) — universe files BUILT ✅ (287 companies, ready to sweep)
- [x] MX Mexico — DONE (56 rows, 13 confirmed)
- [x] IE Ireland — DONE (24 rows, 7 confirmed)
- [x] BE Belgium — DONE (29 rows, 16 confirmed)
- [x] NO Norway — DONE (53 rows, 37 confirmed)
- [x] FI Finland — DONE (39 rows, 36 confirmed)
- [x] PL Poland — DONE (42 rows, 28 confirmed)
- [x] TR Turkey — DONE (48 rows, 21 confirmed)
- [x] ID Indonesia — DONE (58 rows, 15 confirmed)
- [x] AT Austria — DONE (31 rows, 17 confirmed)
- [x] VN Vietnam — DONE (37 rows, 19 confirmed)
- [x] PT Portugal — DONE (26 rows, 19 confirmed)

## ON EACH COMPLETION NOTIFICATION:
1. Mark the finished country [x] here.
2. If any country is QUEUED and running count < 6 → launch it (use the per-country sweep prompt template).
3. If Wave 1 queue empty and Wave 2 universes ready → start launching Wave 2 countries.
4. Only when ALL 23 countries are [x] → run FINAL MERGE: append-only merge new .md files
   (NEVER full-rebuild from .md — the drift-fix lives only in register.csv), then
   cook_aggregates.py → build_atlas.py → commit → push. THEN and only then stop.

## Per-country sweep prompt template: see the ones already issued (read SWEEP_RULES.txt + CLASSIFICATION.md,
## one universe file, 11-col output to data/register/register_<CC>.md, paced, native language).
