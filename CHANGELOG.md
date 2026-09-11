# Changelog

Every entry records what was **measured**, not just what was done.

---

## 2026-09-07 — GW4 projection_log audit (no code change)

**Why:** `projection_log.csv` was written 12:30:13; `fpl_edge.py` was modified
12:36:35 and `fpl_edge_xg_fixes.patch` created 12:33:40 — both *after* the GW4
forecasts were recorded. Point-in-time rows cannot be regenerated after a
deadline, so a pre-patch row would be a permanently lost graded gameweek.

**Method:** regenerated GW4 forecasts from the frozen `fpl_export_gw3.json`
(unchanged since 11:34) into a scratch log with current code, and separately
reimplemented the pre-patch `project_xg` + `xg` record loop from the `-` side
of the patch. Compared all three sets by `player_id`.

**Measured:**

| comparison | n | value diffs |
|---|---|---|
| logged `own` vs current code | 276 vs 276 | 0 |
| logged `xg` vs current code | 259 vs 259 | 0 |
| pre-patch `xg` vs current code | 259 vs 259 | 0 |

**Control** (guards against a dead reconstruction silently "agreeing"): nailed
midfielder, season xG accruing, `starts_last4 = 4`, `mins_last4 = 360`:

| GW | pre-patch | current | delta |
|---|---|---|---|
| 4 | 4.790 | 4.790 | +0.000 |
| 10 | 3.176 | 4.790 | +1.614 |
| 20 | 2.638 | 4.790 | +2.152 |
| 38 | 2.383 | 4.790 | +2.407 |

**Conclusion:** the three xG fixes are a mathematical no-op at GW3→GW4
(season minutes == last-4 minutes through GW4; `min(4, 3)` == `gws_played` == 3;
all 20 teams have exactly one GW4 fixture, so no blank and no double). The 259
logged `xg` rows and 276 `own` rows are **valid and gradeable**. The patch is
load-bearing from GW5 onward — by GW10 the pre-patch code understates a nailed
starter by 34%.

**Verified separately:** `next_deadline(d, 4)` = `2026-09-12 12:30:00+00:00`
= 14:30 CEST, which matches `FPL_PLAN.md`. `CLAUDE_fable chat.md` states
15:30 CEST — that document is wrong by one hour.

---

## 2026-09-07 — mutation audit of the `project_xg` regression tests

**Why:** 67 green says nothing about whether a fix is *protected*. This project
has already shipped two tests that passed with the bug present.

**Method:** copied `fpl_edge.py` / `fpl_sync.py` / `test_fpl.py` / the real
export into a scratch dir (sandbox verified green, 67 tests, 0 skips — note
`test_matches_the_real_export` self-skips when no export sits alongside it),
then reintroduced each fixed bug one at a time and ran the full suite. Each
mutation asserts its target string exists before replacing, so a silent
no-op patch fails loudly.

**Measured — before:**

