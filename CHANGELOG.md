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

---

## 2026-09-11 22:30 CEST — P1 evaluation code FROZEN: `p1_eval.py` (amends the 22:04 entry; do not edit)

The 22:04 entry fixed the rules in prose. This fixes how they are read, in code,
before GW4 kicks off, so no edge case is decided after its effect on the answer
is visible. Run once, on the first export after GW5 has finished:
`python p1_eval.py fpl_export_gw3.json fpl_export_gw5.json`.

**Pinned readings — each one a place where a plausible choice changes the number:**

- **A missing row is never read on its own.** Whether a player's team played is
  read from finished fixtures. No row + team played = blank. Team had no
  finished fixture = player dropped, with the reason. The same missing row means
  opposite things in the two cases.
- **An undefined predictor is dropped, never read as zero.** No GW1–3 minutes,
  or absent from the GW3 export → dropped and counted. (Cannot occur for this
  population: `xg` recording already requires 45+ GW1–3 minutes. Real run: 256
  players, 0 undefined, 84 flagged, 172 not.)
- **The predictor comes from the GW3 export only.** Handing it any other export
  raises.
- **The team is the one at forecast time.** A player whose club differs between
  the two exports is dropped.
- **The post export must be GW5–GW9 and carry `player_id`.** GW4 falls out of the
  six-week window after GW9, and web_names are not unique; both are refused
  rather than guessed.
- **Interval: Newcombe's hybrid score (1998, method 10), not the normal
  approximation.** `_gap_ci` was written for mean points; on proportions it
  collapses to 0 ± 0 when a cell is empty. Newcombe reproduces the published
  example (56/70 vs 48/80 → 0.0524 .. 0.3339) and stays wide on empty cells. The
  raw 2×2 counts are always printed, with a warning when any cell is under 5.
- **Three verdicts, not two.** Lower bound above zero → **PASS**. Upper bound
  below zero → **FAIL — inverted**: the screen points the wrong way.
  Otherwise → **UNPROVEN, not disproven.**

**Power caveat, written into the verdict** — corrected from the "roughly 20
points" proposed in review. At 84 flagged / 172 unflagged, 80% power needs a gap
of **13–16 points** (unflagged blank rate 5–15%), and a **10-point gap is about a
coin flip** (50% power at 8–11 points). A failure is consistent with a real
effect of moderate size.

**Cost reported alongside, both readings:** flagged players who did not blank,
and flagged players who played every available minute. The first counts the
nailed 60-minute substitute; the second hides him.

**Verified:** 10 tests (`P1Evaluation`); 10 mutations — Wald interval, a
missing fixture read as a blank, no minutes read as zero, an exclusive boundary,
predictor read from the post export, id-less export accepted, cost counting
only full-minute players, thin-cell warning suppressed, caveat dropped, inverted
result reported as unproven — each red. Suite 78 → 88.

---

## 2026-09-12 — after the last GW4 recording: G3, export grain, A3

Held back until the 11 Sep 23:55 run had recorded GW4, so nothing on the
recording or sync path changed before it. Built and verified in a sandbox
beforehand; the files applied are byte-identical to the verified copies.

**G3 — `own` branch skips blanks and sums doubles**, matching `xg`. Tests at a
simulated GW18 (the fixture's date helper now builds real dates for any
gameweek — at GW18 it used to emit the 33rd of September). Mutation (old code
restored): both tests red. Single-fixture output unchanged: GW4 regenerated
with the patched code, 527/527 rows identical to what the 23:55 run recorded,
so the frozen GW4 forecasts are untouched.

The run that this waited for: 11 Sep 23:55:11–23:55:21, gate open (88 tests),
**272 `own` and 255 `xg` forecasts, 14h34m before the deadline** — the last
automated recording before it, since Saturday's 23:55 run falls after the 14:30
deadline and the guard will refuse. Frozen P1 population: 255 players, 84
flagged, 171 unflagged, 0 undefined.

**Export grain — one `player_gw_recent` row per player per gameweek, carrying
`player_id`.** `player_gw` holds a gameweek *total*; the fixtures join fanned a
double out into two copies of it (12 points graded as 24), and names are not
unique (17 shared). Now `GROUP BY g.player_id, g.event`, plus `n_fixtures`;
per-match columns are NULL when there is more than one match, because a
gameweek total cannot be attributed to one of two fixtures. Test: synthetic
double → one row, 12 points, `fdr` NULL. Mutation (GROUP BY removed): red.
Checked against a copy of the real `fpl.sqlite`: 929 rows before and after,
identical apart from the two new columns, no other export section changed.
Grading switches to ids automatically; on GW3 the backtest population goes
224 → 225 (one same-name pair had been merged).

**A3 — log naming.** `fpl_run.bat` stamps by the **UTC** date — the date
`price_history` uses — so a catch-up after local midnight is filed under the
day whose price sample it wrote; and the header appends instead of truncating.
Verified: two runs on one date leave two headers in one log; the stamp
expression yields UTC (hour 19 at 21:xx CEST); a simulated 01:56 CEST run on
11 Sep stamps 2026-09-10. The 01:56 catch-up log was copied to
`reports/run_2026-09-10.log` before the 23:55 run overwrote it under the old
scheme.

---

## 2026-09-14 — HISTORICAL_VALIDATION Step 1: dataset verified (no model code written)

Source: `github.com/vaastav/Fantasy-Premier-League`, season 2025/26. Downloaded
to `historical/2025-26/` — kept out of `fpl.sqlite` and out of git (regenerable,
~6.5 MB): `merged_gw.csv` (5.4 MB), `fixtures.csv`, `teams.csv`,
`cleaned_players.csv`. 29,757 rows, GW1–38, 841 players.

**Required fields — all present and populated** (share of player-gameweeks with
minutes that are non-zero, by position):

| field | GK | DEF | MID | FWD |
|---|---|---|---|---|
| `expected_goals` | 0% | 35% | 56% | 68% |
| `expected_assists` | 11% | 69% | 80% | 58% |
| `defensive_contribution` | 0% | 93% | 92% | 82% |
| `starts` | 99% | 81% | 67% | 58% |

Zero blanks or unparsable values in any of them. The position pattern is what it
should be: no xG for keepers, no DEFCON for keepers. The file also carries
`tackles`, `recoveries` and `clearances_blocks_interceptions` — the DEFCON
components — which would allow recomputing it under 2026/27 rules later.

Opponent and venue are per player-gameweek (`opponent_team`, `was_home`).
Fixture difficulty is not in `merged_gw.csv` but joins from `fixtures.csv`
(`team_h_difficulty` / `team_a_difficulty`, 380 fixtures): **0 of 11,498
player-gameweeks fail to resolve their fixture id.**

**Reconciliation against an independent source.** Per-gameweek CSV totals summed
per player and compared with the FPL API's own 2025/26 season totals, held in
`player_history` in `fpl.sqlite` — data that never passed through this repo.
432 of 841 CSV players appear there (the rest have left the game; that limits the
cross-check sample, not the study, which uses CSV ids throughout).

- five highest-minute players (Petrović, Virgil, Leno, Pickford, Verbruggen):
  exact on minutes, points, goals, assists, starts
- five highest-scoring attackers (Haaland 239, B.Fernandes 235, Semenyo 202,
  Gibbs-White 188, Rice 184): exact on all five fields
- whole overlap: **431 of 432 exact**

**One defect found, quantified, and fixed by rule — not by substitution.**
`merged_gw.csv` contains **10 surplus rows**: byte-identical duplicates of the
same (element, fixture), affecting **2 players** across GW1–9 (nine of them
Junior Kroupi, element 100). They inflated his totals to 1826 min / 140 pts
against the API's 1663 / 113. De-duplicating on (element, fixture) removes
exactly those 10 rows and takes reconciliation to **432 of 432 (100%)**.

The de-duplication rule keeps genuine double gameweeks: same round with a
*different* fixture id is a real second match. The file contains **409 genuine
multi-fixture player-gameweeks** against those 10 duplicates, so the adapter
must distinguish them — the same distinction the live export needed when the
fixtures join fanned one gameweek total into two rows.

**Verdict: the dataset supports the study.** Both halves are possible — the
attacking half transfers to 2026/27 rules, the DEF half is measurable here but
validated against superseded BPS rules, exactly as the plan states.

---

## 2026-09-14 — canonical slice, both adapters, and `measure_reliability()`

One implementation, two callers. `fpl_hist.py` adapts the vaastav CSVs into the
same canonical slice `fpl_edge.py` builds from the live export, then calls the
same measurement functions — so a historical result is a statement about our
code, not about a copy of it. (BUILD_SPEC names these as functions to refactor;
they did not exist, so they were built against the neutral format from the
start rather than retrofitted.)

**Contract.** `CANONICAL_FIELDS` / `CANONICAL_ROW_FIELDS` / player / fixture /
team-match field sets, asserted by `check_canonical()` on every adapter output.
Field sets are compared, not duck-typed: if one adapter emitted
`expected_goals` where the other emits `xg`, the model would read zeros from
that source and report a finding instead of failing.

**Historical adapter owns two source properties**, because they are not
properties of the model: de-duplication on (element, fixture), and collapsing
per-match rows into one row per player-gameweek with `n_fixtures`. The de-dup
is **loud** — it names the count and the players — because a silent de-dup that
began dropping real rows after an upstream change would be invisible. On the
real season it reports: *removed 10 repeated row(s) from 2 player(s) - Junior
Kroupi (element 100) x9, Ben Gannon-Doak (element 391) x1*, and keeps all 409
genuine multi-fixture gameweeks.

**`measure_reliability()`** — odd vs even gameweeks (not first/second, which
would measure trend), per-90 rates, tie-corrected Spearman, Spearman–Brown to
full-sample reliability, interval on every figure. A metric with no variance in
a half is reported **undefined**, never as a correlation of zero.

**Measured — 2025/26, full season** (`python fpl_hist.py historical/2025-26`,
0.75s over 29,338 player-gameweeks):

| metric | n | r_half | r_full | weight |
|---|---|---|---|---|
| minutes | 841 | 0.978 | 0.989 | 99% |
| xgi | 454 | 0.795 | 0.886 | 89% |
| defcon | 454 | 0.787 | 0.881 | 88% |
| xg | 454 | 0.737 | 0.848 | 85% |
| xa | 454 | 0.679 | 0.809 | 81% |
| bps | 454 | 0.319 | 0.484 | 48% |
| **pts** | 454 | **0.312** | 0.475 | 48% |

Same ordering as BUILD_SPEC §1.2's GW1–4 figures, every value far higher with
38 gameweeks instead of 4 — as expected, and the reason the reliability-by-
window curve (Step 2) is worth having. Points remains the least reliable input
in the game.

**Regression against BUILD_SPEC §1.2**, live GW1–4 export: defcon 0.564 vs
0.569, xgi 0.503 vs 0.479, xa 0.444 vs 0.435, xg 0.479 vs 0.433, bps 0.198 vs
0.227, pts 0.165 vs 0.153 (n 250 vs 242). Within the noise of a re-synced
export and a GW4 that is still partly unplayed.

**One definition is not cosmetic and needs freezing before Friday.** For
`minutes`, "the whole population" is ambiguous, and the two readings differ:

| population | n | r_half | r_full | weight |
|---|---|---|---|---|
| appeared at least once (default) | 405 | 0.777 | 0.874 | 87% |
| every player in the game | 658 | 0.873 | 0.932 | 93% |
| BUILD_SPEC §1.2 quoted | 399 | 0.784 | 0.879 | 88% |

