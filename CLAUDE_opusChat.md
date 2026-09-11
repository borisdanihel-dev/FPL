# FPL toolchain — project context

Personal Fantasy Premier League analysis tooling. Windows, Python 3.14, stdlib only,
no third-party dependencies. Written 2026/27 season, currently after GW3.

Read `FPL_PLAN.md` for the season plan and deadlines.

---

## Files

| File | Lines | Role |
|---|---|---|
| `fpl_sync.py` | 494 | FPL API → SQLite (`fpl.sqlite`) → `fpl_export_gwN.json` |
| `fpl_edge.py` | 1732 | Reads the export, prints analysis. 16 sections. |
| `test_fpl.py` | 890 | 67 tests, stdlib `unittest`, no network |
| `fpl_run.bat` | — | Daily scheduled task: test → sync → record → report |
| `FPL_PLAN.md` | — | Dated runbook, deadlines in Prague time |
| `projection_log.csv` | — | Append-only forecast log, point-in-time |

Two-stage pipeline. `fpl_sync.py` needs network and writes the export;
`fpl_edge.py` is offline and reads it. Nothing else couples them.

```
python fpl_sync.py                  # daily
python fpl_sync.py --refetch        # re-pull finished GWs (backfills new columns)
python fpl_sync.py --history        # previous-season baselines, ~600 calls, cached
python fpl_edge.py --brief          # 20-line pre-deadline summary
python fpl_edge.py --record --source xg
python fpl_edge.py --section calibration
python test_fpl.py
```

Sections: arbitrage, backtest, bench, brief, calibration, compare, consistency,
defcon, eo, fdr, league, sensitivity, squad, ticker, value, wildcard.

---

## Context

Entry 3073318 "1. FC Kiripolcz", league 455565, 7 managers. 6th of 7 after GW3,
204 points, 39 behind. All four first-half chips unused; four rivals burned
Triple Captain in GW3 on a 9-point Haaland.

Plan: roll GW4 and GW5, Wildcard GW6, Triple Captain GW7 (City home to Ipswich),
Bench Boost GW8 if the bench is genuinely nailed. Free Hit held as insurance,
hard cutoff GW16–17.

---

## Measured findings

All from this season's data, all reproducible from the export. **These are the
output that matters — the code is scaffolding around them.**

**Form is anti-predictive.** GW1–2 points per 90 predicting GW3 points:
Spearman −0.202, SE ≈ 0.10. Significantly negative. xG is less bad (−0.077)
than goals (−0.092), both less bad than points, but none is positive yet.

**FDR predicts clean sheets, not goals.** Over 30 matches: teams rated easy
(FDR ≤2) versus hard (≥4) scored 1.38 vs 1.31 goals — a 0.06 gap, noise.
Clean sheets 38% vs 12%. Monotonic: 38 / 29 / 17 / 0 across FDR 2–5.

**Only defenders are fixture-sensitive**, and only at the hard end. Per
player-match with 95% intervals: DEF +1.27 (0.25 to 2.30, REAL); GK +1.62,
MID +0.54, FWD +1.44 — all intervals span zero. Decomposed: FDR 2 vs 3 is
−0.06 (nothing), FDR 3 vs 4+ is +1.33. **Avoid red fixtures for defenders;
green versus amber is not worth a transfer.** Home/away: nothing significant.

**42% clean sheet rate** across 60 team-matches — higher than expected, makes
cheap nailed defenders more attractive than they look.

---

## Failed approaches — do not retry without new evidence

The points-based `project()` failed three times. Bar is: mean absolute error
versus a constant predictor (predict the league mean for everyone), and Spearman
rank correlation. Ordering is what a squad picker needs; below ~+0.20 it's unusable.

| Attempt | MAE | vs constant 2.38 | rho |
|---|---|---|---|
| shrinkage to positional median | 2.51 | worse | −0.073 |
| + fixture term (actual per-match FDR) | 2.47 | worse | −0.025 |
| + personal priors (last-season ppg) | 2.55 | worse | −0.026 |

Quintile bias is inverted: the players it rates lowest outscore the ones it
rates highest (Q1 bias −1.92, Q5 +1.08). Three gameweeks cannot support
per-player point forecasting.

