# FPL Edge — project handoff for Claude Code

Owner: Boris (FPL entry 3073318, "1. FC Kiripolcz"), mini-league 455565
("VAR Wars: Revenge of the Ref", 7 teams). Season 2026/27. Working dir on
Windows: `C:\Users\Boris\Documents\FPL`. Python 3.14. Prague timezone (CEST/CET).

## What this project is

A local FPL decision tool. It pulls the public FPL API into SQLite, exports a
JSON bundle, and prints a text report that answers: how am I doing against my
six rivals, which of their players hurt me, what should I transfer, and — the
part that matters most — **are my own projections any good?**

Everything is standard-library Python. No pip. Keep it that way.

## Files

| file | role |
|---|---|
| `fpl_sync.py` (494 lines) | API → SQLite (`fpl.sqlite`) → `fpl_export_gwN.json`. Schema migrations in place, so old DBs upgrade. |
| `fpl_edge.py` (1816 lines, 2026-09-11) | Report generator. ~16 sections, `--section a,b,c`, `--brief`, `--diff` (vs previous export), `--out file`, `--record --source own\|xg` (forecast logging), `--horizon N`. |
| `test_fpl.py` (1031 lines, 75 tests, 2026-09-11) | unittest. Synthetic export dicts, no network. Run before every change. |
| `fpl_run.bat` | Daily job: tests → sync → record both forecast sources → report. UTF-8 forced (`PYTHONIOENCODING`, `chcp 65001`) because player names have accents. |
| `projection_log.csv` | Point-in-time forecasts. Columns: `made_at,source,event,player_id,web_name,predicted`. |
| `reports/` | dated report + run log per day |
| `fpl_xg.py`, `test_fpl_xg.py` | **gone** — the obsolete standalone xG module is not in the folder (checked 2026-09-11). |

## Data flow

```
bootstrap-static, fixtures, event/{gw}/live, leagues-classic/{id}/standings,
entry/{id}/{history,transfers}, entry/{id}/event/{gw}/picks,
element-summary/{id} (player_history, set-piece orders)
        │  fpl_sync.py
        ▼
fpl.sqlite: teams, players, price_history, events, fixtures, player_gw,
            player_history, entries, standings, entry_gw, picks, transfers, chips
        │  export()
        ▼
fpl_export_gwN.json  sections: standings, chips_used, squads, transfers,
  league_ownership, top_players_recent, all_players, player_gw_recent,
  fixtures_played, player_history, teams, fixtures_next6, price_changes_7d
        │  fpl_edge.py
        ▼
report text  +  projection_log.csv
```

The FPL API marks a gameweek `finished` only after the last match and bonus
are final; `fpl_sync.py` therefore treats "finished OR is_current" as the
latest GW and re-fetches in-progress weeks on every run.

API quirks learned the hard way: standings/picks endpoints can lag the app by
hours (bonus and DefCon settle late); `leagues-classic/.../standings/` with a
trailing slash once served a stale cache. Names come only from
`bootstrap-static` — everything else is element IDs.

## Non-negotiable design rules

1. **Forecasts are recorded before the deadline or not at all.** `record_projections`
   refuses to write once `next_deadline(gw)` (first kickoff − 90 min) has
   passed. Re-running before the deadline replaces the pending rows. This is
   what makes `sec_calibration` honest. Never weaken it.
2. **Two models, one log, judged head to head.** `source="own"` is the
   points-based model (`project()`); `source="xg"` is the bottom-up model
   (`project_xg()`). `sec_calibration` grades both against actual GW points,
   per week and per position, against a constant baseline. Let the table
   decide which model wins; do not tune by eye.
3. **Shrink components, not outputs.** The GW3 backtest showed that pulling
   final points toward last season's ppg made things *worse* (Spearman −0.03).
   Shrinking xG/90 and xA/90 toward last season's rates is fine because those
   inputs are stable. Prior weight decays: `max(2, 8 − gws_played)`.
4. **No double counting.** `defcon_expectation()` already returns points per
   start (`2 × hit rate`) — use it once, unscaled. Do not add a penalty bump:
   xG already contains spot-kicks (~0.76 each). `pens_order` is a forward-looking
   signal for someone who hasn't taken one yet, not an additive term.
5. **Measure, don't invent.** Clean-sheet probability comes from
   `cs_rate_by_fdr()` (actual results by difficulty bucket, min 6 samples,
   pooled fallback), not from FPL's 1000–1400 strength scale. Same philosophy
   for anything else: if the DB can measure it, measure it.
6. Every projection term should be a scoring rule you can read and argue with,
   not a fitted weight.

## Known bugs — FIXED (patch applied and mutation-verified 2026-09-07; patch file removed 2026-09-11, see git history)