The quoted baseline is reproduced by "appeared at least once", so that is the
default; `population="all"` is available and explicit. Including the ~253
players who never feature adds a block of identical zeros that agrees perfectly
with itself. Either way, a player who featured in one half and not the other is
counted as zero in the half he missed — that part is not in question.

**Noted, not done — recomputing DEFCON under 2026/27 rules.** `merged_gw.csv`
carries `tackles`, `recoveries` and `clearances_blocks_interceptions`
separately, so DEFCON could be rebuilt under current rules instead of taken
from the 2025/26 column. Worth doing *if* the historical run shows DEF failing:
as it stands we could not tell whether that was the rule change or the model,
and recomputing would separate them — and might partly rescue the defensive
half that HISTORICAL_VALIDATION writes off as untransferable.

**Also noted:** the interval `± 1.96 / sqrt(n-1)` is unbounded, so a very high
correlation prints an upper bound above 1 (minutes, full season: 0.910 .. 1.045).
The formula is as specified; the artifact is cosmetic.

**Verified:** 12 new tests; 11 mutations — de-dup on the wrong key, silent
de-dup, an adapter renaming a field, a double gameweek collapsed, the contract
not checking rows, an export without ids accepted, a first/second-half split,
minutes measured per 90, no constant guard, the population silently widened, no
Spearman–Brown step — each red. Suite 91 → 103. The GW5 forecast log is
untouched: regenerated 541/541 identical.

---

## 2026-09-14 — the `minutes` baseline (BUILD_SPEC step 4): P(start) alone, the bar

`--record --source minutes` logs P(start) and nothing else, alongside `own` and
`xg`. `fpl_run.bat` records all three, so GW5 will carry the baseline the model
has to beat.

**P(start) extracted, not duplicated.** `start_probability(p, gws_played)` now
holds the rule that was inline in `project_xg`: `starts_last4` over a window
capped at 4, `is None` rather than `or`, scaled by `chance_next_round`. Both the
model and the baseline call it, so the bar cannot drift from the model's own
notion of starting. The mutation that uncaps the denominator turns the existing
`project_xg` tests red, which is the evidence that it is genuinely shared rather
than copied.

Blank gameweek → no row, double gameweek → counted twice, exactly like the other
sources, so the four columns stay comparable.

**Behaviour on the recording path is unchanged**, which is the thing that
mattered here: `own` and `xg` regenerated from the GW4 export with the extracted
function give **541 of 541 rows identical** to what the 13 Sep run logged.

**The baseline on real GW5 data:** 259 players, values 0.25 to 1.0 (a
four-gameweek window gives quarters), 126 of them nailed at 1.0. That flat top
is exactly why it is a hard bar to beat on rank correlation and why BUILD_SPEC
§3.2's second verdict — 60+ minute players only — is reported separately.

**Verified:** 6 new tests; 6 mutations — a baseline carrying more than P(start),
ignoring a blank, ignoring a double, an uncapped denominator, `or` instead of
`is None`, and injury doubt dropped — each red. Suite 103 → 108, and the gate
passes under the batch environment.

---

## 2026-09-14 — Step 2: reliability as a function of training window (2025/26)

`python fpl_hist.py historical/2025-26 --windows 4,8,12,20,38`. Odd vs even
gameweeks within each window, tie-corrected Spearman, `population="appeared"`
for minutes. r_half, with n in brackets:

| metric | GW4 | GW8 | GW12 | GW20 | GW38 |
|---|---|---|---|---|---|
| minutes | 0.760 (402) | 0.895 (436) | 0.938 (452) | 0.961 (485) | 0.970 (537) |
| xgi | 0.536 (250) | 0.621 (335) | 0.662 (365) | 0.722 (409) | 0.795 (454) |
| defcon | 0.511 (250) | 0.582 (335) | 0.622 (365) | 0.739 (409) | 0.787 (454) |
| xg | 0.393 | 0.539 | 0.627 | 0.703 | 0.737 |
| xa | 0.451 | 0.533 | 0.560 | 0.616 | 0.679 |
| bps | 0.033 | 0.081 | 0.203 | 0.269 | 0.319 |
| pts | 0.041 | 0.120 | 0.184 | 0.238 | 0.312 |

**What it says.** `minutes` is usable from the first window (0.76 at GW4) and
near its ceiling by GW8 (0.895). The attacking inputs and DEFCON sit at 0.51–0.54
on four gameweeks — this season's GW1–4 figures of 0.50–0.56 are right on that
curve — and reach ~0.62 by GW8 and ~0.66–0.72 by GW12–20. **Points and BPS are
indistinguishable from zero on four gameweeks** (GW4 intervals −0.08..0.17 and
−0.09..0.16); points does not clear zero until GW8 and never passes 0.32. This
is the reliability side only; when the *model* becomes usable is Step 3's
question, since a reliable input still has to beat `minutes` on outcomes.

**Correction to the entry above ("canonical slice…"):** its full-season table
gives minutes 0.978 on n=841. That was computed before `population` became a
parameter, i.e. over every player in the game. Under the default that
reproduces the BUILD_SPEC baseline — appeared at least once — the full-season
figure is **0.970 on n=537**. The other six rows are unaffected (they are per-90
and already gated on minutes in both halves). Both readings are now recorded;
neither changes the ordering or any conclusion.

---

## 2026-09-14 — `project_reliability()` built (BUILD_SPEC §2); `bottomup` FROZEN for GW5

**Frozen definition — do not edit; amendments go in a new timestamped entry
committed before Fri 18 Sep 19:30 CEST.** `bottomup` is `project_reliability()`
as committed in this change, on the canonical slice built from the live export:

- `xP = 2·P(start) + xGI·0.62·GOAL_VALUE[pos]·P(start) + xGI·0.38·3·P(start)
  + P(cs)·CS_VALUE[pos]·P(start) + 2·P(DEFCON≥thr)·P(start)`
- P(start): `start_probability()` — the same function `project_xg` and the
  `minutes` baseline use.
- xGI and DEFCON per-90 rates from the canonical rows, **shrunk toward the
  positional median (180+ min) by the measured `r_full`** from
  `measure_reliability()` on the same slice — computed at recording time, never
  hardcoded. The GW1–4 export gives weights xgi 0.67, defcon 0.72.
- Clean sheet: Poisson, `λ = team GC/match × (opponent xG/match ÷ league mean)`,
  `P = e^−λ`, from measured team rates only. DEFCON: logistic on the threshold
  (10 DEF, 12 MID; none for GK/FWD), scale 2.
- No fixture → no row. Double → summed. Population: status `a`, 45+ minutes in
  the last four, as for every other source.
- Known limitation, stated up front: the live export carries the last six
  gameweeks of rows, so live weights and rates come from that window. Harmless
  through GW6; the export window should widen before GW7.

Verified: 16 tests; 14 behavioural mutations each red (blank forecast, double
not summed, flat goal value, clean sheet ignoring the opponent, no shrinkage,
DEFCON threshold ignored, DEFCON for GK/FWD, points leaking into xGI, ablation
stage 0 carrying xGI, backtest training on the target week, benched players
dropped, source logging `project_xg`, interval uncapped) plus one two-site
mutation (position guard *and* `CS_VALUE` removed together → forwards get a
clean sheet → red; each site alone is a no-op by defence in depth). Recording
path unchanged: `own`/`xg` regenerated 541/541 identical. Live GW5 forecast:
259 players, xP 0.63–7.60, mean 3.00. Suite 108 → 122. **Green on 14 Sep, four
days before Thursday's run; `fpl_run.bat` records all four sources from tonight.**

## 2026-09-14 — HISTORICAL_VALIDATION Steps 3–5 on 2025/26

`python fpl_hist.py historical/2025-26 --backtest`, 3 seconds. Rolling origin
GW5–38, train on everything before; 11,039 player-gameweeks graded, benched as
0. Same functions as the live pipeline (`backtest_week` → `reliability_inputs`
→ `project_reliability`). Full tables in `reports/backtest_2025-26.txt`.

**Verdict 1 — whole population, "who blanks and who scores" — bottomup NEVER
separably beats minutes, at any window, for any position.** Rho with interval,
20–37 GWs of training:

| position | n | minutes | bottomup | points | xgi |
|---|---|---|---|---|---|
| ALL | 5755 | +0.318 (0.293..0.344) | +0.318 (0.293..0.344) | +0.087 | +0.080 |
| GK | 425 | +0.416 | +0.393 | +0.164 | +0.155 |
| DEF | 2137 | +0.312 | +0.334 | +0.094 | +0.086 |
| MID | 2530 | +0.319 | +0.334 | +0.071 | +0.085 |
| FWD | 663 | +0.346 | +0.347 | −0.012 | −0.004 |

The pattern holds at 4–7, 8–11 and 12–19 GWs. **There is no crossover** in the
sense the plan asked for: bottomup's lower bound never clears minutes' point
estimate. DEF and MID sit ~0.02 above, GK ~0.02 below, FWD level — all inside
the intervals. On this question the model adds nothing over "will he play?",
exactly as BUILD_SPEC §3.1 found on one gameweek.

**Verdict 2 — players who featured (60+ min), "how well do the starters do" —
bottomup beats minutes, modestly, and the effect is real.** 20–37 GWs:

| position | n | minutes | bottomup | xgi |
|---|---|---|---|---|
| ALL | 3410 | +0.049 (0.016..0.083) | **+0.106 (0.073..0.140)** | +0.111 |
| GK | 326 | +0.046 | +0.099 | +0.036 |
| DEF | 1311 | +0.074 (0.020..0.128) | **+0.154 (0.100..0.209)** | +0.029 |
| MID | 1414 | +0.051 | +0.095 | +0.097 |
| FWD | 359 | +0.074 | +0.110 | +0.119 |

Here `minutes` is near zero by construction (everyone featured) and the model
carries real signal: DEF +0.154 with an interval clear of zero from **8–11 GWs
onward** (+0.174 there), ALL +0.106 clear of minutes' point from 8–11 on. But
rho ≈ 0.10–0.15 is far below +0.20. For MID and FWD, bare `xgi` does as well as
the whole model.

**MAE, 20–37 GWs** (constant predictor in brackets): ALL bottomup 2.16 =
minutes 2.16 (2.25); GK 2.01 < 2.16; MID 2.03 < 2.13; FWD 2.16 < 2.40; **DEF
2.34 ≈ constant 2.35, worse than minutes 2.12.** The DEF rank is fine and its
level is wrong: the projections are too spread — most likely the clean-sheet
term (up to 4 × P(cs)) over-contributing. Under 2025/26 rules, so this is the
model's calibration, not the rule change.

**Ablation** — `p_start` alone reproduces the `minutes` column exactly at every
window and position (an internal consistency check that passed). Whole
population: no term moves rho beyond ±0.02 — decoration for that question.
Featured players, 20–37 GWs: the **clean-sheet term** lifts DEF +0.079 →
+0.136 and GK +0.027 → +0.099 and moves FWD by exactly 0.000; the **xGI term**
lifts FWD +0.074 → +0.110 and MID +0.051 → +0.081 and *hurts* GK (+0.046 →
+0.027, keeper xGI is noise); **DEFCON** adds DEF +0.136 → +0.154 and MID
+0.087 → +0.095. Every term behaves as the theory says it should, and every one
earns its place on the starters question only.

**Two seasons agree.** 2025/26 GW4–7 whole-population: minutes +0.332,
bottomup +0.335. This season GW1-3 → GW4 (BUILD_SPEC §3.1): minutes +0.359,
prototype +0.338. The harness reproduces this season's headline on last
season's data.

