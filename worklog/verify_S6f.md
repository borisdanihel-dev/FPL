# Verifier report: S6f (BUILD_PLAN.md Part F, F-D; S6b and S6c repeated on 2024/25)

Verifier model: Fable 5.1 (claude-fable-5-1), the native `backtest-verifier`
agent; `.claude/agents/backtest-verifier.md` read from disk first (it matches
the loaded instructions). Date 19 Oct 2026, about 22:40 local.

Scope: branch `s6f-wip`, HEAD 483a8a6 (tests), code 161cd69, base a454e09
(s10b-wip), in the scratch worktree. Prereg on master: `3c955b5:prereg/S6f.md`.
Inputs read-only under `C:/GIT/FPL/historical` and the worktree's
`tools/odds/`. Everything I ran wrote only under my scratch folder
(`.../scratchpad/verify_s6f/`); this file is my only write in the worktree.
No session transcript or chat log was read. No key-like string appears in any
file I read for this item or in this report.

## Prereg before code

- `prereg/S6f.md` committed 3c955b5 at 2026-10-19 22:12:26 +0200.
- First code commit 161cd69 at 22:19:44 +0200; tests 483a8a6 at 22:26:42.
- The F-D text in the prereg is byte-identical to `BUILD_PLAN.md` on master
  (line 136). RULING 19 Oct evening is present, with point 1 (DEFCON removed
  on both sides). `git diff 161cd69 483a8a6` touches only
  `tests/test_S6f.py`: the tool was not changed after its run.
- `git diff a454e09 483a8a6 --name-only`: `tests/test_S6f.py`,
  `tools/xp_v2_2425.py` only. PASS.

## Check 1: point-in-time leak check

**1a Truncation test (decides): PASS.** For t = 5, 21, 38 I built a
truncated 2024-25 folder in scratch: `merged_gw.csv` with rows round <= t
only, every performance column of the round-t rows overwritten with 7
(minutes, starts, points, goals, assists, bonus, bps, xG, xA, ICT, scores,
transfers...); `fixtures.csv` with event > t scores blanked and the round-t
scores perturbed (+5/+7); the odds file cut at the last round-t match date;
the 2023-24 prior folder untouched. Rebuilt `Replay.xp_v2(t)`,
`own_rebuilt(t)`, `own_proxy(t)` and P(start) from it and compared with the
full-season values: max |difference| 0.0 for all four at every t (same key
sets: 324/337/332 own_proxy forecasts etc.), the 50 squads identical, and the
per-gameweek primary difference identical (+0.3800, -2.3600, -0.3600). The
rebuildable range ends at t in each truncated copy (`through` = t), so
nothing after round t existed to leak.

**1b Timestamp audit (decides): PASS.** For every g in 5..38, every
`merged_gw.csv` row with round < g and every fixture with event < g kicked
off before g's first kickoff (the deadline proxy; the real deadline is 90
min earlier): 0 late rows, 0 late fixtures. S5's fallback uses results with
kickoff date < the round's first kickoff (`fit_fallback`). Odds rows are
matched to their own match date (+-1 day); none later. All 380 odds rows
come from the `Avg*` pre-closing columns (no closing column exists in the
loader, `PRE_CLOSING`). The prior season's last kickoff is 2024-05-19, before
the first 2024/25 kickoff 2024-08-16. The 2026/27 positions and game_config
feed only the re-score (outcomes).

**1c Shift probe (warns only): WARN condition triggered, cleared by 1a and
1b.** Pooled over GW5-37 among forecast starters (P(start) >= 0.8, in both
forecasts) with 60+ minutes in g and g+1, n = 2803, re-scored points:
xp_v2 Spearman unshifted 0.2922, shifted (target g+1) 0.1888, difference
+0.1034; own_rebuilt 0.1509 / 0.0912, difference +0.0597. xp_v2 is above the
0.25 ceiling and its drop is just above 0.10, so the probe's WARN fires; the
agent file clears a WARN only by 1a and 1b, which both pass with zero
difference. Supporting evidence that it is fixture information, not a leak:
restricted to single-fixture gameweeks (n 2754) 0.2848 -> 0.1810; the
within-gameweek mean over 33 gameweeks 0.2913 -> 0.1850, the same picture.
xp_v2's clean-sheet and xG halves both use odds-implied lambdas for the
target fixture; the 0.15 ceiling and the 0.02-0.06 fixture share were
measured on own-type models without odds. The item's primary metric is a
points difference, not a correlation; the Spearman is a secondary.

## Check 2: clean-checkout test runs: PASS

`git archive` of each commit into scratch, `python -m unittest discover -p
"test*.py"` from that folder (no data):
- a454e09 (base): Ran 692 tests, OK (skipped=10).
- 483a8a6 (head): Ran 698 tests, OK (skipped=10).
The 6 added are `tests/test_S6f.py`'s 6 tests. Matches the implementer's
counts.

## Check 3: re-run of the pre-registered evaluation: PASS

