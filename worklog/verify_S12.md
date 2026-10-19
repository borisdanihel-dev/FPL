# Verifier report — S12 (BUILD_PLAN.md Step 12, minutes model v2, offline part)

Verifier: Claude Fable 5.1 (backtest-verifier agent, `.claude/agents/backtest-verifier.md`
read from disk first; it matched the loaded instructions). Date: 2026-10-19.
Worktree `C:\GIT\FPL-b`, branch `lane-b`, HEAD `e68bf70`. Nothing outside this
file was written in the tree; `C:\GIT\FPL-data` was read only (its status is
clean, last commit `9da6ff1`); no `fpl_sync.py`, `--record` or
`fpl_nightly.py` was run. All scratch work lives in the session scratchpad.

## Prereg order — PASS

- `prereg/S12.md`: ruling verbatim in `7111240` (01:09:17 +0200), template rows
  filled in `3b94269` (01:27:10 +0200).
- First S12 code commit `005531a` (03:52:49 +0200), then `d8a2ee5` (03:56:29)
  and `e68bf70` (04:00:25, tests only). The prereg precedes all code.
- Item diff `65b9232..e68bf70`: `tests/test_S12.py` (+249), `tests/test_S5.py`
  (+11/−5, toy schema gains `team_id`, `yellow`), `tools/minutes_v2.py` (+605).
  `tools/minutes_v2.py` changed between `005531a` and HEAD only by the
  `try/finally` connection close (`rows_2627` → `_rows_2627`); no constant,
  rule or metric moved. `test_fpl.py` untouched.

## Check 1 — point-in-time — PASS

Scratch script `pit.py` (scratchpad), against `C:\GIT\FPL-b\historical\2025-26`
through the item's own entry points (`rows_2526`, `origin_cut`,
`congestion_factor`, `v2_pstart`, `test_2526`) and the S4 harness
(`canonical_at` → `canonical_through(t-1)` → `reliability_inputs`).

### 1a Truncation test — PASS (origins 5, 21, 22, 38)

For each origin t, three truncated copies of the history were written and the
feature rebuilt from them:

- `junk_keepfix`: rows of round > t deleted; rows of round t kept for the
  club map but with `minutes=7, starts=1, yellow_cards=3, total_points=99,
  red_cards=1`; fixtures intact (the schedule is known in advance).
- `junk`: as above and fixtures of event > t deleted.
- `keep`: rows of round > t and fixtures of event > t deleted, round t intact
  (so the per-origin evaluation row can be recomputed).

| t | cut (first kickoff of t) | factor (c, lo, hi, n_short) | players | v2 P(start) diffs > 1e-9 | v2 P(sub) diffs | current p_start diffs |
|---|---|---|---|---|---|---|
| 5 | 2025-09-20 11:30Z | (1.0, None, None, 0) | 741 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| 21 | 2026-01-06 20:00Z | (1.0, 0.91239, 1.02863, 565) | 795 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| 22 | 2026-01-17 12:30Z | (1.0, 0.93163, 1.02472, 691) | 799 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| 38 | 2026-05-24 15:00Z | (1.0, 0.96966, 1.03422, 999) | 841 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

(three cells = the three truncation modes; no key mismatch anywhere; the cut
and the fitted factor tuple are identical in every mode.) The per-origin
evaluation rows (n, Brier cur/v2, MAE cur/v2, GK mismatches, c, c's CI, the
touched counts) recomputed from the `keep` copies at t = 5, 21, 22, 38 are
IDENTICAL to the rows of the full GW5–38 run.

### 1b Timestamp audit — PASS (every origin 5–38)

For every t in 5..38 and every `(player, fixture)` row in `rows.played` at
origin t: the fixture's event is < t and its kickoff is before the origin
(0 violations at every origin); no fixture of a round < t kicks off at or
after the origin (no postponed-match row survives into the training set); no
fixture of a round > t kicks off before the origin (t = 5, 21, 38). The
smallest gap between the last prior-round kickoff and the origin is 1 day
16:30, so every input also predates the real FPL deadline (90 minutes before
the first kickoff). Clubs come from `hist_pit.club_map` `by_gw[t]` (rows ≤ t,
carried forward over blanks; the item's own test plants a GW6 transfer and
shows the GW5 club). Round-t rows contribute only the club and the targets
(`starts`, points); the `junk` truncation above proves their minutes, starts,
yellow cards and points do not touch the feature.