**Reading, per §6:** on the blank question, "never beats minutes at any
window" — use `minutes` for exclusion and stop expecting a model to do better.
On the starters question, "mixed by position": a real but small edge, largest
for DEF via the clean-sheet term, matched by bare xGI for MID/FWD. That is what
BUILD_SPEC §3.2 anticipated when it asked for the two verdicts separately, and
they diverge. Whether +0.10–0.15 among starters is worth acting on — for
captaincy and transfers, where the blank question is already settled — is a
decision, and it is recorded here before GW5 is graded.

**Interval cap.** `reliability_table` now prints intervals clipped to ±1.0; the
normal approximation is unbounded, a correlation is not.

**Harness validated on a second season — six of seven, not seven.** This
season's GW1–4 r_half against 2025/26's GW4 intervals: minutes 0.777 in
0.663..0.858 ✓, xgi 0.503 in 0.412..0.660 ✓, defcon 0.564 in 0.387..0.635 ✓,
xg 0.479 in 0.269..0.517 ✓, xa 0.444 in 0.327..0.575 ✓, pts 0.165 in
−0.083..0.165 ✓ (on the boundary). **bps 0.198 is outside −0.091..0.157.** Six
inside is what independent seasons should give at 95%; the BPS miss is the one
to watch, given the 2026/27 BPS rule changes are exactly the thing
HISTORICAL_VALIDATION says will not transfer.

---

## 2026-09-14 — the ceiling on the starters question, measured (before GW5 is graded)

The "+0.20 may be the wrong bar for the starters question" idea can be a
number. How well does one week's points predict the next week's, among players
who featured (60+ min) in both? That is the test-retest reliability of the
outcome itself, and no predictor can correlate with an outcome better than the
square root of its reliability.

- **Direct:** adjacent-week Spearman of points among starters, 2025/26, pooled
  over 37 week-pairs, n=5,839: **+0.023** (95% CI ±0.026 — spans zero).
  Weekly values −0.19 .. +0.26, median +0.02. **Ceiling ≈ √0.023 = 0.15.**
- **Independent cross-check:** the recorded full-season `r_half(pts)` = 0.312 is
  the reliability of a ~19-gameweek aggregate; Spearman–Brown reversed to one
  gameweek gives **0.023 — ceiling 0.153.** Two methods, same answer.
- For contrast, whole population (blanks as 0): adjacent-week rho +0.206,
  ceiling ≈ 0.45. `minutes` reaches +0.33 of that.

**Reading.** Among starters, bottomup at +0.106 (ALL) and +0.154 (DEF) is at
the ceiling, not short of it. +0.20 was unattainable for single-week points
from stable player quality, and was set with the whole-population test in
mind, where P(start) supplies most of the correlation for free. Caveat: the
adjacent-week ceiling bounds predictors of *stable* quality; week-specific
information (fixture, team news) could in principle exceed it. bottomup is
fixture-aware and still lands at the ceiling, and the ablation shows the
fixture-dependent term adds ~0.02–0.06 — so whatever headroom exists above
0.15 is small and lives in information the export does not carry.

This is recorded as a measured bound, not as a revision of the bar after
seeing the result. Whether it becomes the bar is a decision for after GW5.

**Verified today, for the record:** the hindsight-optimisation figures quoted
in the strategy chat (2019/20: ghost ship 2,446, lineup-only 3,236, free
transfers 3,945, unlimited 4,984 with 145 hits; ghost ship rank 386; De Bruyne
captained every week 502; Bull 2,557) all match the source,
alpscode.com/blog/hindsight-optimization.

---

## 2026-09-14 16:10 CEST — wildcard decision rule FROZEN (as amended), before GW5 is graded

Approved by Boris with one amendment (the last clause). Do not edit; changes go
in a new timestamped entry.

**Three layers, in order. A later layer never overrides an earlier one.**

1. **Exclude on P(start).** The frozen threshold: minutes share ≤ 0.667 over the
   last `min(4, gws_played)` gameweeks is out. Fully validated — 0.76–0.86
   reliability at four gameweeks, and no model beats it on the blank question at
   any window. The hard filter; nobody below it is considered.
2. **Shortlist by role.** Set-piece order (`pens_order`, `corners_order`,
   `fk_order`), position arbitrage, DEFCON hit rate. Rules-level edges that need
   no model. Where Groß and De Cuyper come from.
3. **Order within position** — `bottomup` for DEF (the clean-sheet term is what
   carries it, +0.154 among starters), **bare xGI for MID and FWD** (the
   ablation shows the rest of the model adds nothing there). A +0.10–0.15 edge,
   at the measured ceiling of ~0.15, is a tiebreaker between players who pass
   layers 1 and 2. It is not a reason to override a role-based one.

**Amendment — cross-position budget by quota, not by global value-per-million,
until DEF calibration is fixed.** `_build_squad` today ranks by `proj / price`
and hill-climbs on `proj` across the whole squad, trading a defender against a
midfielder for the same money. DEF projections are correctly ordered but
over-spread (MAE 2.34 vs `minutes` 2.12, ≈ the constant predictor), so a
global comparison would over-buy defenders. Until P(clean sheet) is shrunk
toward the league base rate — not before GW5, and not tuned on 2025/26 —
allocate the 2-5-5-3 quota per position and fill each position from its own
ordered shortlist.

**GW6 work, in this order. None of it before Friday 18 Sep 19:30 CEST.**

1. Rewire `sec_wildcard` to the three layers as above.
2. Horizon projection over GW7–12: `project_reliability()` already takes a
   fixture list, so the six-week sum with per-opponent clean sheets is a call
   with the right list — no model change.
3. Bench Boost screen for GW8: nailed starters with high floors, P(start)-driven.
4. Widen the export's per-gameweek window past six gameweeks (one SQL line in
   `fpl_sync.py`) so live weights and rates use the whole season by GW7+.
5. Effective ownership with captaincy in the mini-league layer — the part that
   decides a seven-man league and the part no public tool does.

GW5 freezes tonight with four sources (`own`, `xg`, `minutes`, `bottomup`). The
two live rows after GW5 settles are the check on whether the 2025/26 result
transfers under this season's rules; given BPS did not, that is not a formality.

---

## 2026-09-14 18:20 CEST — schedule decisions to 23 Oct, and the horizon test PRE-REGISTERED

Accepted by Boris; docs only, the GW5 freeze holds.

- **MILP / PuLP removed** from the international-break work. Optimal XI and
  captain from a fixed 15 is already solved exactly by `_best_xi` (every legal
  formation enumerated; additive objective). For squad selection, an MILP
  objective maximises projected points *across* positions — the comparison the
  16:10 amendment forbids until DEF calibration is fixed — and it breaks the
  standard-library rule. If an exact 15-picker is ever wanted, calibration
  comes first and the rule change is recorded deliberately.
- **GW5 grading and the P1 evaluation run Tuesday 22 Sep**, after Monday's
  23:55 sync, not Monday morning: last kickoff is Sun 20 Sep 17:30 and this
  API's `finished` flag lags. `p1_eval`'s dropped count is the tell if it has
  not flipped.
- **Log checks Tue 15 Sep morning** (first four-source run) **and Fri 18 Sep
  morning** (Thursday's 23:55 is the last automated recording before the
  19:30 deadline; Friday morning is the last chance to record by hand).
- **`fpl.sqlite` backup** — one copy line in `fpl_run.bat` on Mon 21 Sep.
- **DEF calibration has no date by design.** The wildcard is built on the quota
  rule. Revisit around GW10 on 2026/27 data; not tuned on 2025/26.

**Horizon test — definition frozen before it is run** (scheduled Tue 22–Fri
25 Sep; fallback hard deadline Thu 8 Oct, after which the GW6 draft uses
single-week projections and the test is logged pending).

For H in {1, 2, 4, 6, 8, 12}, on 2025/26 with the rolling-origin harness:
train on GW1..t−1; predict the **sum of points over GW t..t+H−1** with the
**sum of per-fixture `bottomup` projections** over the same gameweeks, fixture
pairings taken as known in advance and results not; `minutes-H` = P(start)
times the number of fixtures in the horizon. Whole population with blanks as
0, per position, tie-corrected Spearman with intervals, pooled by training
window as in Steps 3–5. A player is in the population if he passes the usual
gate at t and his team has at least one fixture in the horizon. No fitted
parameters, so a retrospective run is legitimate given this definition was
fixed first. The question it answers: whether the wildcard should be drafted on
a multi-week sum or on single-week projections — and whether that changes the
answer to "bottomup vs minutes".

---

## 2026-09-16 — GW4 graded on the SETTLED export: the first live calibration row

Graded from `fpl_export_gw4.json` as written by the 15 Sep 23:55 CEST sync
(21:55 UTC), after GW4 lockdown — the DB shows the event `finished = 1` and
10/10 fixtures finished. Against the frozen GW4 rows of `projection_log.csv`
(272 `own`, 255 `xg`, recorded 11 Sep 23:55). Benched-but-team-played graded
as 0; no GW4 blanks. Starters = 60+ minutes in GW4. Reproducible with the
repo's own `grade_forecasts` / `_spearman`.

| source | n | whole rho (95%) | starters rho (n) | MAE vs const | bias |
|---|---|---|---|---|---|
| own | 272 | **+0.342** (+0.223..+0.461) | +0.219 (187) | 2.40 vs 2.54 **PASS** | +0.07 |
| xg | 255 | +0.254 (+0.131..+0.377) | +0.108 (185) | 2.74 vs 2.62 **FAIL** | +0.57 |
| minutes* | 272 | +0.282 (+0.163..+0.401) | +0.016 (187) | 2.51 vs 2.54 PASS | −2.20 |

\* retrospective — P(start) from the GW3 export, as `--source minutes` would
have written it. Not in the point-in-time log (the source did not exist on 11
Sep); its bias is meaningless because it is a probability, not points.

**Reading.** One week; the 2025/26 backtest shows single-week rho swinging
±0.1 around its mean, so nothing here is a verdict. `own` passes the constant
bar this week and out-ranks `xg` on both questions; `xg` fails, over-forecasting
by half a point per player. The retrospective `minutes` reproduces last
season's pattern exactly — +0.28 on the whole population, nothing among
starters — and `own` sits above it this week, inside the interval.

**Figures supplied from the strategy chat differ and are not recorded.** They
gave own +0.341 / +0.206, MAE 2.39 vs 2.53, bias +0.03; xg +0.265 / +0.099,
2.72 vs 2.62, +0.52; minutes +0.295 — same n, same verdicts, every value off at
the second decimal. That computation ran outside this repo on an uploaded file
and cannot be reproduced here; a different snapshot of GW4 actuals or a
different starters/blank rule would do it. The claim that the provisional
(14 Sep) and settled grades were identical to three decimals **cannot be
checked**: the 14 Sep export was overwritten by the nightly sync. Exports are
regenerated in place and gitignored — from Mon 21 Sep, keep a dated copy of
each night's export alongside the `fpl.sqlite` backup (≈1.3 MB/day).

**Rule, as stated and now applied:** provisional grades are never recorded.
This entry exists because lockdown had passed.

## 2026-09-16 — the `finished` flag: measured bracket, stated rule, grading rule

**Stated (Boris):** a 2026/27 rule change — `finished` flips at gameweek
lockdown, 09:00 UK the day after the last kickoff.

**Measured on GW4:** last final whistle ≈ Mon 14 Sep 21:00 UTC. `finished = 0`
on all 10 fixtures and the event at the Mon 21:55 UTC sync. `finished = 1`,
`data_checked = 1`, 10/10 fixtures at a direct API read Tue 15 Sep 18:40 UTC.
So the flip is bracketed **Mon 21:55 – Tue 18:40 UTC** — consistent with 09:00
UK, not pinned to it. Pin it on GW5 with two API reads on Mon 21 Sep, before
and after 09:00 UK.

