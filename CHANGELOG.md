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

---

## 2026-09-11 — G1: the ruler fixed and every rho on record re-derived

**R1 — tie-corrected Spearman.** Tied values now share their average rank.
Test: shuffling the input rows must not change rho; known value
`rho([1,2,2,3],[1,2,3,4]) = 3/sqrt(10)`. Mutation (old ranker): both red.

**R2 — grade the whole population.** `grade_forecasts()` and
`backtest_population()` grade a benched player (team played, no row) as 0 and
leave a true blank ungraded; they join on element id when the export carries
it. Tests: benched graded as 0, blank not graded, shared web_name graded
separately, backtest keeps benched and drops blanks. Mutations: 5 of 5 red.
Recording path untouched: GW4 regenerated with the patched code, 529/529
identical to the log.

**Found while building R2 — two more grading defects, not yet fixed** (both
need `fpl_sync.py`, deferred until after the 11 Sep 23:55 run so nothing on
tonight's path changed):
- 17 web_names are shared by 2+ players; 13 of them (Palmer, Johnson, James,
  King, Martinez, ...) are in the GW4 log. `player_gw_recent` has no player id,
  so name-keyed grading summed both players' points. The grader now uses ids;
  the export must start carrying them.
- A double gameweek exports **two** rows per player, each carrying the full
  gameweek total (the fixtures join fans out). Synthetic check: 12 real points
  graded as 24. Latent until the first DGW.

**R3 — every rho on record, re-derived.** The old ruler reproduces all three
failed-attempt rows exactly (MAE 2.51/2.47/2.55, const 2.38, rho
−0.073/−0.025/−0.026), so the reconstruction is faithful.

| `project()` attempt | MAE | const | old rho | fixed rho (95% CI) |
|---|---|---|---|---|
| 1 shrink to positional median | 2.49 | 2.36 | −0.073 | +0.152 (+0.020..+0.283) |
| 2 + fixture term | 2.45 | 2.36 | −0.025 | **+0.182** (+0.050..+0.313) |
| 3 + personal priors | 2.55 | 2.36 | −0.026 | +0.151 (+0.019..+0.282) |

Still fails: MAE loses to a constant in every row, no rho reaches +0.20. But
every interval clears zero — weak, not absent. Played-only, attempt 3 is
+0.059, so most of it is spotting who gets benched (BACKLOG Part 3 D1).

Quintile pattern: mean actual points **rise** with the projection (Q1 2.93 →
Q5 3.83). "The lowest-rated outscore the highest-rated" was a per-quintile
bias misread as a cross-quintile comparison — it is overconfidence (spread too
wide: bias Q1 −1.04, Q5 +1.70), not inversion.

Form, GW1-2 per 90 → GW3, fixed ruler: points +0.061 (CI −0.070..+0.193), xG
+0.133 (+0.002..+0.265), goals +0.135 (+0.004..+0.267). The recorded
−0.202 / −0.077 / −0.092 do not reproduce under either ruler with this
population.

**Verdicts.** `_rho_verdict` ignored sample size and called +0.151 on 224
players "no signal - this is noise". It now reads the 95% interval: +0.151/224
→ "real but weak - below the +0.20 bar"; +0.30/20 → "indistinguishable from
zero". Mutation (interval ignored): red. Printed claims in `sec_wildcard` and
`sec_compare` ("no better than shuffling", "rho near zero") and the two
findings in `CLAUDE_opusChat.md` corrected, with the old claim kept visible.

Suite: 67 → 75 tests, all green.

---

## 2026-09-11 — A2 measured (not applied), A1 built

**A2 — starts floor on `--section wildcard`: counted, not applied** (per Part 3,
the floor waits for P1). Window = last 3 GWs, status `a`:

| filter | GK | DEF | MID | FWD | all |
|---|---|---|---|---|---|
| current `mins_last4 >= 45` | 21 | 104 | 122 | 26 | 273 |
| strict: started all 3 | 18 | 63 | 64 | 14 | 159 |
| loose: started 2+ of 3 | 20 | 81 | 92 | 19 | 212 |

No position thins below a squad's needs (2/5/5/3) under either. All 15 of the
current squad pass strict. **Khalaili — the best arbitrage candidate found —
fails strict** (2/3 starts, 199 min) and survives only the loose floor. That is
the concrete cost of "started every available gameweek", and it should be
weighed when P1 reports.

**A1 — rest days in `--brief`.** `days_since_last_PL_match()` gives days from a
team's previous PL kickoff to its first kickoff in the target GW; the XI block
shows it as `rest Nd` with a printed caveat that it is a calendar fact, its
effect on points is untested, and cup/European minutes are invisible to the
API. No marker for short rest — it must not read as a reason to bench someone.
GW4 XI: 5–9 days everywhere. Tests: 22-day and 3-day turnarounds computed
exactly; brief prints the caveat. Mutations (earliest instead of previous
kickoff; caveat dropped): both red.

Suite: 75 → 78, all green.

---

## 2026-09-11 — G4 version control, G5 hygiene (logged late: first recorded only in commit messages)

**G4 — `git init`.** Baseline commit `8f705cb` (67 green). Tracked: code,
tests, `fpl_run.bat`, docs, and `projection_log.csv` — the point-in-time log is
the one data file that cannot be regenerated, and its history now shows what
was forecast and when. Ignored: `fpl_export_gw*.json` and `reports/`
(regenerated every run), `__pycache__/`. **`fpl.sqlite` is ignored and has no
backup** — it is binary, rewritten nightly, and holds the only copy of
`price_history` (5 daily samples, 6–10 Sep, no gaps), which cannot be
backfilled from the API. Back it up separately. `fpl_edge_xg_fixes.patch`
removed in `03b91a9`; applied and mutation-verified 2026-09-07, content kept in
the baseline.

**G5 — hygiene.**
- `sec_eo` divided by `n_rivals` unguarded; a one-entry league crashed with
  ZeroDivisionError. Now prints "no rivals to compare against" and returns.
  Test `test_one_entry_league_does_not_crash_ownership`; mutation (guard
  disabled): red.
- `sec_backtest` built a ticker it overwrote inside its loop; `sec_wildcard`
  assigned a `quota` it never read. Both removed — dead code, no behaviour
  change (the ticker removal landed in the same commit as R2, whose effect on
  backtest output is recorded in the G1 entry).
- `CLAUDE_fable chat.md`: GW4 deadline 15:30 → **14:30 CEST** (per
  `next_deadline()`: 12:30 UTC); line/test counts updated to 1816 / 1031 / 75;
  `fpl_xg.py` marked gone (not in the folder); known-bugs section marked fixed;
  backlog section pointed at `BACKLOG.md`. Six edits, each matched exactly once.

**Not yet logged, by design:** G3, the export-grain fix and A3 are built and
verified but held until after the 11 Sep 23:55 run; their entry is written and
lands with them.

---

## 2026-09-11 22:04 CEST — P1 evaluation FROZEN (supplements the G2 entry; do not edit)

Written before GW4 kicks off. Player-level outcome, inclusive boundary and
cost reporting are Boris's changes; the predictor-timing, population and
exclusion rules are what the player-level outcome needs to be unambiguous. Any
amendment goes in a new, timestamped entry committed before **Sat 12 Sep 16:00
CEST**. After kickoff nothing here changes.

**Predictor value — one per player, fixed before GW4.** Minutes share over
GW1–3 = `mins_last4` in the GW3 export ÷ (90 × fixtures the player's team played
in GW1–3). All 20 teams played exactly 3, so the denominator is 270 for
everyone. The GW5-time value is **not** used: its window (GW1–4) contains GW4's
outcome.

**Population.** The `xg` rows for event 4 in `projection_log.csv` as they stand
at the GW4 deadline (Sat 12 Sep 14:30 CEST), one row per `player_id`. A player
is dropped if his team did not play in both GW4 and GW5 (blank or postponement)
— he did not have two chances to blank. Currently 256; final after the last
pre-deadline recording.

**Flag.** Minutes share **≤ 0.667, inclusive** — with a 270-minute
denominator, **≤ 180 minutes**. 180 is the most common total after 270 (started
two of three, or 60 minutes in all three); the inclusive boundary puts 9
players in the flagged group. Currently 84 flagged, 172 not.

**Primary outcome.** Blanked in at least one of GW4 or GW5: 0 minutes in a
gameweek his team played. One row per player.

**Pass criterion.** Blank rate (flagged) − blank rate (unflagged), 95% interval
from `_gap_ci()`. Passes only if the lower bound is above zero. Anything else
is *unproven*, not *disproven*.

**Reported alongside — not part of the pass criterion:**
1. The full 2×2 table (flagged / unflagged × blanked / not), so every rate can
   be recovered from it.
2. The cost of excluding on the flag (BACKLOG Part 3 D1). Of the flagged players:
   - the share who did **not** blank — featured in both GW4 and GW5;
   - the share who played **every available minute** — 90 in every fixture of
     GW4 and GW5.
3. Of all players who did not blank, the share who were flagged — the good
   players the screen throws away, as a fraction of all good players.
4. Secondary, labelled **optimistic**: the pooled player-gameweek version (two
   rows per player). Each player counts twice and blanking is correlated
   within a player, so its interval is too narrow.

**Known residual optimism.** Players on the same team share rotation shocks
(a manager rotating after a European week), so even one row per player is not
fully independent. Noted, not corrected.

**Power at the current group sizes (84 / 172).** Blank rates 35% vs 7% → gap
+0.28 ± 0.11, clears. 25% vs 10% → +0.15 ± 0.10, clears. 20% vs 12% → +0.08 ±
0.10, **spans zero**. The test can detect a large separation, not a modest one.