Nothing in the congestion fit reaches past the origin: `congestion_factor`
skips matches with kickoff ≥ cut or not in `known` (event < t), and the
bootstrap unit is the training round. Suspensions use `rows_key_before` (kickoff
< cut) for cautions and minutes.

### 1c Shift probe — N/A

The primary metric is a Brier score on starts, not a correlation on points.

## Check 2 — clean-checkout suites — PASS

`git archive` of `65b9232` (before) and `e68bf70` (after) into the scratchpad,
`FPL_DATA_DIR` unset, `python -m unittest discover -p "test*.py"`:

- before: Ran 545 tests in 292.4 s, OK (skipped=10), 0 FAIL/ERROR.
- after: Ran 552 tests in 290.1 s, OK (skipped=10), 0 FAIL/ERROR.

The 7 new tests are `tests/test_S12.py` (Rules ×4, Season, Live, CLI).
`tests/test_S12.py` alone: Ran 7 tests, OK, ~0.6 s; hermetic (toy history and
toy sqlite in temporary folders, `now` injected, `--data` pointed at the temp
folder; no network, no `C:\GIT\FPL-data`, no git identity).

## Check 3 — the pre-registered evaluation re-run — PASS

`python tools/minutes_v2.py --test --out <scratch>` (14 s) and
`--live --out <scratch>` from `C:\GIT\FPL-b` (defaults: history
`historical/2025-26`, data `C:\GIT\FPL-data`): both outputs are
byte-identical (`cmp`) to `tools/out/minutes_v2_test_2025-26.txt` and
`tools/out/minutes_v2_live.txt`. The in-process run inside `pit.py` is
byte-identical too. Full-precision numbers from my run:

- (a) Brier current − v2: mean +0.00165865, 90% CI [−0.00008768, +0.00329099],
  n = 34 gameweeks, bootstrap p = 0.116 → prints +0.0017 [−0.0001, +0.0033];
  bar ≥ 0.01 with lower bound > 0: FAIL.
- (b) bottomup MAE v2 − current: −0.00423155 [−0.01320736, +0.00518537] →
  −0.0042; bar ≤ +0.02: PASS.
- (c) keeper-starter mismatches current 76, v2 56; bar v2 ≤ current: PASS.
- pre-registered result: FAIL (all three must hold) — matches the item's
  output exactly (difference 0, well within 1e-6).

Live (GW8, deadline 2026-10-23 17:30 UTC, from `fpl_export_gw7_2026-10-18.json.gz`
and `fpl.sqlite`): congestion factor 1.000; touched lock 54, cover 1,
congestion 0, suspension 0; 0 overrides applied (`overrides.csv` does not
exist on the branch); information only. The live run wrote nothing to the
tree or the data worktree.

## Check 4 — metric, filter, bootstrap, threshold as pre-registered — PASS