In `project_xg` / the `xg` branch of `record_projections`:

- `xg90 = p["xg"] / mins_last4 * 90` — season xG over last-4 minutes. Identical
  through GW4, inflates from GW5. Use `p["minutes"]`.
- `p_start = starts_last4 / gws_played` — decays as the season lengthens
  (4/10 = 0.4 for a nailed player by GW10). Denominator must be `min(4, gws_played)`.
- Blank GW gets `fdr=3` via `min(..., default=3)` and a positive forecast.
  Skip when no fixture; for a double gameweek **sum** the fixtures.

Known omissions (not bugs; fix when calibration shows the bias):
- no goals-conceded penalty (−1 per 2 for GK/DEF), no save points for GKs
- `exp_mins = 90 × p_start` ignores sub-60 risk (Calafiori is hooked before
  the hour often; `player_gw_recent` has minutes per game to build a p60)
- `saves` is in the `player_gw` table but not in the `player_gw_recent` export

## Backlog, in priority order — superseded by `BACKLOG.md` (Parts 1–3)

1. Apply the three fixes above; add tests for each (a season-vs-window minutes
   test, a p_start-at-GW10 test, a blank-GW test).
2. Add `saves` to `player_gw_recent` export; add GK saves and GC penalty to
   `project_xg`; re-run calibration.
3. Transfer-aware optimizer: best 1–2 moves from the *current* squad,
   hit-adjusted (−4), respecting 3-per-club, budget, and `estimate_free_transfers`.
   `sec_wildcard` builds from scratch; `sec_arbitrage` is position arbitrage —
   neither answers the weekly "what do I actually do" question.
4. Wildcard builder: add a minutes/ownership floor for the XI so it stops
   drafting a 3%-owned bench keeper as starter; keep 3-per-club cap.
5. Effective-ownership in the mini-league should include captaincy multipliers
   (currently ownership only; the captaincy block is historical).
6. Once Claude Code has network access, `fpl_sync.py` can be run directly and
   the report generated on a schedule — the JSON upload step exists only
   because claude.ai chat cannot fetch arbitrary URLs.

## How to run

```
python test_fpl.py                                   # must be green
python fpl_sync.py                                   # sync + export latest GW
python fpl_edge.py fpl_export_gw4.json               # full report
python fpl_edge.py fpl_export_gw4.json --brief       # short version
python fpl_edge.py fpl_export_gw4.json --section calibration,wildcard
python fpl_edge.py fpl_export_gw4.json --record --source own
python fpl_edge.py fpl_export_gw4.json --record --source xg
fpl_run.bat                                          # the whole daily job
```

Schedule `fpl_run.bat` daily (Task Scheduler) so `price_history` accumulates
and forecasts are recorded before each deadline. GW4 deadline: Sat 12 Sep
2026, **14:30 CEST** (corrected 2026-09-11; was 15:30 — `next_deadline()` gives 12:30 UTC).

## FPL context the code serves (so recommendations stay consistent)

- Squad after GW3: Verbrüggen, Kinsky; Van Dijk, Calafiori, Mitchell,
  N. Williams, Shaw; Bruno Fernandes, Szoboszlai, Elanga, Ndiaye, Slater;
  Haaland, João Pedro, Wissa. Bank £0.2m, value £100.3m, 1 FT for GW4.
- League after GW3: Lukáš 243, Jan 229, Alex 217, Simon 216, Ratul 208,
  **Boris 204 (6th)**, Honza 176. Boris's 59 was the best chip-adjusted score in GW3.
- Chips: Boris holds all four first-half chips (WC, FH, BB, TC — expire at the
  GW19 deadline, 2 Jan 2027). Lukáš and Alex have used BB and TC; Jan BB;
  Simon and Honza TC; Ratul none. This chip edge is the main strategic asset.
- Plan: 1 FT/week until GW5 (Ndiaye is a City starter — 266 min — so the
  planned Ndiaye→Groß is now optional), **Wildcard in the Sep 20–Oct 10
  international break** drafted for GW7+, **Bench Boost the week after**,
  **Triple Captain Haaland at home vs a promoted side (GW7 vs Ipswich is the
  candidate)**, Free Hit as insurance / spent by GW17–19.
- Strategy: cover the near-universal core (Haaland captain, Bruno), differentiate
  at the edges (Mitchell, Neco, Elanga/Wissa), never take −4 hits for sideways
  moves, chips as the sledgehammer. Rivals are reactive (Lukáš sold Mbeumo the
  week before he scored 8); Boris's edge is holding fixture-based positions.
- Watchlist: Isak, Mbeumo (United's run turns at GW7), De Cuyper (top attacking
  defender by xG+xA/90), Barcola (wait for two team sheets), Groß, Semenyo.