**Grading rule:** grade after the sync that follows lockdown, never before.
GW5: last kickoff Sun 20 Sep 17:30 CEST → lockdown Mon 21 Sep 09:00 UK →
Monday's 23:55 sync carries it → **grade Tuesday 22 Sep.**

**Guard — scheduled Mon 21 Sep, with the post-freeze grading changes.** The
export gains an `events` section (id, finished, data_checked); `sec_calibration`
and `p1_eval` refuse to grade an event that is not `data_checked` and say why.
`data_checked` rather than `finished`: it is the API's "points and bonus are
final" flag. Not before Friday: `fpl_edge.py` is imported by the recording path,
and a broken edit trips the test gate and skips Thursday's last pre-deadline
recording. Turning the timing rule into code has to wait for the freeze to
lift; it must be in place before Tuesday's grading, and Monday is in time.

---

## 2026-09-16 — Monday 21 Sep work, pre-specified (nothing touches `fpl_edge.py` or `fpl_run.bat` before Fri 18 Sep 19:30)

Order: 1–4 (grading correctness), then 5, 6. All before the Tuesday 22 Sep grading.

1. **Calibration guard.** `fpl_sync.py`: migrate `events` to carry
   `data_checked` (from bootstrap `events[].data_checked`), and export an
   `events` section — `id`, `finished`, `data_checked` per gameweek.
   `sec_calibration` and `p1_eval` refuse to grade any gameweek whose events
   row lacks `data_checked = 1`, and print why. Keyed on `data_checked`, not
   `finished`: the first means points and bonus are final, the second only
   that the match ended. Tests: a gameweek with `data_checked = 0` is refused
   with the reason printed; mutation (guard keyed on `finished`) red.
2. **Print the definitions.** Calibration output states on the page: starters
   threshold (60+ minutes); blank rule (logged player whose team played and has
   no row = 0; team did not play = excluded); population count per source.
   Two computations disagreed on GW4 and neither had its rules written down.
3. **Dated exports.** The nightly run keeps each export as
   `archive/fpl_export_gwN_YYYY-MM-DD.json` (UTC date, same `%STAMP%` as the
   log) instead of only overwriting in place. Point-in-time inputs, same reason
   as point-in-time forecasts. `archive/` gitignored. The working-folder
   `fpl_export_gwN.json` stays as is, so `newest_export()` / `previous_export()`
   are unaffected — they glob the working folder only.
4. **Backup.** `copy fpl.sqlite archive\fpl_YYYY-MM-DD.sqlite` each night, after
   the sync. Price history cannot be regenerated; three unattended weeks follow.
5. **Drive sync.** After the report step, copy the current export,
   `projection_log.csv` and the night's run log to `<Drive>\FPL\`. Log the copy
   result; a failed copy is not fatal but must be visible. Never sync
   `fpl.sqlite`. Copying keeps the working files out of the sync client's
   reach — `record_projections` rewrites `projection_log.csv` whole, and a
   client touching the working file mid-write is the risk being avoided.
   **Blocker found 16 Sep: Google Drive for desktop is not installed on this
   machine** — no `%LOCALAPPDATA%\Google\DriveFS`, no `Google Drive` / `My
   Drive` folder on any letter, no `GoogleDriveFS.exe`. Install it (or name
   another sync folder) before Monday, or item 5 slips.
6. **Pin the lockdown.** Two direct API reads Mon 21 Sep, before and after
   09:00 UK; record `finished` and `data_checked` from each. Turns the stated
   rule into a measured one.
7. **GW4 discrepancy** — once Drive sync is live, Boris diffs his GW4
   computation against `sec_calibration` player by player on the same export.
   Until then the repo's row stands. Likely cause: actuals snapshot or a
   boundary player, not the ranker — bias moved, n did not.

**Addendum to item 5 (Boris, 16 Sep):** the same reasoning as item 3 applies
to the Drive sync — the synced folder must be **outside the working
directory**, or `newest_export()` / `previous_export()` glob
`fpl_export_gw*.json` and pick up the synced copy. Copy *to* the Drive folder;
never point the sync client at `Documents\FPL`. Google Drive for desktop was
installed on 16 Sep but had not mounted yet at 14:20 (no process, no DriveFS
config, no `My Drive` on any letter) — it needs sign-in; the mounted path is
recorded here once it appears, and item 5 uses `<that path>\FPL\`.

**Item 5 target, recorded 16 Sep 14:10:** Google Drive for desktop 130.0.2.0,
signed in, streaming mount **`G:\My Drive`**, no folders synced *from* the
machine (setup step skipped, per the addendum). Target folder created and
proven writable: **`G:\My Drive\FPL\`**. The batch copies the current export,
`projection_log.csv` and the night's run log there after the report step;
`fpl.sqlite` never.

---

## 2026-09-21 — run audit 17–20 Sep; the Excel lock; there was no copy step

Quoted from `reports\run_2026-09-1[7-9].log` and `run_2026-09-20.log`:

| run (23:55 CEST) | tests | record step | export |
|---|---|---|---|
| Thu 17 Sep | `Ran 122 tests` / `OK` | `recorded 278 … 'own'`, `256 … 'xg'`, `256 … 'minutes'`, `256 … 'bottomup'` for **GW5**, `19:34:41 before deadline` | gw4 |
| Fri 18 Sep | 122 / OK | 264 / 246 / 246 / 246 for GW6, `21 days, 12:04` before | gw5 |
| Sat 19 Sep | 122 / OK | **4 × `PermissionError: [Errno 13] Permission denied: 'projection_log.csv'`** — then `Done`, task `Last Result: 0` | gw5 |
| Sun 20 Sep | 122 / OK | 282 / 264 / 264 / 264 for GW6, `19 days, 12:04` before | gw5 |

All four ran; GW5 was frozen correctly on Thursday with four sources.

**The Drive folder was never stale because nothing had ever copied to it.**
`fpl_run.bat` contained no copy line on any of those nights (`grep -i copy`:
none; its git history has four commits, none adding one). The four files dated
17 Sep 00:09 in `G:\My Drive\FPL` were a one-off manual copy. The copy step
was item 5 of the Monday plan and is built today.

**Saturday's failure:** Excel (PID 37028) had `projection_log.csv` open from
19 Sep 13:39, which takes an exclusive lock. `open(path, "w")` failed before
truncation, so the log was untouched: 1,573 GW4+GW5 rows byte-identical to the
commit made while the lock was held (`3249c65`). Closed without saving; Sunday's
run was normal. The failure was silent — four tracebacks, exit code 0 — because
the batch does not check `errorlevel` after `--record`. Still open.

## 2026-09-21 — settled-gameweek guard, definitions, archive, backup, shipping (`d5a5edb`)

**Guard.** `gameweek_settled(d, ev)`: gradable only when the event has
`data_checked = 1` **and** every one of its fixtures has `finished = 1`;
`sec_calibration` refuses otherwise and names each blocker. The instruction
asked for per-fixture `data_checked`; the API has no such field — a fixture
carries `finished` / `finished_provisional`, `data_checked` exists on events
only (verified on a live read) — so the rule is event-level points-final plus
fixture-level finished, and nothing was substituted. An export with no flag
sections is refused, not trusted. Live, 09:41 UTC:

    REFUSED GW5 - not settled; grading it now would record provisional points:
      - event data_checked = 0 (points and bonus not final; event finished = 0)

while GW4 grades and reproduces the 16 Sep row exactly (own n=272, 2.40 vs
2.54, +0.342, starters +0.219 n_st 187, bias +0.07; xg n=255, 2.74 vs 2.62,
+0.254, starters +0.108 n_st 185, bias +0.57).

**Definitions printed in the output itself:** n and population, tie-corrected
Spearman, whole vs starters (60+ minutes, with `n_st`), MAE, const, bias, the
blank rule, the settled rule. Calibration gains the starters column, so the
second verdict is no longer computed ad hoc.

**Sync:** `events.data_checked` (migration + bootstrap), export sections
`events` and `fixtures_status` (unfinished fixtures included).

**`fpl_ship.py`**, called by `fpl_run.bat` after the report:
`archive\fpl_export_gwN_<UTC date>.json`, never overwritten by a later day;
`backup\fpl_<date>.sqlite` via the sqlite backup API, last 7 kept; then the
dated export, `projection_log.csv`, the run log and the report to
`G:\My Drive\FPL`. Every copy prints a result line (`SHIP OK` / `HELD` /
`FAILED` / `REFUSED`). Drive unmounted → `outbox\`, delivered at the start of
the next run. The database is refused. A ship failure is logged and non-fatal;
a report failure no longer skips shipping. All three folders sit outside the
`newest_export()` glob.

**Verified:** 16 new tests, suite **122 → 138**; 16 mutations each red (guard
always-true, keyed on `finished`, ignoring fixtures, trusting a flagless
export, definitions removed, starters threshold; sync exporting `finished` as
`data_checked`, hiding unfinished fixtures, bootstrap storing the wrong flag,
missing migration; ship without fallback, without flush, shipping the
database, silent missing file, no pruning, undated archive). Batch wiring run
with stubs in three scenarios. Then the real batch end to end, 09:40:52–
09:41:07 UTC, exit 0: `ARCHIVE OK`, `BACKUP OK`, four `SHIP OK`; files
confirmed in `G:\My Drive\FPL`. Sunday's untouched export and database were
filed first as `archive\fpl_export_gw5_2026-09-20.json` and
`backup\fpl_2026-09-20.sqlite`.

## 2026-09-21 — lockdown: three observations of GW5's flags (no flip time stated)

GW5's last kickoff: Sun 20 Sep 15:30 UTC (FUL v MUN). 09:00 UK = 08:00 UTC.

| | when (UTC) | source | fixtures `finished` | event `finished` | event `data_checked` |
|---|---|---|---|---|---|
| A | Sun 20 Sep 21:55:09 | nightly sync (DB + export, archived) | **0 / 10** — including BRE v CHE, 50 h after full time | 0 | not stored then — **not observed** |
| B | Mon 21 Sep 09:34:22 | direct API read | **10 / 10** (`finished_provisional` 10/10) | False | **False** |
| C | Mon 21 Sep 09:40:54 | fresh sync, new code | 10 / 10 | 0 | **0** |

**What this bounds.** Fixture-level `finished` flipped for all ten matches
somewhere in the 11 h 39 min between A and B. That window contains 09:00 UK
and is consistent with a lockdown then; it does not pin it, and no read was
taken before 09:00 UK today (the session began at 10:32 UK). Event-level
`finished` and `data_checked` had **not** flipped by 09:41 UTC, 1 h 41 min
after 09:00 UK — so they are a later, separate step. For GW4 the event-level
flip lies between Mon 14 Sep 21:55 UTC (0) and Tue 15 Sep 18:40 UTC (1).

**Correction to the 16 Sep entry:** "the `finished` flag flips at lockdown" is
true of fixtures only. The flag that matters for grading is the event's
`data_checked`, and it is not tied to 09:00 UK by anything observed. Tuesday's
grading goes ahead only if Monday's 23:55 sync carries `data_checked = 1` for
GW5; the guard decides, not the calendar.

---

## 2026-09-21 — item 7: the forecast-log write is atomic and retried; a failed record is visible (`4ac8af3`)

**The incident.** Sat 19 Sep 23:55: Excel held `projection_log.csv`; all four
`--record` calls died with `PermissionError`; the batch printed `Done`, exit 0.

**Write.** `write_log_atomic()` writes `projection_log.csv.tmp`, then
`os.replace()`s it over the log. The log is never opened for writing, so it is
always either the old file or the new one. A locked target is retried 3 times,
5 s apart (4 attempts, 15 s). On final failure the `.tmp` is kept — it holds
that run's forecasts with their pre-deadline timestamps — and is gitignored.

**Status.** `record_status()` returns `(ok, n, reason)`. FAIL only when a
forecast should have been written and was not: the deadline is open and no rows
were produced, the projections file is unreadable, or the log stayed locked. A
passed deadline (and an export with no fixtures for the target) is **OK with
n = 0** — it happens after every deadline, and a line that cries wolf nightly
gets ignored. The CLI prints `RECORD OK <source> <n>` / `RECORD FAIL <source>
<reason>`, appends it to `--status`, and exits 1 on failure; an unexpected
exception is caught, its traceback printed, and reported the same way.

**Batch.** Each source goes through `:record`; `errorlevel` is checked after
every call, and a crash that wrote no status line gets one from the batch.
One line per source is summarised after the report and **before shipping**, so
the Drive copy of the run log carries it. A failed record never stops the
report or the shipping. The run then ends `FINISHED WITH ERRORS`, exit 1 —
Task Scheduler's `Last Result` is now a real signal — instead of `Done`, exit 0.
A red test suite writes `RECORD FAIL <source> skipped - test suite is red` for
all four.

**Verified.** 9 new tests, suite **138 → 147**, two of which run the real
`fpl_run.bat` under `cmd.exe` with stub scripts (they add ~3–5 s). The lock
tests hold the file open with a plain handle: on Windows `os.replace()` then
fails with `PermissionError` (winerror 5), which is what Excel produced. 10
mutations, each red — **retry removed** (2 tests), **errorlevel check removed**
(1), non-atomic write, failure exiting 0, no status line, zero rows counted as
OK, passed deadline reported as FAIL, a failed record stopping the run, run
exiting 0 after a failed record, no end-of-run summary. Recording output
unchanged: GW6 regenerated with the new code, 1,074 of 1,074 rows identical.
Saturday reproduced through the real CLI with real waits: three `retry n/3`
lines, 15.1 s, `RECORD FAIL minutes … still locked after 4 attempts`, exit 1,
log hash unchanged, 264 forecasts kept in the `.tmp`. Then the real batch end
to end (12:08 CEST): four `RECORD OK`, `ARCHIVE OK`, `BACKUP OK`, four
`SHIP OK`, `Done`, exit 0.

One environment note: `cmd /c fpl_run.bat` with only a working directory fails
here ("not recognized") — this machine's `cmd` does not search the current
directory — so the batch tests call it by absolute path. Task Scheduler already
does.

## 2026-09-21 — item 8: `CLAUDE.md` (`ff85bc3`); item 9: `p1_eval.py` stays frozen

`CLAUDE.md` is a 38-line index: what the project is, the standing rules
(stdlib only, never fabricate, point-in-time, lockdown guard, model-change
protocol, change protocol) and one line per context file. The other files are
unchanged. `p1_eval.py` is untouched — no settled guard added; it is run only
after `--section calibration` accepts GW5, and `CLAUDE.md` says so.

---

## 2026-09-23 — GW5 graded on the settled export; P1 evaluation run (recorded as printed, no interpretation)

GW5 settled: `data_checked = 1` since the night of Mon 21 Sep. Both commands run by Boris (20:01 / 20:04 CEST) and re-run here (20:15 / 20:16); outputs identical. Export as written by the 22 Sep 23:55 sync.

`python fpl_edge.py --section calibration`:

```
  source      GW     n    MAE  const     rho  starters  n_st   bias   verdict
  bottomup     5   256   2.38   2.49   0.260     0.001   190  -0.22   beats const
  minutes      5   256   2.72   2.49   0.265     0.030   190  -2.50   loses
  own          4   272   2.40   2.54   0.342     0.219   187  +0.07   beats const
  own          5   278   2.22   2.42   0.383     0.101   194  -0.27   beats const
  xg           4   255   2.74   2.62   0.254     0.108   185  +0.57   loses
  xg           5   256   2.45   2.49   0.305     0.086   190  +0.24   beats const

  BOTTOMUP over 1 gameweek(s), 256 forecasts
    MAE 2.377 vs constant 2.492   rho +0.260 +-0.123
    real signal
    2 more gameweek(s) before this is worth acting on.

  MINUTES over 1 gameweek(s), 256 forecasts
    MAE 2.725 vs constant 2.492   rho +0.265 +-0.123
    real signal
    2 more gameweek(s) before this is worth acting on.

  OWN over 2 gameweek(s), 550 forecasts
    MAE 2.308 vs constant 2.483   rho +0.358 +-0.084
    real signal
    1 more gameweek(s) before this is worth acting on.

  XG over 2 gameweek(s), 511 forecasts
    MAE 2.598 vs constant 2.562   rho +0.277 +-0.087
    real signal
    1 more gameweek(s) before this is worth acting on.

  257 forecasts pending for bottomup GW6
  257 forecasts pending for minutes GW6
  275 forecasts pending for own GW6
  257 forecasts pending for xg GW6
