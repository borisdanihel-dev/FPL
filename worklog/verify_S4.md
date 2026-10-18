# verify_S4 — backtest-verifier report

Item S4 (tools/backtest.py, tests/test_S4.py), repository C:\GIT\FPL-b, branch
lane-b. Verifier model: Fable 5.1 (claude-fable-5-1), effort high, as
.claude/agents/backtest-verifier.md on disk (read first; it matches the loaded
instructions). Descriptive item: checks 1, 2, 5, 6, 7 and the prereg's
acceptance tests 1-10. Date 2026-10-18. No key-like strings occur in any file
or output examined (nothing to mask).

## Prereg before code

- prereg/S4.md committed f9ca3d0 (15:40:27 +0200) and amended 94fbc36
  (15:43:22 +0200); first and only code commit 4eab638 (16:16:55 +0200).
  PASS.
- The ruling text ("RULING S4 ..." points 1-4) and "Amendment 1" (points 1
  and 3) are present verbatim in prereg/S4.md.
- `git diff 94fbc36..4eab638 --stat`: .gitignore (+3, `/tools/out/`),
  tests/__init__.py (empty), tests/test_S4.py (+439), tools/backtest.py
  (+889). No other file.

## Check 1 — point-in-time leak check

### 1a Truncation test (decides) — FAIL

Method: for g in (5, 20, 38) a copy of historical/2025-26 holding only rows
with round < g unchanged, round g's rows with every outcome column replaced by
garbage (minutes 90, points 50, xG 3.0, BPS 99, ...; pairing columns element,
fixture, round, team, opponent_team, was_home, value, selected kept), no row
with round > g; fixtures.csv with events < g unchanged, event g with fake
scores 7-7 (pairing only), nothing later. Rebuilt g with the item's own
`load_2526` + `rebuild_2526` and `best_fifteen(squad_candidates())`, compared
to the rebuild from the full file (what --compare/--report graded). Scripts:
scratchpad leak_1a.py, diag_1a.py.

| GW | source   | population | max abs diff | result |
|----|----------|------------|--------------|--------|
| 5  | bottomup | 342 = 342  | 2.149e+00 (156 of 342 differ) | FAIL |
| 5  | minutes  | 342 = 342  | 0            | ok |
| 5  | p_start  |            | 0            | ok |
| 5  | P(defcon) per player |  | 0           | ok |
| 5  | P(cs) per player |      | 6.70e-01    | FAIL |
| 5  | decision squad | identical, cost 99.0m |  | ok |
| 20 | bottomup | 336 = 336  | 3.210e-01 (161 of 336 differ) | FAIL |
| 20 | minutes  | 336 = 336  | 0            | ok |
| 20 | P(cs) per player |      | 2.12e-01    | FAIL |
| 20 | decision squad | differs: metric 57,428,466 vs 59,251,952, same cost 99.9m | | FAIL |
| 38 | all of the above |      | 0            | ok |

Cause (diagnosed, not guessed): `fpl_hist.canonical_from_vaastav` builds
`players[pid]["team"]` from the player's last row in the whole file, and
`fpl_edge.canonical_through` slices `rows` and `team_matches` but not
`players`. A rebuild of GW5 therefore uses each player's club as of GW38.
Example: pid 260 is Crystal Palace in GW5 (and in every row through GW5) but
mapped to MCI; his GW5 bottomup is 3.719 (full file) vs 5.867 (truncated).
Because `reliability_inputs` aggregates team xG and GC by that same map, 11
teams' rate inputs differ at GW5 and at GW20 (AVL, BOU, BUR, CHE, CRY, EVE,
FUL, MCI, TOT/NFO, WHU, WOL), which moves P(clean sheet) and the bottomup
forecast of players who never moved (every Newcastle defender shifts by
0.783 at GW5; every Arsenal defender by 0.321 at GW20). The club cap in
`squad_candidates` uses the same map, which is why the GW20 most-selected 15
differs. At GW38 the last row is the current row, so nothing differs.

Effect on the item's printed output (full-file rebuild vs truncated rebuild,
real outcomes in both): GW5 starters bottomup rho +0.1504 vs +0.1612, all
+0.3345 vs +0.3370, regret11 84 vs 75; GW20 starters rho +0.1092 vs +0.1406,
tau +0.0815 vs +0.1039, decision XI+C 48.0 vs 61.0. So the compare tables,
report.txt and power.txt (s_d of bottomup minus minutes) contain values that
depend on post-deadline information for every gameweek before the last club
change of the season.