- Through the harness: `python tools/xp_v2_2425.py --test --hist
  C:/GIT/FPL/historical --out <scratch>` (30 s, run.txt commit 483a8a6, 0
  modified tracked files). `rescored_2024-25.csv` SHA-256 49f81e47... equals
  the implementer's. `s6f_2024-25.txt` is identical to the implementer's
  line for line, the only difference being the output path inside the
  re-score note.
- Independently (my own script): I built the GW1 candidates myself from the
  2024-25 `merged_gw.csv` round-1 rows (612 with `selected` > 0, weights =
  `selected`), drew 50 squads with `sample_squads(seed 7)`: identical to the
  tool's squads; each has 15, 2-5-5-3, cost <= 100.0, club cap 3. I then
  looped over 34 gameweeks x 50 squads with my own realised-points function
  (formation enumeration, captain = top projection doubled, FPL autosubs on
  the re-scored minutes): 0 mismatches against the harness over 3 x 1700
  squad-gameweeks. My own percentile bootstrap (B 10000, seed 20261018, 90%):
  primary xp_v2 - own_rebuilt mean -0.396471, CI [-0.864118, +0.044706],
  p 0.1402, n 34, season -13.480; secondary xp_v2 - own_proxy +0.357059
  [+0.177059, +0.547647], season +12.140; own_rebuilt - own_proxy +0.753529
  [+0.268824, +1.271176]; same XI 0.6682, same captain 0.5882. All match the
  implementer's report to 1e-6. Lower bound +0.045 > 0 -> the pre-registered
  bar is FAILED (the recorded result, not a verdict failure). A different
  bootstrap seed (1) gives [-0.860, +0.053]: the FAIL is not a seed artefact.

## Check 4: metric, filter, bootstrap, threshold as pre-registered: PASS

Prereg: GW5-38, 50 squads seed 7 from 2024/25 GW1 ownership, realised points
with rule_autosubs and the captain doubled, primary = per-gameweek squad mean
of (xp_v2 - own_rebuilt), bootstrap unit gameweek B 10000 seed 20261018 90%,
pass iff lower bound > 0, priors 2023/24, odds E0 2024-25 pre-closing,
starters by P(start) >= 0.8. The tool: `FIRST, LAST = 5, 38`;
`CH.N_SQUADS 50`, `CH.SQUAD_SEED 7`; `XR.SEED = BT.SEED = 20261018`, `BT.B
10000`, `BT.CI 0.90`; `"pass": c["boot"]["lo"] > 0` (S6c's bound, never
S6b's); `BT.STARTER_P 0.8`; `PRIOR = "2023-24"`. No metric promoted and no
re-tuning after the result: the run's `run.txt` names commit 161cd69 with 0
modified tracked files, and the later commit changed only the tests.

## Check 5: recording path: PASS (offline item)

The item changes no runner file: `fpl_edge.py`, `fpl_sync.py`,
`fpl_nightly.py`, `fpl_ship.py`, `fpl_publish.py`, `fpl_gate.py`,
`checks.py`, `fpl_hist.py` and `.github/` are byte-identical between
a454e09 and 483a8a6. The nightly's imports (`fpl_ship`, `checks`) import
nothing under `tools/`; the suite's existing tests
(`tests/test_S3.py::test_the_nightly_imports_nothing_under_tools_or_analysis`,
`tests/test_S4.py::test_nightly_imports_nothing_under_tools_or_analysis`)
pass at head, and `test_S6f.py` asserts no root module names `xp_v2_2425`.
I did not run `--record` (the runner is the only writer; data lives on the
`data` branch); with the recording code unchanged byte for byte there is
nothing that could move the projection log.

## Check 6: mutation spot-check: PASS

On a scratch `git archive` of 483a8a6, each mutation applied alone to
`tools/xp_v2_2425.py`, `python -m unittest tests.test_S6f`, then restored
(green again): alias not applied RED; alias not restored RED; counts not
checked RED; re-score unchecked RED; flag not checked RED; DEFCON points not
checked RED; bar on S6b's bound RED; bar at >= 0 RED; prior season = season
RED; window shifted (test_s6c first+1) RED; squad count ignored RED;
own_rebuilt note unlabelled RED; different squads accepted RED; label not
converted RED; missing input returns 0 RED; primary line prints S6b's mean
RED. One of my own stayed GREEN: the per-gameweek `v2-prx` display column
read from S6c's `diff` instead of S6b's (information-only column; the S6b
bootstrap line, which is what the prereg lists, is tested). 16 of 17 red.

## Check 7: secrets: PASS

`tools/xp_v2_2425.py` and `tests/test_S6f.py` contain no API key, no URL
with `apiKey=`, no Authorization or Bearer value, no `ODDS_API_KEY`
reference. The odds file is S10b's (commit 5918f02), not this item's.

## The main session's six questions

1. **Drivers unchanged, inputs point-in-time: PASS.** `run()` calls
   `XR.test_s6c` and `XR.test_2526` with `hist_dir` 2024-25, `prior_dir`
   2023-24, the 2024-25 odds file, S10b's re-score (`R.normalise_season`,
   bonus official, DEFCON flagged), first 5, last 38, 50 squads, seed 7,
   bootstrap seed 20261018, and prints its own 2024/25-labelled report from
   their returned records. `tools/xp_v2_replay.py` and every other harness
   file are unchanged from the base. Squads from 2024/25 GW1 ownership and
   rounds < t: confirmed independently (check 3 and check 1a).