```

`python p1_eval.py fpl_export_gw3.json fpl_export_gw5.json` (predictor export generated 2026-09-11T21:55:16Z, the GW3 export the GW4 forecasts were made from):

```
  graded 255 players, dropped 0

  PRIMARY: blanked in at least one of GW4, GW5 - one row per player
                  blanked  did not  total    rate
    flagged            24       60     84     29%
    unflagged          30      141    171     18%
    gap +0.110   95% interval +0.003 .. +0.226  (Newcombe)

  SECONDARY, OPTIMISTIC - pooled player-gameweeks, each player twice:
    gap +0.106   95% interval +0.040 .. +0.179  (too narrow: blanking is correlated within a player)

  COST OF EXCLUDING ON THE FLAG
    flagged who did not blank (featured both weeks)    71%
    flagged who played every available minute           20%
    of all players who did not blank, share flagged     30%

  VERDICT: PASS
```

---

## 2026-09-23 — item 1: a stranded `projection_log.csv.tmp` is promoted before recording (`44c7e6f`)

If a pre-deadline write fails (log locked), the `.tmp` holds the only copy of
that week's frozen forecasts, and the next run — after the deadline,
`RECORD OK 0` — must not overwrite it. `recover_stranded_log()` runs at the
start of every `--record`, **before the deadline check**: a `.tmp` newer than
the log is `os.replace()`d into place with the same 3 × 5 s retry as the write,
`RECOVERED <n> rows from projection_log.csv.tmp` is printed, then recording
proceeds. A clean log prints nothing.

Three cases a literal implementation gets wrong, each pinned by a test and a
mutation:

- **`.tmp` older than the log** → left alone (a later successful write
  superseded it).
- **Unreadable or truncated** — a crash while the `.tmp` was being written
  leaves a half-file that is *newer* than the log → never promoted and never
  deleted: moved aside as `projection_log.csv.tmp.refused-<UTC stamp>`;
  recording continues.
- **Log still locked** → `RECORD FAIL <source> projection_log.csv.tmp holds
  <n> unpromoted rows and the log is locked - close it and re-run`. Writing
  would rebuild the log from the stale copy and overwrite the `.tmp` that
  holds the rows.

**Verified:** 5 tests, suite **147 → 152**; 6 mutations each red — promotion
removed, promoted regardless of age, no validation, locked promotion falling
through to a write (clobbers the `.tmp`), `RECOVERED` not printed, refused
`.tmp` deleted. Recording output unchanged: GW6 regenerated 1,046 of 1,046
identical, no recovery chatter on a clean log.

---

## 2026-09-23 — item 2: the horizon test run as pre-registered (`5a9ec05`)

`fpl_hist.py --horizon` implements the definition frozen in `9b43a78` without
change and calls the same `reliability_inputs()` / `project_reliability()` as
the single-week backtest; H = 1 reproduces `backtest_week` exactly (tested).
One implementation detail, not a redefinition: an origin t is used for a given
H only when t+H−1 ≤ GW38, so every graded horizon is complete.

The result table — per H and position, bottomup-H vs minutes-H with 95%
intervals, pooled by training window — is appended to
`HISTORICAL_VALIDATION.md` with the UTC timestamp and this commit hash, and
kept as `reports/horizon_2025-26.txt`. No pass criterion was pre-registered, so
none is applied here and nothing is concluded from it.

**Verified:** 6 tests, suite 152 → 158; 8 mutations each red — training on
the target weeks (leak), minutes-H not scaled by fixtures, benched players
dropped instead of scored 0, teams with no fixture kept, an incomplete horizon
graded, per-fixture projections not summed, either rho column dropped from the
report.

---

## 2026-09-23 — item 3: `--section bench_boost` (`3806daf`)

**Input:** a 15 — my current squad by default (`web_name` + team → id), or
`--squad id,id,…`. **Weeks:** the export's next six gameweeks (GW6–11 from
the GW5 export). **Per week:** each of the fifteen with fixture and FDR,
projection, P(start), minutes share and FLAG; the fifteen's total; GK/DEF slots
at FDR 4+; blanks; then **two labelled numbers** — the best XI from this 15,
and the best XI the same money buys around a fodder bench (the cheapest legal
fillers for the bench slots), same formation.

**Projection = the frozen three-layer rule**, through `project_reliability`
with the week's fixture list. GK/DEF: all terms (bottomup). MID/FWD: the xGI
term only — P(start) + xGI-per-90 × P(start), expressed in points. The
instruction wrote "xGI-per-90 × P(start)"; carrying it through the model's
scoring value keeps the fifteen in one unit so they can be summed and an XI
compared. Ordering within position is unchanged by that, and no fixture term
reaches a MID or FWD (tested, mutation-verified). Blank → no forecast; double
→ summed. FLAG is the frozen P1 predictor, minutes share ≤ 0.667 inclusive;
the constant is tested equal to `p1_eval.FLAG_MAX`.

**No new model code.** `_build_squad` gained a `quota` argument (default
unchanged) so the fodder-bench XI keeps the current XI's formation — the
16:10 amendment's per-position quota, not a cross-position optimiser; no
MILP. The 3-per-club limit is applied within the XI; the fodder are the
cheapest available and are not counted against it. Excluded from the nightly
"all" report.

**Not a projection change:** GW6 regenerated identical for all four sources;
`--section wildcard` output byte-identical before and after.

**Live, GW5 export, my current 15, budget £102.9m** (`reports/bench_boost_gw5.txt`):

```
  GW6
    all 15 projected: 57.8 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.0 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   56.2 pts
  GW7
    all 15 projected: 58.3 pts   GK/DEF at FDR 4+: 1   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.0 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   55.0 pts
  GW8
    all 15 projected: 58.2 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.3 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   54.9 pts
  GW9
    all 15 projected: 57.9 pts   GK/DEF at FDR 4+: 4   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               46.8 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   56.8 pts
  GW10
    all 15 projected: 58.6 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.3 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   58.0 pts
  GW11
    all 15 projected: 59.4 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               48.8 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   56.2 pts