The defect is in the frozen adapter and slice, not in a line S4 wrote, but
prereg/S4.md asserts that bottomup and minutes qualify because "every input
is a pre-deadline row", and the item's numbers rest on that assertion. The
rule for this check is any value differing by more than 1e-9 = FAIL.

The `minutes` source and `p_start` are unaffected (player-level only).

### 1b Timestamp audit (decides) — PASS

Real log C:\GIT\FPL-data\projection_log.csv (5,734 rows; data worktree at
4af6abe "nightly 2026-10-18"), re-read independently of `fpl_edge.forecasts`.
Settled gameweeks 1-6 (data_checked = 1, every fixture finished). Rows at or
after their event's deadline anywhere in the log: none. Rows the harness
reads for settled gameweeks: 2,574; the harness's forecast dict equals
`forecasts(read_log(), d)` exactly. Last snapshot read per (event, source)
and its margin before the deadline: GW4 own/xg 2026-09-11T21:55:16Z
(14h34m); GW5 own/xg/bottomup/minutes 2026-09-17T21:55:18-19Z (19h34m); GW6
own/xg/bottomup/minutes 2026-10-09T21:50:35-36Z (12h09m). 0 late rows.

### 1c Shift probe (warns only)

Spearman of forecast(g) vs points(g) and vs points(g+1), players with 60+
minutes in both, pooled.

| season | source | filter | n | unshifted | shifted | diff | flag |
|---|---|---|---|---|---|---|---|
| 2025/26 | bottomup | all | 4977 | +0.065 | +0.050 | +0.014 | ok |
| 2025/26 | bottomup | starters | 2902 | +0.146 | +0.097 | +0.049 | ok |
| 2025/26 | minutes | all | 4977 | -0.009 | -0.007 | -0.002 | ok |
| 2025/26 | minutes | starters | 2902 | +0.081 | -0.021 | +0.102 | WARN |
| 2026/27 | own | all / starters | 323 / 103 | +0.123 / +0.025 | +0.106 / +0.131 | +0.017 / -0.105 | ok |
| 2026/27 | xg | all / starters | 319 / 103 | +0.090 / +0.093 | +0.119 / +0.022 | -0.030 / +0.071 | ok |
| 2026/27 | bottomup | all / starters | 156 / 103 | -0.005 / -0.127 | -0.016 / -0.011 | +0.010 / -0.116 | ok |
| 2026/27 | minutes | all / starters | 156 / 103 | +0.036 / +0.000 | -0.018 / +0.000 | +0.054 / 0 | ok |

The one WARN (2025/26 minutes, starters, diff +0.102) concerns the `minutes`
source, which passes 1a with zero difference and 1b. Context: with the
starters filter (p_start >= 0.8) every 2025/26 starter has p_start exactly
1.0 (GW5: 133 of 133; GW20: 118 of 118; GW38: 89 of 89), so the minutes
forecast is a constant except for double-gameweek players (GW26: 13 at 2.0);
its starters Spearman is 0.000 in 31 of 34 gameweeks and the probe's value is
driven by those few doubles. Information, not a defect of the item; the
report's "minutes starters +0.028 [+0.008,+0.056]" cell is this artefact.

## Check 2 — clean-checkout test runs — PASS

`git archive` of 94fbc36 (before) and 4eab638 (after) into the scratchpad,
FPL_DATA_DIR unset:
- before: `python test_fpl.py` — Ran 386 tests, OK (skipped=8)
- after:  `python test_fpl.py` — Ran 386 tests, OK (skipped=8)
- after:  `python -m unittest tests.test_S4` — Ran 24 tests, OK
- after:  `python -m unittest discover -s tests -t .` — Ran 24 tests, OK
test_fpl.py is unchanged by the item (lane B never edits it).

## Check 3 — not required (descriptive); reproduction done anyway

Every CLI output re-run into tools/out/verify (gitignored) is byte-identical
to the implementer's file in tools/out: selftest.txt (400 replications, seed
4, n = 69: power 0.777 PASS, false positives 0.068 PASS; 65 s), power.txt
(s_d starters Spearman 0.1032 over 34 GWs; all Spearman 0.0213; decision
6.3221), report.txt, and all 12 compare_*.txt (2025-26 bottomup/minutes all
and starters; 2026-27 own/xg/bottomup/minutes pairs, all and starters).
Two files compare_2026-27_xg_minutes_{all,starters}.txt appeared in
tools/out at 16:22:57-58 (after the commit, during this verification);
written by the main session, gitignored, not part of the commit, not
reproduced here.

