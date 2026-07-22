# Run Control — Long-Running Sweep: Track / Pause / Resume

The sweep spans many sessions. This file defines how we keep it **visible, pausable, and resumable** — so it is never a black box.

## The 4 guarantees
1. **Live visibility** — see progress any time, not only at the end.
2. **Pause anytime** — stop with (at most) one company's work lost.
3. **Resume exactly** — pick up where it stopped, across sessions & context loss.
4. **Verify as it goes** — spot-check rows mid-run, not just at merge.

## Source of truth
- **Local files = truth + checkpoint.** Each agent writes `register_<CC>.md` + `findings_<CC>.md`, flushed **per company** (not batched at end).
- **Google Sheet = dashboard + consolidated view.** Never the live write target for parallel agents (API races + ~60 writes/min rate limit).
- **Progress tab = the trust surface.** Live status per country.

## Checkpoint granularity
- **Per company.** Agent: pick company → search → gate → write row(s) to local file → update its progress counter → next.
- Pause = just stop. Lose at most the one company in flight.

## Resume rule (read-state-first)
- On (re)launch for a country, agent MUST:
  1. Read its own `register_<CC>.md` → list companies already done.
  2. Skip done companies. Continue with the remainder.
- A cold-context session reconstructs everything from local files + Progress tab. No conversation memory required.

## Progress tab schema (live dashboard)
`country · status · companies_done · companies_total · last_company · verticals_covered · last_updated · notes`
- status ∈ {not_started, running, paused, done, partial}
- Updated after each company (or each sync).

## Sync cadence (local → Sheet)
- **DECISION PENDING (user):** every ~5 companies (live-ish, more API calls) VS on-demand ("sync" command, less overhead).
- Sync = single-writer batched merge (one `batchUpdate`), no race.

## Status command (DECISION PENDING — user)
- A small script I run to print / refresh the Progress tab on demand → eyeball where we are anytime.

## Pause / carry-on protocol
- **Pause:** stop agents. Local files + Progress tab already hold state. Nothing else needed.
- **Carry-on:** relaunch agent(s) for unfinished/partial countries → they read-state-first → continue.
- **Merge:** whenever (periodic or at end), single-threaded, local files → Sheet Register/Findings/Noise tabs.

## Sheet
- ID: `<KARTO_SHEET_ID — in karto.config>`
- URL: <your Google Sheet URL — see karto.config>
- Tabs: Register · Findings · Noise · Progress

## Open decisions (need user)
1. Sync cadence: every ~5 companies **or** on-demand?
2. Build the `status` command? (y/n)