```

**Verified:** 10 tests, suite **158 → 168**; 9 mutations each red — a blank
given a phantom fixture, a double counted once, the fixture term reaching
MID/FWD, the flag exclusive at 2/3 (unflags 180 of 270), the total counting
GK/DEF only, the FDR 4+ count including every position, the fodder XI built as
a full 15, the fodder cost not deducted from the XI budget (this one needed a
budget-bound fixture — at £100m the synthetic pool never touches the
ceiling; at £77m it does), the second labelled number dropped. One equivalent
mutant recorded rather than "caught": `<` vs `<=` at 0.667 is unobservable,
because no minutes total over 270 or 360 lands on 0.667 exactly; the boundary
that matters is 2/3, and that mutation is red.

---

## 2026-09-23 — review of items 1–3: A. budget = team value alone; B. `minutes` shows rho only (`448fec4`)

**A — the API's `value` already includes the bank.** Measured from the DB
rather than assumed: on the deadline days, `entry_gw.value` equals my fifteen's
`price_history` prices on that day plus the bank **to the tenth** — GW4:
value 100.4, bank 0.2, prices 100.2 (gap +0.0); GW5: value 100.3, bank 2.6,
prices 97.7 (gap +0.0). Today's export shows prices 97.5 against value 100.3
and bank 2.6 — a +0.2 gap that is five days of price drift since the GW5
deadline, not the bank. `bench_boost` and the wildcard builder used
`(value + bank) / 10` and so counted the bank twice (£102.9m instead of
£100.3m). Both now use `value / 10`; the printed line says "team value (bank
included)". Tests: the synthetic export pins budget = value/10 (100.3, not
100.5); on the real export, |value − (sum of my 15's prices + bank)| must be
within a tick per player and, when the bank is £0.5m or more, smaller than
the bank — the reading that would double-count it fails that. Mutations
(value + bank restored, in each builder): red.

**The item 3 table above was computed at £102.9m and is superseded.**
Re-run at £100.3m (`reports/bench_boost_gw5.txt`, and the corrected live
output in the item 3 report on Drive):

```
  squad: 15 players (my current 15)   budget £100.3m = team value (bank included)
  GW6
    all 15 projected: 57.8 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.0 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   56.0 pts
  GW7
    all 15 projected: 58.3 pts   GK/DEF at FDR 4+: 1   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.0 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   54.8 pts
  GW8
    all 15 projected: 58.2 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.3 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   54.7 pts
  GW9
    all 15 projected: 57.9 pts   GK/DEF at FDR 4+: 4   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               46.8 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   56.6 pts
  GW10
    all 15 projected: 58.6 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               47.3 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   57.7 pts
  GW11
    all 15 projected: 59.4 pts   GK/DEF at FDR 4+: 2   blanks: 0   flagged: 0
    XI from this 15 (4-3-3):                               48.8 pts
    best XI, same budget, fodder bench (4-3-3, fodder £16.7m):   56.0 pts
```

**B — `minutes` is a start probability, not a points forecast.** Its MAE,
const and bias are undefined; `sec_calibration` now prints only its rho columns
(whole, starters, n_st), the verdict reads `rho only`, and one note says why.
Other sources are unchanged. Tests: the minutes row carries `-` in the three
columns and the note; `xg` still prints MAE; the per-source summary prints rho
only for minutes. Mutations (MAE printed for minutes, note dropped, summary
prints MAE): red.

Suite 168 → 172; 5 mutations each red.

---

## 2026-09-23 — item 4 (break-list 3): `sec_wildcard` rewired to the frozen three-layer rule, scored on the six-week sum (`1c71235`)

The old section — shortlists and a squad from `project()`, the points model
that failed three times — is gone. The new one applies the rule frozen at
16:10 on 14 Sep, as amended, scored on H = 6 per the horizon test:

- **Layer 1, exclude:** status not `a`; under 45 minutes in the last four;
  **minutes share ≤ 0.667** (the frozen P1 flag); no fixture in the horizon.
  Counts printed per reason.
- **Layer 2, shortlist by role** (rules only, no model): `pens`, `corners`,
  `fk` = first choice; `defcon` = hit rate ≥ 50% over 2+ starts of 60 minutes;
  `arb` = a DEF whose xGI/90 reaches the MID median. A player's tier is his
  number of edges, and **a role edge outranks the model** — the ordering key
  is (tier, model), so layer 3 is a tiebreaker among equals, never an override.
- **Layer 3, order within position:** GK/DEF by the six-week bottomup sum;
  MID/FWD by P(start) × fixtures, then xGI/90 — the minutes baseline with bare
  xGI as the tiebreak, which is what the horizon test and ablation support.
- **Money: per-position quota, never global value-per-million.** The budget
  (team value alone, after review item A) is split across positions in the
  **current squad's shape** (each position's share of my fifteen's prices,
  scaled to the budget; quota-proportional if no squad is known). Each
  position is filled from its own ordered list — take the next candidate when
  he fits the position's share with enough left for the cheapest fill of the
  remaining slots — then leftover money upgrades the lowest-ranked pick of a
  position to a higher-ranked affordable one, position by position, until
  nothing moves. 3-per-club throughout. No MILP.
- **Output:** the per-position shortlists (top 8, with roles, six-week points,
  P(start) × fixtures, xGI/90); the squad's cost; the XI with the six-week sum
  per player and the captain (top six-week sum in the XI) marked `(C)`; the
  four bench players with their six-week sums and their fixtures for the
  horizon's weeks 3–6 (GW8–11 from a GW5 export); the XI and bench six-week
  totals; keeps from the current 15.

**Judgment calls, stated:** the six-week points sum used for XI selection,
captain and the printed `6wk` is the item 3 projection (bottomup for GK/DEF,
the xGI term for MID/FWD), so the XI is chosen in one unit; the MID/FWD
*ordering* is exactly as specified (P(start) × fixtures, then xGI/90) and is
separate from that sum. The split rule (current squad shape) is my choice
where the instruction only said "per-position quota"; it is printed so it can
be argued with.

**Live, GW5 export, budget £100.3m** (`reports/wildcard_gw5.txt`):

```
  budget £100.3m = team value (bank £2.6m included)
  split by position, current squad shape: GK £9.3m  DEF £26.8m  MID £36.0m  FWD £28.2m
  SQUAD  £100.2m of £100.3m   keeps from your current 15 (6): B.Fernandes, Barry, Groß, Haaland, Szoboszlai, Verbruggen
    XI (5-2-3)
      GK  Tzolakis       HUL    4.6  6wk  21.7  
      DEF Muharemović    LEE    5.0  6wk  34.8  defcon  (C)
      DEF Bogle          LEE    4.6  6wk  34.2  arb
      DEF Mukiele        SUN    5.4  6wk  29.8  arb,defcon
      DEF Khalaili       CRY    5.0  6wk  28.6  arb,defcon
      DEF Hall           NEW    5.3  6wk  26.9  corners,defcon,fk
      MID B.Fernandes    MUN   11.9  6wk  28.3  corners,fk,pens
      MID Tavernier      BOU    6.1  6wk  24.2  corners,fk
      FWD Haaland        MCI   15.6  6wk  30.7  pens
      FWD Barry          EVE    5.6  6wk  27.4  pens
      FWD Thiago         BRE    7.8  6wk  25.5  pens
    BENCH                            6wk   fixtures GW8-11
      GK  Verbruggen     BHA    4.5   21.1   LIV (A) 4 | MCI (A) 5 | BRE (H) 3 | HUL (A) 2
      MID Groß           BHA    5.8   23.6   LIV (A) 4 | MCI (A) 5 | BRE (H) 3 | HUL (A) 2
      MID Szoboszlai     LIV    7.0   22.3   BHA (H) 2 | ARS (H) 4 | CRY (A) 3 | MUN (H) 4
      MID Stach          LEE    6.0   18.6   SUN (A) 3 | BOU (A) 3 | TOT (H) 3 | CHE (A) 4
    XI six-week sum 312.1   bench six-week sum 85.6
```

**Verified:** 7 tests, suite **172 → 179**; 9 mutations each red — layer 1 no
longer excluding the flag, role edges dropped from the ordering, MID/FWD
ordered by points, the xGI/90 tiebreak dropped, the club limit removed (with
one club rigged to top every list), the split made quota-proportional, the
captain not marked, bench fixtures dropped, and the per-position fill
replaced by the global value-per-million builder. Nothing here changes a
projection: `bench_boost` and the four recorded sources are untouched.

---

## 2026-09-23 — item 4b (review D): no cross-position choice in `sec_wildcard` on the mixed-unit sums (`cc50441`)

The item 4 draft chose its XI and captain by comparing GK/DEF bottomup sums
with MID/FWD xGI-term points — two units — and came out 5-2-3 with a DEF
captain. Until the DEF calibration is addressed (~GW10), nothing across
positions is decided on the sums:

1. **Formation is a parameter.** `--formation DEF-MID-FWD`, default 4-3-3
   (legal: DEF 3–5, MID 2–5, FWD 1–3, ten outfield). The XI is the top of
   each position's ordered list up to that shape, taken within the position's
   money; `_best_xi` is no longer called here.
2. **Captain and vice** are the highest and next six-week full sums **among
   the MID/FWD in the XI**, marked `(C)` and `(V)`, with the reason line
   `captain restricted to MID/FWD: DEF over-spread` printed under the XI.
3. **One unit.** Every printed six-week sum — shortlists, XI, bench, totals —
   is `project_reliability` with **all terms**, for every position, so the
   fifteen add up (`fifteen` total printed). It sits next to the ordering
   metric (`by bottomup …` for GK/DEF, `by P(st)xfix … xGI/90 …` for MID/FWD).
   The ordering within position is exactly as frozen: for GK/DEF the full
   sum *is* the bottomup sum, so their order is unchanged; MID/FWD are still
   ordered by P(start) × fixtures then xGI/90, never by the sum.
   `project_week` gained a `terms` parameter (default: the frozen three-layer
   terms), so `bench_boost` is untouched.
4. **`--split GK,DEF,MID,FWD`** — any four positive numbers, scaled to the
   budget; default the current squad's shape. If a share cannot buy its
   position's cheapest legal fill it is raised to that fill and the others
   give up the difference in proportion to their slack (`repair_split`, the
   repaired split printed). A budget below the cheapest legal 15 is refused
   (`Could not assemble a legal 15 within £…`), never printed as a draft.
5. **Bench** = the cheapest candidates who pass layer 1 in each remaining
   slot (1 GK, and the outfield slots the formation leaves: 1 DEF + 2 MID for
   4-3-3). GK/DEF ties are broken by the fixture count in the horizon's later
   weeks (GW8–11 from a GW5 export — the Bench Boost window), then the
   frozen order. The bench is re-drawn after every upgrade round, so an
   upgrade that frees a cheaper body is used; it is never the leftovers of
   the XI walk.

**Live, GW5 export, budget £100.3m, 4-3-3, squad-shape split**
(`reports/wildcard_gw5.txt`):

```
  SQUAD  £97.8m of £100.3m   keeps from your current 15 (7): B.Fernandes, Barry, Groß, Haaland, Slater, Szoboszlai, Verbruggen
    XI (4-3-3, --formation)   sums = full model, all terms   by = the frozen ordering metric
      GK  Pickford       EVE    5.5  6wk  26.2  by bottomup 26.2                  
      DEF Hall           NEW    5.3  6wk  26.9  by bottomup 26.9                  corners,defcon,fk
      DEF Mukiele        SUN    5.4  6wk  29.8  by bottomup 29.8                  arb,defcon
      DEF Khalaili       CRY    5.0  6wk  28.6  by bottomup 28.6                  arb,defcon
      DEF Muharemović    LEE    5.0  6wk  34.8  by bottomup 34.8                  defcon
      MID B.Fernandes    MUN   11.9  6wk  30.5  by P(st)xfix 6.00 xGI/90 0.78     corners,fk,pens  (V)
      MID Groß           BHA    5.8  6wk  26.2  by P(st)xfix 6.00 xGI/90 0.53     corners,fk,pens
      MID Szoboszlai     LIV    7.0  6wk  26.1  by P(st)xfix 6.00 xGI/90 0.46     corners,fk,pens
      FWD Haaland        MCI   15.6  6wk  30.7  by P(st)xfix 6.00 xGI/90 0.99     pens  (C)
      FWD Barry          EVE    5.6  6wk  27.4  by P(st)xfix 6.00 xGI/90 0.79     pens
      FWD Thiago         BRE    7.8  6wk  25.5  by P(st)xfix 6.00 xGI/90 0.67     pens
    captain restricted to MID/FWD: DEF over-spread
    BENCH  cheapest who pass layer 1 per remaining slot (GK/DEF ties: GW8-11 fixture count)      fixtures GW8-11
      GK  Verbruggen     BHA    4.5  6wk  21.1   LIV (A) 4 | MCI (A) 5 | BRE (H) 3 | HUL (A) 2
      DEF Thomas         COV    4.0  6wk  26.4   FUL (H) 2 | SUN (H) 2 | EVE (A) 3 | CRY (H) 3
      MID Slater         HUL    4.5  6wk  20.1   BRE (H) 3 | IPS (H) 2 | ARS (A) 5 | BHA (H) 2
      MID Rudoni         COV    4.9  6wk  29.2   FUL (H) 2 | SUN (H) 2 | EVE (A) 3 | CRY (H) 3
    XI six-week sum 312.7   bench six-week sum 96.8   fifteen 409.5   (one unit: full model, all terms)