## Check 4 — not required (descriptive); conformance noted

Constants in tools/backtest.py equal the prereg: B = 10,000, 90% percentile
CI, seed 20261018, two-sided bootstrap p floored at 1/(B+1) and capped at 1,
Holm alpha 0.10, BH q 0.10, z_alpha 1.645, z_beta 0.842, deltas 0.01/0.02/
0.03, self-test 400 reps seed 4 s 0.10 delta 0.03 with bars 0.80 +/- 0.05
and 0.05 +/- 0.02, starters P(start) >= 0.8, top-k (1, 3, 11), clip 1e-6,
2/5/5/3, club cap 3, 100.0m, GW5-38, DEFCON 10/12, captain doubled, missing
forecast 0, `_best_xi` formations. One small deviation: the 2025/26 DEFCON
component additionally requires minutes > 0 (`a["mins"] > 0`, line 403),
which the prereg does not state. No metric promotion or re-tuning is visible
in the commit; the self-test bars were met on the first and only recorded
run.

## Check 5 — recording path — PASS

The item adds no recording code. `git diff 94fbc36..4eab638 --stat` touches
only .gitignore, tests/__init__.py, tests/test_S4.py and tools/backtest.py:
fpl_edge.py, fpl_nightly.py, fpl_sync.py, fpl_gate.py, fpl_publish.py,
fpl_ship.py, fpl_hist.py and .github/workflows are unchanged. Nightly
isolation: `python -c "import fpl_nightly, fpl_ship, fpl_edge, fpl_sync,
fpl_gate, fpl_publish"` loads no module under tools/ or analysis/ (empty
list); no runner file has an `import tools|analysis|backtest` line; no
workflow references tools/ or analysis/. The projection log was not
regenerated here (the runner is the only writer; `--record` is never run
locally); the data worktree is byte-for-byte untouched by every run in this
verification (117-file listing with mtimes and sizes identical before and
after; `git -C C:\GIT\FPL-data status` clean).

## Check 6 — mutation spot-check — PASS, with two survivors reported

Six one-line mutations applied one at a time to the scratch copy of 4eab638
(the repository file untouched; cmp confirms the copy restored), `python -m
unittest tests.test_S4` after each:
- M1 `train = E.canonical_through(c, t)` (harness training slice includes
  round g): 24 OK — SURVIVED.
- M2 `inp = E.reliability_inputs(E.canonical_through(c, t), gws_played=t)`:
  24 OK — SURVIVED.