| mutation | tests red | caught by |
|---|---|---|
| M1 season xG over last-4 minutes | 1 | `test_xg_rate_uses_season_minutes_not_last_four` |
| M2 `p_start` denominator decays | 2 | `test_start_probability_does_not_decay_over_the_season` (+M1's) |
| M3 `or` hides a genuine zero | 1 | `test_zero_recent_starts_is_not_treated_as_missing` |
| M4 blank GW gets default FDR | 1 | `test_blank_gameweek_gets_no_forecast` |
| M5 double GW not summed | **0** | **nothing** |

**Gap found:** `test_double_gameweek_sums_both_fixtures` called `project_xg`
twice itself and asserted `one + other > one` — arithmetic on its own two
locals, true for any positive projection. The summing lives in the `xg` branch
of `record_projections`, which the test never called, so removing the sum could
not fail it.

**Fixed:** added `double_team=` to `make_export` (mirrors the existing
`blank_team=`), and rewrote the test to drive `record_projections` end-to-end
on two otherwise-identical exports — one with a single fixture, one with a
double — asserting the *logged* value for every player on that team is more
than 1.5x the single-fixture value.

**Measured — after: 5/5 mutations caught, M5 now red via
`test_double_gameweek_sums_both_fixtures`.** Suite still 67 green (the test was
replaced, not added). The file proven red under M5 in the sandbox is
byte-identical to the one now in the repo.

---

## 2026-09-07 — gate `--record` on a green test suite (`fpl_run.bat`)

**Why:** the batch aborted on the step whose output is regenerable (`EDGE FAILED`
-> `exit /b 1`; the report is just a re-render of the export) and ran straight
through the only step whose output is permanent (both `--record` calls, no
`errorlevel` check at all). A red suite means the projection code is suspect,
and the response was to write point-in-time forecasts from it. Those rows freeze
at the deadline and cannot be regenerated, so one bad set silently contaminates
the calibration table the wildcard decision rests on.

**Change:** `set TESTS_OK=0` inside the existing `if errorlevel 1` block; the
record step is wrapped in `if "%TESTS_OK%"=="1" (...) else (echo SKIPPED ...)`.
Set inside the block, read outside it, so no delayed-expansion trap. Sync and
the report still run unconditionally — their output is regenerable.

**Measured:** exercised offline in a scratch dir with stub `test_fpl.py` /
`fpl_sync.py` / `fpl_edge.py`, driving both branches:

| suite | `--record` | sync | report |
|---|---|---|---|
| green | both calls ran | ran | built |
| red | **skipped**, `SKIPPED --record` logged | ran | built |

The file applied to the repo is byte-identical to the copy that passed both.
Backup of the previous version in the session scratchpad.

**Trade accepted:** a red suite now costs that day's recording. Correct
direction — a missing forecast is a visible gap, a wrong one is permanent and
invisible — but a test failure during a deadline week must be fixed same-day.

---

## 2026-09-07 — first automated run of the record step

`\FPL_SYnc` fired 23:55:06, completed 23:55:22 (16s). `Ran 67 tests / OK`, then
`recorded 276 forecasts for GW4 as 'own'` and `259 as 'xg'`, 4d 14h before the
deadline. This was the **first time `--record` ran under the scheduler** — the
only prior automated run (06/09 23:24) predates the rewrite of `fpl_run.bat`
and did tests-less sync + report only.

**Measured — daily re-recording is a no-op between gameweeks.** Tonight's rows
are numerically identical to the 12:30 manual run: 276/276 and 259/259 matched,
**0 values moved**, despite a fresh sync writing a new export (+168 bytes of
price/transfer churn). No matches are played between a gameweek settling and the
next deadline, so every projection input is static. Forecasts should only move
when results land or when injury news shifts `status` / `chance_next_round` —
i.e. late in the week, not mid-week.

**Amendment — why the daily cadence is still required.** The entry above is
about *re-recording forecasts*, which is genuinely idempotent between
gameweeks. It is not an argument that the daily sync is redundant. The sync
exists to accumulate `price_history`, and that is the one thing in the pipeline
that **cannot be backfilled**: `bootstrap-static` serves only `now_cost`, there
is no historical price endpoint, and `cost_change_start` gives the cumulative
net move but not when it happened. A skipped day is a permanent hole. So a
missed run does cost something after all — just not a forecast.

State: 2 samples (2026-09-06, 2026-09-07), 0 gaps. The single overnight window
captured **25 price changes**, 22 down and 3 up, including Shaw £4.5 -> £4.4
(owned). The mechanism works.

**Timing is well chosen.** FPL reprices at ~01:30 UK (00:30 UTC while BST).
The 23:55 CEST run is 21:55 UTC — about 21 hours after that day's change and
before the next — so each run is exactly one clean sample per price cycle.
Note the recovery boundary: `price_history.date` is the **UTC** date, so a
catch-up run must fire before 02:00 CEST (00:00 UTC) to land on the missed
day's row. Later than that it stamps the following day and the hole is
permanent.

**Wart found: `price_changes_7d` mislabels its window.** The query takes
`b.date = (SELECT MIN(date) FROM price_history WHERE date >= date('now','-7 day'))`
— the *oldest sample within* seven days, not the sample seven days ago. With
fewer than 7 days of history, or after any gap, the column `price_7d_ago` is
not 7 days ago and nothing says so. Live right now: tonight's export carries 25
rows under `price_7d_ago` that are a **1-day** change. Not urgent — it becomes
correct once 7 unbroken days accumulate — but it will silently under-report the
window after any missed run.

---

## 2026-09-11 — the rank-correlation ruler is broken (measurement only, no code change)

**Why:** `BACKLOG.md` P1 and P5 both say to run on "the existing backtest
harness". Before relying on it for a decision that sets the wildcard basis, I
checked whether the harness can measure what they ask.

**Method:** read-only against `fpl.sqlite`, which — unlike the export — keeps
zero-minute rows. GW1-2 → GW3, players with 90+ minutes in GW1-2. Compared
`E._spearman` against a tie-corrected (average-rank) Spearman; re-ran
`E._spearman` under 300 random input orderings; replicated `gw_index()`'s exact
row order; and captured the live `sec_backtest` inputs by wrapping
`E._spearman`.

**Measured — three defects:**

1. `_spearman` breaks ties by input order. 16% of player pairs are tied on
   actual points.
2. The input order is correlated with the prediction: the export's
   `ORDER BY g.event, g.total_points DESC` ranks high-scorers-from-week-one
   lowest among tied actuals, pushing form-based rho negative.
3. Grading only ever sees players who played in the target week
   (`fpl_sync.py:415`, `fpl_edge.py:1554`). 18 of 225 (8%) got no minutes in GW3.

| quantity | as computed | tie-corrected |
|---|---|---|
| form GW1-2 → GW3, export row order | −0.112 | −0.009 (CI −0.146 .. +0.127) |
| same, reversed row order | +0.097 | −0.009 |
| `sec_backtest` on tonight's export | −0.026 | +0.059 (random orders: +0.018 .. +0.090) |
| minutes share → GW3, played only | — | +0.061 (CI −0.076 .. +0.197) |
| minutes share → GW3, benched = 0 | — | **+0.194 (CI +0.063 .. +0.325)** |
| starts per GW → GW3, benched = 0 | — | +0.142 (CI +0.011 .. +0.273) |

**Conclusions:** the headline "form is anti-predictive (−0.202)" does not
survive — form is non-predictive, not anti-predictive. `project()`'s failure
stands on MAE but "rates backwards" was an artifact. Minutes share is the
strongest single signal measured so far, and the current harness would have
reported it as noise. `sec_backtest` reporting −0.026 outside all 300 random
orderings shows the bias is systematic, not variance.

Also measured for P2: 64 of 740 consecutive-PL-match gaps this season are
under 4 days, 81 are 4–5.

Full write-up and the resulting reprioritisation: `BACKLOG.md` Part 2. Nothing
changed in code; suite still 67 green.

---

## 2026-09-11 21:15 CEST — P1 predictor definition FROZEN (BACKLOG Part 3, G2)

Frozen before GW4 kicks off (Sat 12 Sep 16:00 CEST). **Do not edit this entry.**
The git commit that adds it is the timestamp. GW3 was already inspected for two
candidate predictors and is exploratory; GW4 and GW5 are clean tests only
because the definition below was fixed before they were played.

> Minutes share over the last `min(4, gws_played)` gameweeks.
> Population: the recorded `xg` forecast set.
> Benched but team played = 0. True blank gameweek = excluded.

Use, per BACKLOG Part 3 D1: floor protection (exclude players likely to blank),
**not** ranking the players who start.