```

Read against item 4: the same top of every list; Haaland captain, Fernandes
vice; GK Pickford replaces Tzolakis (the top of the GK list is now
affordable once the bench is fodder); Groß enters the XI, Bogle and
Tavernier drop to make the 4-3-3; £2.5m unspent
because nothing higher-ranked is left to buy in any position. One thing the
one-unit column makes visible: bench MID Rudoni's full sum (29.2) exceeds
two XI midfielders' (26.2, 26.1) — the frozen ordering puts three role edges
above the model, as decided at 16:10 on 14 Sep. Observation, not a change.

**Verified:** 6 tests, suite **180 → 186**; 14 mutations each red — the section ignoring `--formation`, the builder ignoring the formation, captain from the whole XI, vice from the whole XI, the reason line dropped, the sums in the mixed units, the bench as the leftovers of the XI list, the bench tie-break dropped, the tie-break counting every week, `--split` ignored, the split repair dropped, the over-budget guard dropped, the bench not re-drawn after upgrades, the CLI parameters never reaching the section. `bench_boost`
output and the four recorded GW6 sources regenerate identically
(GW6 regenerated from the same export under both codes: 1,046 of 1,046 rows identical on source, event, player and predicted). Nothing here changes a projection.

---

## 2026-09-24 — item 5 (task-list 4): bench-vs-XI check in the squad section (`b10f5ae`)

`--section squad` now ends with a **BENCH vs XI** block for the next gameweek.
No detailed specification reached me beyond the title, so the definition is
stated here and can be argued with:

- **Population:** my current 15 as picked at the last deadline — slots 1–11
  are the XI, 12–15 the bench (`squads` rows; GW+1 picks are not visible
  before the deadline).
- **Unit:** every projection is `project_reliability` with **all terms**, for
  every position — the same one unit as the wildcard draft after review D —
  for the first gameweek in `fixtures_next6`. P(start) and the frozen
  minutes-share flag (≤ 0.667) are printed beside each player.
- **Comparison:** each bench player against the **lowest-projecting XI player
  of his own position**. Same-position swaps only: the formation is not chosen
  on the sums (review D). A second swap in the same position is not chained.
- **Verdict:** `SWAP` when the bench projection exceeds that XI player's
  (delta printed), `hold` otherwise; a blank XI player is the lowest by
  construction and reads `SWAP (XI blank)`; a blank bench player is
  `hold (bench blank)`.
- **Flag line:** XI players under the frozen flag, with their share, or `none`.
- Nothing here changes a projection or a recording: `bench_boost`,
  `wildcard` and the four recorded sources are byte-identical before and after.

**Live, GW5 export, GW6** (`reports/squad_gw5.txt`):

```
  BENCH vs XI  GW6   proj = full model, all terms (one unit); each bench player
  against the lowest-projecting XI player of his own position. Same-position swaps
  only - the formation is not chosen on the sums. Picks as of the last deadline.
    bench                proj P(st) share   lowest XI            proj P(st) share  delta  verdict
    GK  Kinsky           2.47  1.00  1.00   GK  Verbruggen       3.25  1.00  1.00  -0.78  hold
    MID Ndiaye           2.84  0.75  0.82   MID Groß             4.29  1.00  1.00  -1.45  hold
    MID Slater           3.42  1.00  0.96   MID Groß             4.29  1.00  1.00  -0.87  hold
    DEF Shaw             3.29  0.75  0.68   DEF Mitchell         3.59  1.00  0.91  -0.30  hold
    XI under the frozen flag (minutes share <= 0.667): none
```

**Verified:** 5 tests, suite **186 → 191**; 8 mutations each red — compared against the highest XI player, compared across positions, mixed units, a blank XI player not the lowest, swap verdict reversed, flag line dropped, flag reversed, bench including slot 11. GW6 regenerated from the same export under both codes: 1,046 of 1,046 rows identical on source, event, player and predicted.

---

## 2026-09-24 — item 6 (task-list 5): the export window is the whole season (`624241a`)

`fpl_sync.py` exported `player_gw_recent` and `fixtures_status` for the last
six gameweeks (`event BETWEEN gw-5 AND gw`). From GW7 that would have dropped
GW1 from the canonical slice, so the live weights, priors and team rates
(`reliability_inputs`) would have come from a sliding window while the
historical run uses full seasons — the limitation stated up front on
2026-09-14. Both queries now take every gameweek through the export's
(`event <= gw`); `fixtures_played` already did. The last-4 form columns
(`pts_last4`, `mins_last4`, `defcon_last4`, `starts_last4`, and
`top_players_recent`) keep their four-gameweek window: they are definitions,
not a slice, and the frozen P1 predictor reads them.

- **Changes nothing before GW7.** At GW5 the old window (`0..5`) already held
  the whole season: the export regenerated from a read-only connection to the
  real database with the new query is identical to today's export: 1,538 player_gw_recent rows (GW1–5), 50 fixture flags, 667 all_players rows.
- **From GW7** the export grows by one gameweek of rows per week (~275 × N
  rows; ~10k by GW38) and `--section backtest`, `consistency` and the
  calibration guard see every gameweek instead of six.
- No projection changes today; the recording path is untouched
  (`fpl_edge.py` only gains a corrected comment in the `bottomup` source).

**Verified:** 2 tests, suite **191 → 193** — the export at simulated GW8, 10,
20 and 38 carries per-gameweek rows and fixture flags for every gameweek and
the canonical slice sees them all; the last-4 columns at GW10 still sum four
gameweeks. 3 mutations each red — the player_gw_recent window restored to six gameweeks, the fixtures_status window restored, the last-4 columns widened to the season.

---

## 2026-09-24 — item 7 (task-list 6): the mini-league layer — effective ownership with captaincy (`d939845`)

`--section eo` keeps its two ownership-gap blocks and the historical captaincy
block, and gains three forward-looking ones. No detailed specification reached
me beyond "effective ownership with captaincy", so the definitions are stated
here and can be argued with:

- **Effective ownership with captaincy.** From the latest picks (GW gw — the
  next gameweek's picks are not visible before the deadline): a captain counts
  2, a starter 1, a bench player 0, a Triple Captain 2 (spent, cannot recur).
  For every player in any squad: my multiplier, the rivals' EO (mean
  multiplier over the N rivals), how many rivals start and captain him, and
  **net/pt = mine − EO**, the points gained on the average rival per point he
  scores. Two lists: their stakes I don't match (net < 0) and mine they don't
  (net > 0).
- **Per rival, next gameweek (projected).** For each rival, with the full
  model, all terms, one unit, for the first upcoming gameweek: **swing** =
  Σ (my multiplier − theirs) × projection; **shared** = Σ min(mine, theirs)
  × projection; **yours / theirs** = what only one side holds. Blanks and
  unmapped names count 0. Their captain named. This is the model's number
  under the current picks, with the DEF calibration still pending.
- **Captain cover.** My candidates are the MID/FWD in my XI, by projection —
  never a DEF (review D). Each with the rivals' EO of him, how many captain
  him, and the net stake per point if I captain him (2 − EO). Printed with the
  reason it is not a recommendation: the expected value of a captaincy is its
  projection alone; EO changes the variance of my rank, not the expectation —
  the field's captain covers, a differential swings.
- Nothing here changes a projection or a recording.

**Live, GW5 export** (`reports/eo_gw5.txt`), the three new blocks:

```
  EFFECTIVE OWNERSHIP WITH CAPTAINCY   (rival picks as of GW5; captain = 2, bench = 0, TC = 2)
  THEIR STAKES YOU DON'T MATCH   (net/pt < 0: every point he scores costs you)
  player         team pos  mine    EO  start  capt  net/pt
  Gvardiol       MCI  DEF     0  0.67   4/6    0/6    -0.67
  Rogers         CHE  MID     0  0.67   4/6    0/6    -0.67
  Gibbs-White    NFO  MID     0  0.50   2/6    1/6    -0.50
  Calvert-Lewin  LEE  FWD     0  0.50   3/6    0/6    -0.50
  Kinsky         TOT  GK      0  0.33   2/6    0/6    -0.33
  Muharemović    LEE  DEF     0  0.33   2/6    0/6    -0.33
  Saka           ARS  MID     0  0.33   2/6    0/6    -0.33
  Raya           ARS  GK      0  0.33   2/6    0/6    -0.33
  Ndiaye         MCI  MID     0  0.17   1/6    0/6    -0.17
  Van Hecke      TOT  DEF     0  0.17   1/6    0/6    -0.17
  M.Sangaré      BRE  MID     0  0.17   1/6    0/6    -0.17
  Palmer         CHE  MID     0  0.17   1/6    0/6    -0.17
  YOUR STAKES THEY DON'T MATCH   (net/pt > 0: every point gains on the average rival)
  player         team pos  mine    EO  start  capt  net/pt
  Verbruggen     BHA  GK      1  0.00   0/6    0/6    +1.00
  Virgil         LIV  DEF     1  0.00   0/6    0/6    +1.00
  Mitchell       CRY  DEF     1  0.00   0/6    0/6    +1.00
  Barry          EVE  FWD     1  0.00   0/6    0/6    +1.00
  Groß           BHA  MID     1  0.17   1/6    0/6    +0.83
  Wissa          NEW  FWD     1  0.17   1/6    0/6    +0.83
  N.Williams     NFO  DEF     1  0.33   2/6    0/6    +0.67
  Szoboszlai     LIV  MID     1  0.33   2/6    0/6    +0.67
  Haaland        MCI  FWD     2  1.50   5/6    4/6    +0.50
  B.Fernandes    MUN  MID     1  0.50   2/6    1/6    +0.50

  PER RIVAL, GW6   (projected: full model, all terms, one unit; picks as of GW5; blanks 0)
  rival                 their captain    swing  shared  yours  theirs
  ReturnOfTheDjedi FC   Gibbs-White       -2.0    18.8   34.7    36.7
  Revelstoke FC         Haaland           +1.0    24.5   29.1    28.1
  No More Mr. Rice Guy  Haaland           +1.8    29.0   24.5    22.7
  Skori FC              B.Fernandes       +1.9    10.2   43.3    41.4
  Bruno Dos Tres        Haaland           +4.2    15.2   38.3    34.1
  PyroNeniZlocin        Haaland           +7.3    15.2   38.3    31.0

  CAPTAIN COVER, GW6   (MID/FWD in your XI by projection; stake/pt = 2 - EO if captained)
  candidate      team   proj    EO  capt  stake/pt
  B.Fernandes    MUN    5.17  0.50   1/6      +1.50
  Haaland        MCI    5.11  1.50   4/6      +0.50
  Barry          EVE    4.57  0.00   0/6      +2.00
  Szoboszlai     LIV    4.30  0.33   0/6      +1.67
  Groß           BHA    4.29  0.17   0/6      +1.83
  Wissa          NEW    3.76  0.17   0/6      +1.83
  the expected value of a captaincy is its projection alone; EO changes the variance
  of your rank, not the expectation: the field's captain covers, a differential swings.