- M3 `sel_round = g` (decision squad reads gameweek g's own `selected`):
  red (test_candidates_use_previous_gameweek_selected).
- M4 Kendall denominator without the tie terms: red
  (test_kendall_tau_b_with_ties).
- M5 lockdown ignores unfinished fixtures: red (test_lockdown_guard,
  test_compare_needs_a_common_graded_week).
- M6 captain not doubled: red (test_decision_points).

M1 and M2 survive because the bottomup/minutes forecasts in `rows` come from
`E.backtest_week` (which slices internally), while the harness's own `train`
and `inp` (lines 378-379) feed only `p_start` (the starters filter and the
P(start) component) and the P(cs)/P(defcon) components; acceptance test 4
checks `rows["bottomup"]` only and its mutation is a mock of
`canonical_through` rather than the harness line. A leak into the starters
filter or the Brier/log-loss cells would not be caught by the suite.

## Check 7 — secrets — PASS

The four files of the commit: no match for apiKey=, api_key, Authorization,
Bearer, x-api-key, token=, secret, ODDS_API, AKIA..., ghp_..., sk-...; no
32+ character hex or base64 blob in the added lines (only test names).

## Acceptance tests 1-10 (prereg)

1. Self-test: reproduced exactly (power 0.777, false positives 0.068, n = 69;
   seed 4, 400 reps, B = 10,000). PASS. Note 0.068 sits 0.002 inside the
   0.03-0.07 bar.
2. Reader = `fpl_edge.forecasts(read_log(), d)`: test_reader_is_the_s2_rule
   (two pre-deadline snapshots, one post-deadline, a tie; 13 rows, tie 9.0,
   99.0 never read, dropped = 1) passes; confirmed on the real log in 1b.
   PASS.
3. Lockdown: test_lockdown_guard (GW4 one fixture unfinished, GW6
   data_checked = 0, settled = {5}) passes; M5 turns it red. PASS.
4. Leak test: the test as written passes (altering pts/xg/minutes of rows
   with round >= g changes nothing; the mock goes red). The verifier's own
   three-gameweek truncation (check 1a) FAILS for bottomup at GW5 and GW20
   through the player-team map, which the test does not alter, and the
   harness's own training lines are not covered (M1, M2 survive). FAIL.
5. Rebuilt 2025/26 equals `backtest_week` on a toy season within 1e-9:
   test_rebuilt_equals_backtest_week passes. The prereg names
   `fpl_hist.backtest_week`; the function lives in fpl_edge and
   `fpl_hist.backtest_report` calls `E.backtest_week` — the same function.
   PASS.
6. Hand cases checked by hand: Kendall 4/6 and 0.8 (conc 4, tx 1, ty 1),
   Holm {a} and {a, b}, BH {a, b, c} and {a, b}, top-k regret with the id tie
   break, MAE/Brier/log loss incl. the clip, decision 4-5-1 XI = 86.0
   forecast with captain 14 -> 102.0 realised, brute-force squad on four
   small worlds with the club cap binding at least once and pruning
   neutral, power formula, Spearman delegated to `_spearman`. PASS.
7. CLI: `--compare own bottomup --season 2025-26 --filter starters` prints
   "MISSING INPUT: own cannot be rebuilt for 2025/26: ..." and returns 2;
   `--compare bottomup minutes --season 2025-26 --filter starters`, the
   2026-27 compares, `--report`, `--power`, `--selftest` all return 0. PASS.
8. Writes nothing under the data folder and nothing outside --out: data
   worktree listing identical before/after; every output landed in
   tools/out/verify (gitignored via `/tools/out/`). PASS.
9. Nightly isolation: test_nightly_imports_nothing_under_tools_or_analysis
   passes and my own import check agrees. PASS.
10. tests/test_S4.py holds 24 tests; test_fpl.py 386 before and after. PASS.

## Other findings (information)

- tools/backtest.py line 11: the module docstring contains `C:\GIT\FPL-data`
  and Python 3.14 emits `SyntaxWarning: "\G" is an invalid escape sequence`
  on every run (a future Python makes it an error). Cosmetic; a raw
  docstring or `C:\\GIT` fixes it.
- The 2025/26 starters filter admits only players with p_start = 1.0 (3 of 4
  starts = 0.75 < 0.8), so the `minutes` source is constant on that filter;
  its starters cells in report.txt are not informative.
- Write guard: this verifier wrote only worklog/verify_S4.md and gitignored
  files under tools/out/verify/ and the session scratchpad. `git status` in
  C:\GIT\FPL-b also shows ` M CHANGELOG.md`, ` M worklog/SESSION_STATE_B.md`
  and `?? worklog/cc_2026-10-18_S4.md` — not mine; the main session's
  in-progress files.

VERDICT: FAIL

Reason: check 1a decides and fails. Rebuilding 2025/26 gameweeks 5 and 20
from inputs available before each deadline (rows with round < g plus round
g's pairings) gives bottomup forecasts that differ from the item's output by
up to 2.149 (156 of 342 players at GW5, 161 of 336 at GW20), P(clean sheet)
by up to 0.67, and a different most-selected 15 at GW20; the per-gameweek
numbers the item printed move with it (GW20 starters rho 0.109 vs 0.141,
decision 48 vs 61). The cause is that `canonical_from_vaastav` assigns each
player the club of his last row in the whole season and `canonical_through`
does not slice `players`, so the fixture pairing, the club cap and 11 teams'
xG/GC rates for an early gameweek carry post-deadline club changes; the
prereg's qualification of bottomup ("every input is a pre-deadline row")
does not hold as implemented, acceptance test 4 does not alter the team
column and so passes, and the harness's own training lines survive two
leak mutations. Everything else passes: the prereg preceded the code, the
rulings are verbatim, 386/386 and 24 tests, every output byte-identical on
re-run, the 2026/27 reader verified on the real log with no late row, the
runner untouched and importing nothing under tools/, the data folder
untouched, no secrets. GW38 (last club change already in the data) and the
`minutes` source are unaffected, which points at the fix: a per-gameweek
team map (the team of the latest row with round <= g) in the adapter or in
the harness, with a test that alters the team column of rows with round >= g.
