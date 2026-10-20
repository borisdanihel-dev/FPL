# verify_S4 — backtest-verifier report (second run, after RULING S4 amendment 2)

Item S4 (tools/backtest.py, tools/hist_pit.py, tests/test_S4.py), repository
C:\GIT\FPL-b, branch lane-b, verified at commit 973b3f8. Verifier model:
Fable 5.1 (claude-fable-5-1), effort high, as .claude/agents/backtest-verifier.md
on disk (read first; it matches the loaded instructions). Descriptive item:
checks 1, 2, 5, 6, 7, the prereg's acceptance tests 1-10 and amendment 2
point 3's tests. Date 2026-10-18. No key-like strings occur in any file or
output examined (nothing to mask).

## First run (summary)

The first run (on 4eab638) returned FAIL on check 1a: `fpl_hist.canonical_from_vaastav`
gives every player the club of his last row in the whole season and
`canonical_through` does not slice `players`, so a GW5 or GW20 rebuild used
end-of-season clubs (bottomup differed by up to 2.149 on 156 of 342 players at
GW5, P(clean sheet) by up to 0.67, a different most-selected 15 at GW20), and
two harness training-line mutations (M1, M2) survived the suite. What changed
since: RULING S4 amendment 2 appended verbatim to prereg/S4.md (79d14ee,
before any fix code); new offline module tools/hist_pit.py (973b3f8) derives
each player's club per gameweek from his row's fixture, cross-checked against
the team column, carried forward over blanks, never backfilled; backtest.py
rebuilds gameweek t on `canonical_at(hist, t)` and reads the decision squad's
clubs from the map; eight tests added (32 now); the pre-fix outputs are kept
in tools/out/old_clubmap_leak/ and marked "invalid: club-map leak" in the
item's report; the docstring SyntaxWarning is gone. The frozen fpl_hist.py and
fpl_edge.py are untouched (`git diff 94fbc36..973b3f8 --stat`: .gitignore,
CHANGELOG.md, prereg/S4.md, tests/__init__.py, tests/test_S4.py,
tools/backtest.py, tools/hist_pit.py, worklog/*).

## Prereg before code

- prereg/S4.md committed f9ca3d0 (15:40:27), amendment 1 94fbc36 (15:43:22);
  first code commit 4eab638 (16:16:55). Amendment 2 committed 79d14ee
  (16:47:21); the fix commit 973b3f8 (16:55:45). PASS.
- The ruling text (RULING S4 points 1-4, Amendment 1 points 1 and 3,
  "RULING S4 amendment 2" points 1-4 to END RULING) is present verbatim in
  prereg/S4.md. The amendment 2 header states it was appended after the
  verifier's FAIL and before any fix code, and that the test design is
  unchanged; the git order confirms it.

## Check 1 — point-in-time leak check

### 1a Truncation test (decides) — PASS

Method (scratchpad v2/leak_1a_v2.py, v2/diag_components_v2.py; outputs
v2/leak_1a_v2.txt, v2/diag_components_v2.txt): for g in (5, 20, 38) a copy of
historical/2025-26 holding only rows with round < g unchanged, round g's rows
with every outcome column replaced by garbage (minutes 90, points 50, xG 3.0,
BPS 99, defcon 40, ...; pairing columns element, fixture, round, team,
opponent_team, was_home, value, selected, position, name kept), no row with
round > g; fixtures.csv with events < g unchanged, event g with fake 7-7
scores (pairing only), nothing later. Rebuilt g with the item's own
`load_2526` + `rebuild_2526` and `best_fifteen(squad_candidates())`, compared
with the rebuild from the full file (what --compare/--report graded).

| GW | compared | result |
|----|----------|--------|
| 5  | club map `by_gw[5]` truncated == full (741 players) | identical |
| 5  | bottomup 342 = 342 players, max abs diff 0.000e+00 (0 differ) | OK |
| 5  | minutes 342 = 342, max abs diff 0 | OK |
| 5  | p_start, max abs diff 0 | OK |
| 5  | P(start), P(cs) per round-5 fixture, P(DEFCON) per player: 970 = 970 keys, max abs diff 0 | OK |
| 5  | decision squad identical, metric 55,221,338, cost 99.0m | OK |
| 20 | club map `by_gw[20]` (790 players) | identical |
| 20 | bottomup 336 = 336, max abs diff 0 (0 differ); minutes 0; p_start 0 | OK |
| 20 | components per player 947 = 947 keys, max abs diff 0 | OK |
| 20 | decision squad identical, metric 59,251,952, cost 99.9m | OK |
| 38 | club map `by_gw[38]` (841 players) | identical |
| 38 | bottomup 334 = 334, max abs diff 0; minutes 0; p_start 0 | OK |
| 38 | components per player 937 = 937 keys, max abs diff 0 | OK |
| 38 | decision squad identical, metric 59,656,465, cost 100.0m | OK |

Worst difference over every forecast, probability and squad: 0.0 (the first
run's GW5 worst was 2.149 and the GW20 squad differed). The per-gameweek
starters numbers tie to the compare file: GW5 bottomup rho +0.1612, GW20
+0.1406 (the first run's truncated values, now reproduced from the full file).
Note on method: my script's component *pair lists* (which players enter
Brier/log loss) differ between the copies because the garbage outcomes change
who played 60+ minutes; that is my copy's artefact, so the probabilities were
compared per (player, fixture) directly through the harness's `_p_cs`,
`_p_defcon` and `reliability_inputs` on `canonical_at(hist, g)` — identical.

Planted club change in a later round (asked for in this run): for g in
(5, 20, 36) one player with rows in every later round was moved to a
different club from round g+2 on (team column, fixture, was_home,
opponent_team rewritten consistently so the cross-check holds), in a copy of
the full file.
- GW5: element 36 Aston Villa -> BOU from round 7 (32 rows; the adapter's
  end-of-season club for him is BHA). Rebuild of GW5: bottomup, minutes,
  p_start, every component pair (probability and outcome), and the decision
  squad identical (max diff 0). Sanity: at GW7 his bottomup moves 5.020 ->
  4.338 and 25 players differ (the plant took effect).
- GW20: element 38 Aston Villa -> MUN from round 22 (17 rows). GW20 identical
  (max diff 0); at GW22 his bottomup 4.090 -> 2.824, 32 players differ.
- GW36: element 1 Arsenal -> BHA from round 38 (1 row). GW36 identical; at
  GW38 his bottomup 3.780 -> 2.978, 1 player differs.

Other adapter `players` fields: no player has more than one `position` or
`name` across his rows in the real file, so the adapter's last-row values for
those fields carry nothing from later rounds.

Real club map (`python tools/hist_pit.py`): 841 players, rounds 1-38, 29
mid-season club changes (e.g. element 260 CRY -> MCI from GW23, the first
run's example; elements 391, 52, 83, 630, 426 from GW2; 149 BHA -> WHU GW4
-> BHA GW24; 168 BHA -> CHE GW4 -> LEE GW22); the real-file cross-check
raises on no row.

### 1b Timestamp audit (decides) — PASS

Real log C:\GIT\FPL-data\projection_log.csv (5,734 rows; data worktree at
4af6abe "nightly 2026-10-18", unchanged since the first run), re-read
independently of `fpl_edge.forecasts` (scratchpad audit_1b.py, output
v2/audit_1b.txt). Settled gameweeks 1-6. Rows at or after their event's
deadline anywhere in the log: none. Rows the harness reads for settled
gameweeks: 2,574; the harness dict equals `forecasts(read_log(), d)` exactly.
Last snapshot read per (event, source) and margin before the deadline: GW4
own/xg 2026-09-11T21:55:16Z (14h34m); GW5 own/xg/bottomup/minutes
2026-09-17T21:55:18-19Z (19h34m); GW6 all four 2026-10-09T21:50:35-36Z
(12h09m). 0 late rows. For 2025/26 the truncation test above is the
timestamp audit: every input row for gameweek g has round < g, plus round g's
pairing columns.

### 1c Shift probe (warns only)

Spearman of forecast(g) vs points(g) and vs points(g+1), players with 60+
minutes in both, pooled (v2/shift_1c.txt; 2025/26 now on the point-in-time
club map).

| season | source | filter | n | unshifted | shifted | diff | flag |
|---|---|---|---|---|---|---|---|
| 2025/26 | bottomup | all | 4977 | +0.065 | +0.050 | +0.014 | ok |
| 2025/26 | bottomup | starters | 2902 | +0.147 | +0.099 | +0.047 | ok |
| 2025/26 | minutes | all | 4977 | -0.009 | -0.007 | -0.002 | ok |
| 2025/26 | minutes | starters | 2902 | +0.081 | -0.021 | +0.102 | WARN |
| 2026/27 | own | all / starters | 323 / 103 | +0.123 / +0.025 | +0.106 / +0.131 | +0.017 / -0.105 | ok |
| 2026/27 | xg | all / starters | 319 / 103 | +0.090 / +0.093 | +0.119 / +0.022 | -0.030 / +0.071 | ok |
| 2026/27 | bottomup | all / starters | 156 / 103 | -0.005 / -0.127 | -0.016 / -0.011 | +0.010 / -0.116 | ok |
| 2026/27 | minutes | all / starters | 156 / 103 | +0.036 / +0.000 | -0.018 / +0.000 | +0.054 / 0 | ok |

The one WARN (2025/26 minutes, starters, diff +0.102) is the same as in the
first run and is cleared by 1a and 1b (the `minutes` source rebuilds with zero
difference from truncated inputs). Context, unchanged: on the starters filter
every 2025/26 starter has p_start exactly 1.0, so the minutes forecast is
constant except for double-gameweek players, and the probe is driven by those
few. Information, not a defect of the item.

## Check 2 — clean-checkout test runs — PASS

`git archive` of 94fbc36 (before the item) and 973b3f8 (after) into the
scratchpad, FPL_DATA_DIR unset:
- before: `python test_fpl.py` — Ran 386 tests, OK (skipped=8)
- after:  `python test_fpl.py` — Ran 386 tests, OK (skipped=8)
- after:  `python -m unittest tests.test_S4` — Ran 32 tests, OK (skipped=1:
  the real-season club-map test, since historical/ is gitignored and absent
  from the archive)
- after:  `python -m unittest discover -s tests -t .` — Ran 32 tests, OK (skipped=1)
- in the worktree (historical/2025-26 present): tests.test_S4 — Ran 32
  tests, OK (0 skipped); discovery — Ran 32 tests, OK.
test_fpl.py is unchanged by the item (lane B never edits it).

## Check 3 — not required (descriptive); reproduction done anyway

Every CLI output re-run into tools/out/verify2 (gitignored) is byte-identical
to the implementer's file in tools/out (17 of 17: selftest.txt — power 0.777
PASS, false positives 0.068 PASS, n = 69; power.txt — s_d starters Spearman
0.1028 over 34 GWs, all Spearman 0.0215, decision 5.6823; report.txt; the two
2025-26 compares and the twelve 2026-27 compares). `--compare own bottomup
--season 2025-26 --filter starters` prints "MISSING INPUT: own cannot be
rebuilt for 2025/26: ..." and returns 2; every other run returns 0.
The pre-fix power.txt in tools/out/old_clubmap_leak differs from the current
one (s_d 0.1032 / 0.0213 / 6.3221 before), as expected from the fix.

## Check 4 — not required (descriptive); conformance noted

Constants unchanged from the first run and equal to the prereg: B = 10,000,
90% percentile CI, seed 20261018, two-sided bootstrap p floored at 1/(B+1)
and capped at 1, Holm alpha 0.10, BH q 0.10, z_alpha 1.645, z_beta 0.842,
deltas 0.01/0.02/0.03, self-test 400 reps seed 4 s 0.10 delta 0.03 with bars
0.80 +/- 0.05 and 0.05 +/- 0.02, starters P(start) >= 0.8, top-k (1, 3, 11),
clip 1e-6, 2/5/5/3, club cap 3, 100.0m, GW5-38, DEFCON 10/12, captain
doubled, missing forecast 0. The 2025/26 DEFCON component still additionally
requires minutes > 0 (not stated in the prereg; unchanged since the first
run). The fix commit changes no metric, filter, bootstrap setting or bar; the
self-test bars were met on the first and only recorded run, and the self-test
file is byte-identical before and after the fix. Amendment 2 was appended
after results were seen, but it fixes a leak and alters no test design, as
its text states; the pre-fix numbers are kept and marked "invalid: club-map
leak" in worklog/cc_2026-10-18_S4.md (lines 67-106) and CHANGELOG.md, as
the ruling requires.

## Check 5 — recording path — PASS

The item adds no recording code. `git diff 94fbc36..973b3f8 --stat` touches
no runner file: fpl_edge.py, fpl_hist.py, fpl_nightly.py, fpl_sync.py,
fpl_gate.py, fpl_publish.py, fpl_ship.py and .github/workflows are unchanged.
Nightly isolation: importing fpl_nightly, fpl_ship, fpl_edge, fpl_sync,
fpl_gate, fpl_publish and fpl_hist loads no module from tools/ or analysis/
(empty list, scratchpad v2/isolation.py); no runner file has an
`import tools|analysis|backtest|hist_pit` line; no workflow references
tools/ or analysis/. The projection log was not regenerated here (the runner
is the only writer; `--record` is never run locally); the data worktree is
untouched by every run in this verification (`git -C C:\GIT\FPL-data status`
clean before and after, HEAD 4af6abe).

## Check 6 — mutation spot-check — PASS (10 of 10 red)

Ten one-line mutations applied one at a time to a scratch copy of the
worktree files (scratchpad v2/mutate_v2.py; the repository files untouched —
byte-identical after the run), `python -m unittest tests.test_S4` after each
(baseline 32 OK):
- H1 hist_pit.club_at: `g = cm["through"]` (always the end-of-season club):
  RED, 4 failures (blank/no-backfill, look-ahead probe, planted transfer,
  rebuild uses the club of that gameweek).
- H2 club_at backfills from the end-of-season map before the first row: RED
  (test_blank_carries_forward_and_no_backfill).
- H3 derive_clubs cross-check dropped: RED (test_cross_check_and_unknown_fixture_raise).
- H4 derive_clubs takes the club from the team column instead of the
  fixture: RED (same test).
- H5 club_map does not carry forward over a blank: RED (test_blank_carries_forward_and_no_backfill).
- B1 backtest.canonical_at returns the adapter's end-of-season players: RED
  (test_rebuild_uses_the_club_of_that_gameweek).
- B2 rebuild_2526 reads the club map one round ahead (`canonical_at(hist, t + 1)`):
  RED (same test).
- B3 squad_candidates uses the adapter's end-of-season club: RED (same test).
- B4 = first run's survivor M1, `train = E.canonical_through(c, t)`: RED
  (test_components_leak_free_and_mutation_red).
- B5 = first run's survivor M2, reliability inputs through round t with
  gws_played = t: RED (same test).

## Check 7 — secrets — PASS

Every file the item adds or changes (tools/backtest.py, tools/hist_pit.py,
tests/test_S4.py, tests/__init__.py, prereg/S4.md, .gitignore, CHANGELOG.md,
worklog/SESSION_STATE_B.md, worklog/cc_2026-10-18_S4.md including the
uncommitted working copies): no match for apiKey=, api_key, Authorization,
Bearer, x-api-key, token=, ODDS_API_KEY, AKIA..., ghp_..., sk-..., or any
32+ character hex blob. `py_compile` with warnings as errors: clean (the
first run's SyntaxWarning is gone).

## Acceptance tests 1-10 (prereg) and amendment 2 point 3

1. Self-test: reproduced byte-identically (power 0.777, false positives
   0.068, n = 69; seed 4, 400 reps, B = 10,000). PASS.
2. Reader = `fpl_edge.forecasts(read_log(), d)`: test_reader_is_the_s2_rule
   passes; confirmed on the real log in 1b (2,574 rows, dict equal). PASS.
3. Lockdown: test_lockdown_guard passes (GW4 one fixture unfinished, GW6
   data_checked = 0, settled = {5}). PASS.
4. Leak test: the three-gameweek truncation (1a) gives zero difference for
   every forecast, probability and squad at GW5, GW20 and GW38; the planted
   later-round club change leaves GW5, GW20 and GW36 unchanged; the suite's
   mutations and mine (B1-B5) go red. PASS (was FAIL).
5. Rebuilt 2025/26 equals `backtest_week` on a toy season within 1e-9:
   test_rebuilt_equals_backtest_week passes (the function lives in fpl_edge;
   fpl_hist calls the same one). PASS.
6. Hand cases: tests Metrics.* and Squad.* pass (Kendall with ties, top-k
   tie break, MAE/Brier/log loss with clip, decision XI with captain doubled
   and missing forecast 0, most-selected 15 equals brute force, Holm and BH,
   power formula, Spearman delegated to `_spearman`). PASS.
7. CLI: refusal for `own` on 2025/26 (exit 2); the 2025-26 and 2026-27
   compares, `--report`, `--power` and `--selftest` run (exit 0). PASS.
8. Writes nothing under the data folder (worktree clean) and nothing outside
   --out (every output in tools/out/verify2, gitignored via `/tools/out/`).
   PASS.
9. Nightly isolation: test_nightly_imports_nothing_under_tools_or_analysis
   passes and my own import check agrees (hist_pit included). PASS.
10. tests/test_S4.py holds 32 tests; test_fpl.py 386 before and after. PASS.

Amendment 2 point 3:
- "every row's derived club is one of its fixture's two teams":
  test_every_row_club_is_one_of_its_fixture_teams (toy) and
  test_real_season_rows_match_their_fixtures (real file; `derive_clubs`
  raises on any mismatch; 841 players, through 38, > 0 changes) pass; my run
  of `tools/hist_pit.py` on the real file raises nothing. PASS.
- "a planted mid-season transfer changes club in exactly the right gameweek":
  test_planted_transfer_changes_club_in_exactly_that_gameweek passes
  (ALP x3 then BET x3, `changes` = [(1, 4, ALP, BET)]); my real-data plants
  at rounds 7, 22 and 38 are visible at exactly those rounds and invisible
  before. PASS.
- "a look-ahead probe shows that the club for gameweek g is computed from
  rounds <= g only": test_look_ahead_probe passes on the toy; on the real
  file `by_gw[g]` from the copy truncated to rounds <= g equals the full
  file's for g = 5, 20, 38. PASS.

## Other findings (information)

- `reliability_inputs` (frozen) attributes a player's training-period xG to
  his club *as of g*; for the 29 transferred players, xG earned at the old
  club counts toward the new club's rate. Not a point-in-time leak (the club
  at g is pre-deadline information), a modelling simplification of the frozen
  function; stated for the record.
- A player who changes club in a round in which he has no row keeps his
  previous club until his next row (carry-forward), as amendment 2 specifies.
- The 2025/26 starters filter still admits only players with p_start = 1.0,
  so the `minutes` source is constant on that filter (unchanged observation).
- Write guard: this verifier wrote only worklog/verify_S4.md and gitignored
  files under tools/out/verify2/ and the session scratchpad. `git status` in
  C:\GIT\FPL-b also shows ` M CHANGELOG.md`, ` M worklog/SESSION_STATE_B.md`
  and ` M worklog/cc_2026-10-18_S4.md` — not mine; the main session's
  in-progress files, as announced.

VERDICT: PASS

Reason: the defect of the first run is fixed and shown fixed. Rebuilding
2025/26 gameweeks 5, 20 and 38 from a copy holding only rows with round < g
plus round g's pairing columns gives every bottomup and minutes forecast,
every P(start), P(clean sheet) and P(DEFCON), the club map for g and the
most-selected 15 identical to the item's output (worst difference 0.0,
threshold 1e-9); a club change planted in round g+2 leaves gameweek g
unchanged at g = 5, 20 and 36 while visibly changing g+2; the real-file
cross-check of every row's club against its fixture raises nothing; the
2026/27 reader uses no row at or after a deadline; the one shift-probe WARN
is the same `minutes`-starters artefact as before and is cleared by 1a and
1b. Amendment 2 was committed verbatim before the fix code, the frozen
adapter and fpl_edge are untouched, the runner imports nothing under tools/,
the data folder is untouched, all 17 outputs reproduce byte-identically, the
pre-fix numbers are kept and marked invalid as the ruling requires, 386/386
and 32/32 tests pass before and after, ten mutations (including the two that
survived the first run) all go red, and no file holds a secret.