```

Read: six rivals; Haaland is captained by four of them (EO 1.50), so my
armband on him is a +0.50 stake per point — cover, not a swing. Fernandes
projects marginally higher (5.17 v 5.11) at EO 0.50; Barry at EO 0.00 is the
pure differential. The per-rival swings are within ±8 points of projection —
the league is decided by variance on shared assets, which is the point of the
layer.

**Verified:** 4 tests, suite **193 → 197**; 12 mutations each red — Triple Captain as 3, bench as 1, captain not doubled, net sign flipped, cover counting starters, swing ignoring multipliers, projections in the mixed units, candidates including DEF, candidates including the bench, stake = 1 − EO, candidates unordered, expectation note dropped. `bench_boost`,
`wildcard` and `squad` byte-identical; GW6 regenerated from the same export under both codes: 1,046 of 1,046 rows identical on source, event, player and predicted.

---

## 2026-09-24 — item 4c (review E): layer 2 admits, layer 3 ranks — the role tier leaves the ordering key (`c97ae18`)

Item C read "shortlist by role" as a rank: the ordering key was (number of
role edges, metric), so a three-role player sat above any higher metric in
his position. That was my reading, not the rule. As specified now: **layer 2
admits a player to the shortlist and never ranks him**; **layer 3 orders the
whole shortlist by its metric alone** — GK/DEF by the summed per-fixture
bottomup (the six-week sum, all terms), MID/FWD by P(start) × fixtures, then
xGI/90. The role flags (pens, corners, fk, defcon, arb) are still computed
and printed beside every player — shortlists, XI and bench — for a human
override at draft time. The header says so. Nothing else in the section
moves: budget, split, formation, bench, captain rule as in review D.

**Live, GW5 export, budget £100.3m, 4-3-3, squad-shape split**
(`reports/wildcard_gw5.txt`), the top eight of each ordered shortlist with
price, then the squad:

```
  SHORTLISTS  (top 8 per position; 6wk = full model, all terms, GW6-11:
               one unit for every position, next to the ordering metric)
    GK   player         team     £  roles              6wk P(st)xfix  xGI/90
         Pickford       EVE    5.5                    26.2      6.00    0.00
         Trafford       LEE    5.0                    25.0      6.00    0.00
         Raya           ARS    6.1                    23.8      6.00    0.00
         Kelleher       BRE    5.0                    23.4      6.00    0.00
         Tzolakis       HUL    4.6                    21.7      6.00    0.00
         Verbruggen     BHA    4.5                    21.1      6.00    0.04
         A.Becker       LIV    5.5                    21.0      6.00    0.00
         Donnarumma     MCI    5.5                    20.8      6.00    0.00
    DEF   player         team     £  roles              6wk P(st)xfix  xGI/90
         Muharemović    LEE    5.0  defcon            34.8      6.00    0.11
         Bogle          LEE    4.6  arb               34.2      6.00    0.36
         Branthwaite    EVE    5.5  defcon            33.5      6.00    0.04
         Tarkowski      EVE    6.1  defcon            33.0      6.00    0.04
         Justin         LEE    4.5                    32.2      6.00    0.13
         De Cuyper      BHA    4.9  arb               31.8      6.00    0.47
         Calafiori      ARS    5.8  arb               31.3      6.00    0.28
         Gabriel        ARS    8.0                    30.7      6.00    0.14
    MID   player         team     £  roles              6wk P(st)xfix  xGI/90
         Saka           ARS    9.5  pens              34.6      6.00    0.91
         B.Fernandes    MUN   11.9  corners,fk,pens   30.5      6.00    0.78
         Mbeumo         MUN    7.9                    30.3      6.00    0.77
         E.Le Fée       SUN    5.7  corners           28.3      6.00    0.70
         Cherki         MCI    7.8  corners,fk        28.8      6.00    0.67
         Ndoye          NFO    5.5                    28.0      6.00    0.62
         Rudoni         COV    4.9  fk                29.2      6.00    0.62
         Rogers         CHE    7.7                    26.5      6.00    0.61
    FWD   player         team     £  roles              6wk P(st)xfix  xGI/90
         Haaland        MCI   15.6  pens              30.7      6.00    0.99
         Isak           LIV    9.1                    27.4      6.00    0.79
         Barry          EVE    5.6  pens              27.4      6.00    0.79
         Brobbey        SUN    5.7                    25.8      6.00    0.69
         Thiago         BRE    7.8  pens              25.5      6.00    0.67
         Calvert-Lewin  LEE    6.0  pens              25.0      6.00    0.64
         Gonzalo        FUL    6.0  pens              24.6      6.00    0.62
         Emersonn       IPS    5.5                    22.6      6.00    0.49

  SQUAD  £100.3m of £100.3m   keeps from your current 15 (5): B.Fernandes, Barry, Haaland, Slater, Verbruggen
    XI (4-3-3, --formation)   sums = full model, all terms   by = the frozen ordering metric
      GK  Tzolakis       HUL    4.6  6wk  21.7  by bottomup 21.7                  
      DEF Muharemović    LEE    5.0  6wk  34.8  by bottomup 34.8                  defcon
      DEF Bogle          LEE    4.6  6wk  34.2  by bottomup 34.2                  arb
      DEF Branthwaite    EVE    5.5  6wk  33.5  by bottomup 33.5                  defcon
      DEF Tarkowski      EVE    6.1  6wk  33.0  by bottomup 33.0                  defcon
      MID Saka           ARS    9.5  6wk  34.6  by P(st)xfix 6.00 xGI/90 0.91     pens  (C)
      MID B.Fernandes    MUN   11.9  6wk  30.5  by P(st)xfix 6.00 xGI/90 0.78     corners,fk,pens
      MID Rudoni         COV    4.9  6wk  29.2  by P(st)xfix 6.00 xGI/90 0.62     fk
      FWD Haaland        MCI   15.6  6wk  30.7  by P(st)xfix 6.00 xGI/90 0.99     pens  (V)
      FWD Isak           LIV    9.1  6wk  27.4  by P(st)xfix 6.00 xGI/90 0.79     
      FWD Barry          EVE    5.6  6wk  27.4  by P(st)xfix 6.00 xGI/90 0.79     pens
    captain restricted to MID/FWD: DEF over-spread
    BENCH  cheapest who pass layer 1 per remaining slot (GK/DEF ties: GW8-11 fixture count)      fixtures GW8-11
      GK  Verbruggen     BHA    4.5  6wk  21.1   LIV (A) 4 | MCI (A) 5 | BRE (H) 3 | HUL (A) 2
      DEF Thomas         COV    4.0  6wk  26.4   FUL (H) 2 | SUN (H) 2 | EVE (A) 3 | CRY (H) 3
      MID Slater         HUL    4.5  6wk  20.1   BRE (H) 3 | IPS (H) 2 | ARS (A) 5 | BHA (H) 2
      MID Sadiki         SUN    4.9  6wk  18.3   LEE (H) 2 | COV (A) 2 | CHE (H) 4 | AVL (A) 4
    XI six-week sum 337.0   bench six-week sum 85.9   fifteen 423.0   (one unit: full model, all terms)
```

Against item 4b (tier ordering): the XI six-week sum rises 312.7 → 337.0 and
the money is fully spent. The MID list is now Saka, Fernandes, Mbeumo,
Le Fée, Cherki, Ndoye, Rudoni, Rogers — Groß (three roles, xGI/90 0.53) and
Szoboszlai (0.46) leave the top eight; Rudoni is the third XI midfielder
because £4.9m is what the MID share leaves after Saka and Fernandes, and
Tzolakis replaces Pickford in goal for the same reason (nothing is left over
to upgrade). Five keeps from the current 15 (was seven). The shortlists are
the argument: the flags say who has a role, the order says who the model
prefers, and the draft is the human's.

**Verified:** three item-C tests rewritten (roles admit but never rank — a
three-role midfielder with the lower metric sits below a no-role midfielder
with the higher one, the same for defenders, the roles still printed in the
shortlist and beside him in the XI; the legal-squad rig now tops the lists by
metric; the build takes the top of the list, not the value-per-million pick);
the split test's binding budget moved to £80.0m. Suite stays at **197**.
5 mutations each red — the role tier restored to the ordering key, the tier as a tiebreak after the metric, roles dropped from the shortlist print, roles dropped from the XI lines, the old global value-per-million build in place of the per-position fill. `bench_boost`, `squad` and `eo` byte-identical; GW6 regenerated from the same export under both codes: 1,046 of 1,046 rows identical on source, event, player and predicted.

---

## 2026-09-24 — item 8 (F 1): one-match concentration in xGI rates — three columns, information only (`389495a`)

Wherever an xGI-per-90 rate is printed — the wildcard shortlists, the
wildcard XI lines (MID/FWD), and the squad section, which now prints the rate
for my 15 — three columns sit beside it, computed by one function
(`xgi_rate_variants`) from the canonical per-gameweek rows:

- **conc** = best single gameweek's xGI / season xGI, flagged `!` at 0.50 and
  above; blank when season xGI is 0.
- **trim90** = xGI/90 with that best gameweek removed, when the player has 4+
  gameweeks with minutes; else blank.
- **med90** = median per-gameweek xGI per 90 over gameweeks of 60+ minutes;
  else blank.

A double gameweek is one row in the canonical slice, so it counts as one
"game" here. **Nothing orders or projects on these:** the ordering rate and
the rate the model consumes are the raw season xGI/90 as before (tested), and
the recording path is untouched. Two things the live columns show at once:
goalkeepers read `1.00!` because their season xGI is one tiny event, so the
flag is noise for GK by construction; and among the draft's midfielders
Fernandes (0.64), Mbeumo (0.51) and Rudoni (0.52) carry the flag while Saka
(0.35) does not — which is exactly what F (2) tests before anything acts on it.

**Verified:** 4 tests, suite **197 → 201** — the arithmetic on five games with
one spike (conc 0.60, trim90 0.10, med90 0.10) and an even count (median of
the middle two); the blanks (three games → no trim90; no 60-minute game → no
med90; zero xGI → no conc; a 45-minute game out of med90 and in raw90; no
minutes → no rate); a spike-vs-steady pair where raw prefers the spike and
trim90/med90 the steady one — the ordering follows raw and the rate the
projection consumes is raw; the columns present in the shortlists, the XI
line and the squad section with the flag on the spike. 11 mutations each red — conc over minutes, trim90 keeping the best game, trim90 on three games, med90 over every game, the flag threshold moved, MID/FWD ordered on trim90, ordered on med90, the columns dropped from the shortlist, from the XI line, from the squad section, and the squad section printing trim90 as the rate.
`bench_boost` and `eo` byte-identical; the wildcard squad unchanged in
names, prices and sums; GW6 regenerated from the same export under both codes: 1,046 of 1,046 rows identical on source, event, player and predicted.