2. **DEFCON removed on both sides: PASS for the primary, with one note.**
   The re-score: 26,919 rows, every row `DEFCON missing`, every
   `defensive_contribution` 0 (the tool's `check_rescored` passes; my own
   read agrees). The 2024-25 `merged_gw.csv` has no defensive-action column
   (27,605 rows, 0 such columns). At origins 5, 21, 38: xp_v2's hit-rate
   term is 0.0 for every player (242/344/392), `detail["defcon"]` max 0.0;
   canonical defcon sum 0.0; `defcon90` inputs {0.0, None}; the positional
   defcon90 priors all 0.0; the reliability weight 0.0. own_rebuilt's term is
   `p.get("_defcon_pts", 0.0) * p_start` and the players it builds carry no
   `_defcon_pts`: exactly 0. **Note:** own_proxy (S6b's secondary comparator,
   `project_reliability`) models DEFCON as a logistic, `2 / (1 + exp(-(dc -
   thr) / 2)) * P(start)`; with dc = 0 that is a floor of 0.01339 x P(start)
   per DEF fixture and 0.00494 per MID fixture, not 0 (max 0.0268 on a
   double). Its effect, measured: 2 of 1700 XIs and 5 of 1700 captains
   change; the secondary xp_v2 - own_proxy is +0.357 [+0.177, +0.548] with
   the floor and +0.373 [+0.187, +0.568] without. The primary is untouched.
   The prereg's sentence "bottomup's defcon90 inside own_proxy ... 0" is true
   of the input; "both forecasts' DEFCON terms are 0" is exactly true for the
   two sides of the primary only. Worth one line in the report/CHANGELOG.
3. **The two adaptations: PASS.** S5's table alone refuses the 2024/25 odds
   file (`team 'Ipswich' is not in the team table`, 2024-25 `teams.csv`
   names it "Ipswich"); with `season_names("2024-25")` all 380 rows load for
   20 clubs; `OL.FD_ALIASES` is the original dict after the context, after
   the Replay construction and after the tool's run ("Ipswich" -> "Ipswich
   Town" again). Ruleset label: `ruleset` is read only by
   `fpl_edge.one_ruleset` (a mixing refusal inside `measure_reliability`);
   I wrapped `BT.load_2526` to relabel every row "2024-25" and rebuilt the
   Replay: xp_v2, own_rebuilt and own_proxy equal at t = 5, 21, 38.
4. **Primary re-run: PASS**, see check 3: -0.396471 [-0.864118, +0.044706],
   FAIL on the bar, reproduced with my own loop, realised function and
   bootstrap.
5. **Tests: PASS.** 6 tests in `tests/test_S6f.py`; suite 692 OK (10
   skipped) -> 698 OK (10 skipped) on clean archives; 16 of 17 of my
   mutations red (check 6).
6. **Provenance and hygiene: PASS.** The worktree's `run.txt`: commit
   161cd69, 0 modified tracked files, the two outputs' SHA-256; mine the
   same CSV hash. Every input file's SHA-256 matches
   `worklog/downloads_2026-10-19b.md` (2024-25 merged_gw 5bbb..., teams
   d10a..., players_raw 7568..., 2023-24 merged_gw e9c0..., teams 7795...,
   players_raw 43d8..., E0 2024-25 d0c8...) and the morning record for
   fixtures (2024-25 ce69..., 2023-24 d852...). No runner file changed, the
   nightly imports nothing new, no secrets, nothing tuned after the result.
   `git status` in the worktree was clean before this file.

## Findings for the chat (none blocks the verdict)

- own_proxy's DEFCON logistic floor (point 2 above): a secondary-only
  deviation of up to 0.013 points per DEF start; state it in the report.
- Shift probe WARN on xp_v2 (0.29 pooled Spearman, drop 0.10), cleared by
  the zero-difference truncation test and the clean timestamp audit; the
  odds-implied fixture terms explain it.
- The `v2-prx` per-gameweek column is not covered by a test (display only).

VERDICT: PASS

Reason: the prereg was committed before any code and its F-D text matches
BUILD_PLAN.md; the tool calls S6b's and S6c's drivers unchanged on 2024/25
with the pre-registered squads, window, metric, bootstrap and bar, and my
independent loop (own squads build, own realised-points function, own
bootstrap) reproduces every number in the implementer's report to 1e-6,
confirming the recorded FAIL on the bar (-0.396, 90% CI [-0.864, +0.045]);
the truncation test at GW5/21/38 rebuilds every forecast with zero
difference after round-t outcomes are perturbed and later data removed, the
timestamp audit finds no late row, and the shift probe's WARN is thereby
cleared; DEFCON is exactly 0 on both sides of the primary (the secondary's
own_proxy keeps a 0.013-point logistic floor, measured as immaterial and
noted); the alias is applied only inside the construction and restored, the
ruleset relabel moves no number; the suite goes 692 -> 698 OK on clean
archives, 16 of 17 mutations go red, no runner file or secret is touched,
and the input hashes match the download record.