| Prereg | Code (`tools/minutes_v2.py`) |
|---|---|
| Primary: Brier of P(start) vs `starts ≥ 1`, per gameweek, current − v2 | `b_cur`, `b_v2` per GW with `y = max(starts ≥ 1)` over round t; `d_brier = b_cur − b_v2` |
| Population: recording gate, 45+ minutes in the last four, same for both; GW5–38 | `p["mins_last4"] < 45 or not pairings[team] → skip`, applied once to both; `range(5, 39)` (342/319/334 players at t = 5/21/38, recomputed by me) |
| Comparison: `fpl_edge.start_probability` on the same inputs (the S4 harness's rebuilt `p_start`) | `E.reliability_inputs(E.canonical_through(canonical_at(hist, t), t−1), gws_played=t−1)["players"][pid]["p_start"]`; I recomputed `start_probability` from `starts_last4` over rounds (t−5, t−1] for every player at t = 5, 21, 38: 0 mismatches |
| Bootstrap: unit gameweek, 10,000 resamples, 90% percentile, seed 20261018 | `BT.bootstrap_mean` with `B = 10000`, `CI = 0.90`, `SEED = 20261018`, one value per gameweek |
| (a) mean ≥ 0.01 and lower bound > 0 | `PASS_BRIER = 0.01`; `bb["mean"] >= PASS_BRIER and bb["lo"] > 0` |
| (b) MAE(v2) − MAE(current) ≤ 0.02, both through `project_reliability` with P(start) swapped | `MAE_SLACK = 0.02`; `E.project_reliability(pid, inp, fx)` vs the same with `p_start = pv`; `bm["mean"] <= MAE_SLACK` |
| (c) keeper mismatches v2 ≤ current, summed GW5–38 | top-P keeper per club with a fixture vs who started; `mis_v <= mis_c` |
| All three must hold | `a_ok and b_ok and c_ok` |

Rule constants match the prereg: window 4, lock window 3, 0.95/0.05/0 with
the latest-start tie rule, regular = ≥ 3 of the last 4, rest ≤ 3 days,
bands (5, 19) and (10, 32), credibility m/(m + 4). The prereg says "no
re-tuning after viewing results"; the only post-`005531a` source change is
the connection close, the outputs regenerate byte-identically, and the result
is recorded as FAIL. No metric was promoted: the printed (b) and (c) are the
prereg's co-conditions, not substitutes for (a).

Information only (no prereg conflict, for the chat if it ever adopts v2):
rest days use the floor of the timedelta (`(ko − prev).days`); the caution
band reads "before the 19th match" literally (`n_next ≤ 19`); the cover rule
runs after the keeper lock, so an absent locked keeper's replacement can end
above 0.95 while the locked keeper keeps 0.95.

## Check 5 — recording path — PASS

The item is offline. `git diff --stat 65b9232 e68bf70` lists only
`tests/test_S12.py`, `tests/test_S5.py`, `tools/minutes_v2.py`; no runner
file (`fpl_nightly.py`, `fpl_ship.py`, `fpl_edge.py`, `fpl_sync.py`,
`fpl_gate.py`, `fpl_publish.py`, `.github/`, `test_fpl.py`) changed, so the
recorded forecasts of every model cannot have moved. The nightly isolation
check, run by me in the tree: importing `fpl_nightly, fpl_ship, fpl_edge,
fpl_sync, fpl_gate, fpl_publish` loads nothing from `tools/` or `analysis/`
(`[]`); `tests/test_S3.py::test_the_nightly_imports_nothing_under_tools_or_analysis`
and `tests/test_S12.py::CLI` passed in the after suite. `projection_log.csv`
was not regenerated here (CLAUDE.md: the runner is the only writer and
`--record` is never run locally); the data worktree's status is clean.

## Check 6 — mutation spot-check — PASS (9 of 9 red)

In a scratch `git archive` of HEAD (`scratchpad/mut`), one line of
`tools/minutes_v2.py` changed per run, `python -m unittest tests.test_S12`,
the pristine file restored (verified equal) and the suite green again:

| mutation | result |
|---|---|
| m1 training through t (`rnd >= t` → `rnd > t`) | RED (`test_point_in_time_and_the_current_model`) |
| m2 lock 0.95/0.05 → 0.9/0.1 | RED (`test_states_and_lock`) |
| m3 `REST_SHORT` 3 → 4 | RED (`test_congestion_factor`) |
| m4 served ban applied again (drop `total − y_prev < count`) | RED (`test_suspensions`) |
| m5 factor kept when the CI includes 1 | RED (`test_congestion_factor`) |
| m6 cover never inherits | RED (`test_cover`) |
| m7 keeper tie rule dropped | RED (`test_states_and_lock`) |
| m8 regular = 2 of 4 | RED (`test_cover`) |
| m9 window 4 → 5 | RED (`test_cover`, `test_states_and_lock`) |

The tree's `tools/minutes_v2.py` was never edited.

## Check 7 — secrets — PASS

`git diff 65b9232 e68bf70` and the two output files grepped for `apiKey=`,
`api_key`, `Authorization`, `Bearer`, `x-api-key` and any 32+ character
alphanumeric run: no hit. `overrides.csv` does not exist. Nothing key-like
to mask.

## VERDICT: PASS

The prereg (ruling verbatim and template rows) was committed before any S12
code; the feature rebuilt from truncated histories at GW5, 21, 22 and 38 is
identical to the item's output to 1e-9 in every mode, and every input row at
every origin 5–38 predates the origin (and the real deadline); the suites run
545 → 552 tests, all green on clean checkouts; my re-run of `--test` and
`--live` is byte-identical to the item's outputs with the pre-registered
result FAIL on (a) +0.0017 [−0.0001, +0.0033] against the bar ≥ 0.01 with
lower bound > 0, (b) −0.0042 PASS, (c) 76 → 56 PASS; metric, population,
bootstrap and thresholds are exactly the prereg's with no re-tuning after the
result; no runner file changed and the nightly imports nothing from `tools/`;
nine single-line mutations each turn `tests/test_S12.py` red; no secret in any
added or changed file. The item correctly records a FAIL of its own bar;
minutes v2 drives no decision and replaces nothing.