`project()` is retained only as the `own` baseline in the head-to-head. It
should not drive decisions.

---

## Open work

**In flight — `project_xg()`, the bottom-up model.** Expected points assembled
from scoring rules rather than fitted weights: appearance from start rate,
goals from season xG/90 × position value (GK/DEF 6, MID 5, FWD 4), assists
from xA/90 × 3, clean sheet from *measured* CS rate by FDR bucket × 4 (GK/DEF)
or 1 (MID), DEFCON from measured hit rate, small ICT-percentile bonus term.
Components shrink toward last season's xG/xA per 90 with weight
`max(2, 8 − gws_played)`.

Logged as `source="xg"` alongside `own` from GW4. `--section calibration`
grades both on identical weeks. **Needs three graded gameweeks (GW4–6) before
the result means anything.** Do not act on one week.

**Not started, in order:**
1. Transfer-aware mode — best 1–2 moves from the current squad, hit-adjusted.
   Downstream of a projection that works; useless against rho ≈ 0. Not needed
   until GW7 (GW4/5 are rolls, GW6 is the wildcard).
2. Bench Boost screen — cheapest *nailed starters* with high floors, not
   cheapest players. Lifting the bench from £4.0m to £5.5m costs ~£6m from the
   XI to gain ~8 points in one week. The chip's value comes from bench players
   *starting*, not from being expensive.
3. Starts floor for `--section wildcard` — current filter is `mins_last4 >= 45`,
   far too weak. Use started-every-available-gameweek. **Do not add an ownership
   floor** — ownership measures popularity, and low ownership is the edge in a
   7-man league (Khalaili, 0.2% owned, is the best arbitrage candidate found).

**Socket built, untested:** `--section compare --projections file.csv` scores
any external projection against the same bar, with a DEFCON correction for
models predating 2025/26. Intended for OpenFPL (`github.com/daniegr/OpenFPL`,
MIT). Caveat: trained on 2020-21 to 2023-24, so it has never seen DEFCON or the
current BPS weighting, and it ships no data pipeline — ~200 features per
position must be built from FPL and Understat by hand.

---

## Working practices

Every one of these came from a bug that reached production.

**Verify patches applied.** Two string-replace patches silently matched nothing
and reported success (`entry_id` in the export, `--refetch` CLI flag). Check the
diff, not that the file still parses.

**Verify new code is wired in.** `personal_priors()` was written, tested, and
never called — 595 API requests fetched data that sat unused, and the backtest
output was byte-identical before and after. If you add a function, add a test
that fails when it isn't called.

**Tests must assert on behaviour, not source text.** A regression test checking
for the string `project(p, tick` failed when the code was fixed correctly.
Replaced with: changing only the forward ticker must not move a backtest of a
past gameweek.

**Tests must not be able to skip their own assertion.** The blank-gameweek test
had a conditional guard and passed with the bug deliberately reintroduced.
Always reintroduce the bug and confirm the test fails.

**Test at future gameweeks.** Three bugs in `project_xg` were invisible at GW3
and wrong by GW5: season xG divided by a 4-gameweek minutes window, `p_start`
decaying as `starts_last4/gws_played`, and blank gameweeks getting a default
FDR. Tests simulate GW10, GW20, GW38.

**`is None`, not `or`.** `p.get("starts_last4") or p.get("starts")` treats a
genuine zero as missing, so a dropped player falls back to season starts.

**Windows console is cp1252.** Player names contain ć, ß, ø, í. `force_utf8()`
plus a per-stream try/except in `_Tee`; `fpl_run.bat` sets `PYTHONIOENCODING`
and `chcp 65001`.

**Point-in-time discipline.** `record_projections` refuses to write once a
gameweek's deadline has passed (first kickoff minus 90 minutes). Without it the
log fills with hindsight the first time it runs on a Sunday.

**Put confidence intervals on everything.** Four of five "findings" in the
fixture-sensitivity table did not survive them. An earlier FDR conclusion was
stated confidently from 10 hand-entered matches with borrowed ratings and was
*reversed* by the full 30-match sample.

**Never fabricate inputs.** If data is missing, say so and stop. The reversed
FDR finding came from injecting stand-in ratings to make a section run.
