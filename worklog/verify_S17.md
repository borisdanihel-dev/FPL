# verify_S17.md — the mini-league win simulator (Part F, F-H)

Verifier: the backtest-verifier agent, model **Fable 5.1** (claude-fable-5-1), effort high, instructions
read from `.claude/agents/backtest-verifier.md` on disk (identical to the loaded ones). Date 2026-10-20.

Scope: branch `s17-wip` at **e17c5e5** (base fef1edc). Code `tools/league_sim.py` (011b072, e17c5e5),
tests `tests/test_S17.py` (6958980, e17c5e5). Prereg on master `07c3fff:prereg/S17.md`. Inputs read-only:
`C:/GIT/FPL/historical` (2025-26, 2024-25, 2026-27), `tools/odds/E0_2025-26_fetched_2026-10-18.csv`.
Nothing written outside this file and my scratch folder (`.../scratchpad/verify_s17/`); `git status` of the
worktree is clean (tools/out/ is ignored).

## Prereg ordering
- `prereg/S17.md` committed on master at 07c3fff, **2026-10-20 08:56:35 +0200**; first S17 code commit
  011b072 at **09:01:00 +0200**. Prereg first: PASS.
- The F-H paragraph in the prereg is verbatim BUILD_PLAN.md line 144; the night ruling block (2,205 chars) is
  identical to the copy in `prereg/S15.md`. Both rulings present: check 4's "ruling not there" does not apply.

## Check 1 — point-in-time (decides)
**1a Truncation (file level), PASS.** For each origin T in {20, 26, 32} I copied `historical/` and junked every
2025-26 `merged_gw.csv` row with round >= T (minutes 90, starts 1, total_points 30, xG 3.0, bonus 3, ICT 99.9,
DEFCON 99, value 999, selected 1, ...; 15,572 / 10,757 / 5,918 rows) and every `fixtures.csv` row with
event >= T (score 9-0, stats blank; 190 / 130 / 71 fixtures), then rebuilt `SimSeason` on the junk root
(the clean re-score passed in, since the outcomes are the truth). Compared with the clean run by `==` on the
float dicts (tolerance 0, i.e. well inside 1e-9):
- `horizon(T, 38)` (the xp_v2 matrix and every Step 14 PMF for weeks T..38): **identical** at T = 20, 26, 32.
- `point_in_time(u)` for every u < T (the truth's choices feeding the base): identical.
- the base totals GW2..T-1 for all 2,000 managers: identical; GW1 candidates and the 200 leagues: identical.
- The junk was live: round T's loaded rows carry it, and `horizon(T+1)` on the junk root differs from the
  clean one (so a leak would have shown). One sub-check of my script printed "sources identical False" at
  T = 20 and 26; I traced it to my own comparison: the clean season had also logged the truth's
  `forecasts(T)` sources (weeks T..T+5), each present in `horizon(T)` with the same source — an artefact, not
  a leak (T = 32 compared True because my clean pass stopped at GW31).
Script and output: `scratchpad/verify_s17/verify_truncate.py`, `trunc/truncate.txt`.

**1b Timestamp audit, PASS.** All inputs are round-indexed: `XL.core` reads rounds < t (sub inputs, ICT
percentile, DEFCON rates, S11 sums over `set(range(1, t))`), `reliability_inputs` on `canonical_through(c,
t-1)`, the sub PMFs and bonus table from rounds < T. Lambdas: week T = S5's `lambdas(T)` (pre-match odds of
the football-data file for round T's fixtures: priced 10/10, 11/11, 10/10 at the three origins); later weeks =
the fallback fitted on results of rounds < T, cut at round T's first kickoff (2026-01-03 12:30Z,
2026-02-10 19:30Z, 2026-04-10 19:00Z); fixtures of rounds < T kicking off at/after the cut: 0 at every origin.
Squads use GW1 `value`/`selected`; priors are 2024/25. The fixture *schedule* for weeks > T is the final one
(rescheduled fixtures are placed where they ended up) — the replay limitation shared with S8b/S15, not new.

**1c Shift probe:** not applicable (no correlation metric on points).

## Check 2 — clean-checkout suites (git archive copies, discovery `-p "test*.py"`, no FPL_DATA_DIR)
- fef1edc (before): **Ran 723 tests, OK (skipped=10)**, 354 s.
- e17c5e5 (after): **Ran 732 tests, OK (skipped=10)**, 360 s. +9 = `tests/test_S17.py` (ByHand 2, Styles 1,
  Chips 1, Toy 3, Live 1, Isolation 1).

## Check 3 — the pre-registered evaluation re-run and recomputed
**Re-run through the harness** (`python tools/league_sim.py --test --hist C:/GIT/FPL/historical --out
<scratch>/run1`, from the worktree at e17c5e5, 207 s): the output is identical to the implementer's
`tools/out/league_sim/league_sim_test.txt` except the re-score note's output-folder path (the only diff line).
Every number matches exactly: skill **+0.0839**, CI **[-0.0219, +0.1685]**, GW20 0.0699/0.0650/-0.075,
GW26 0.0327/0.0430/+0.241, GW32 0.0227/0.0288/+0.209, the ten deciles, "PASS". Implementer's run.txt:
commit e17c5e5, 0 modified tracked files, 194 s, after the last commit (09:05:28 +0200 < 09:09:37 +0200).

**Independent recomputation** (`verify_recompute.py`, my own code for the truth, the simulator and the
metrics; the item's `SimSeason` only to obtain the inputs, which I checked separately — see check "design"):
- Truth: my own best-XI enumeration, FPL autosub rule, captain doubled, on the re-scored outcomes: **0
  differences** from the item's over 2,000 managers x 37 weeks. No tied winner in 200 leagues.
- Choices: my XI/captain v the item's `choice()` on the origin matrices: 0 differences (2,000 x 19/13/7).
- Simulator: my own draw-and-count (different RNG stream, the captain's draw added explicitly, ties split),
  2,000 sims: P(win) v the item's per manager — max |d| 0.038 / 0.045 / 0.038, RMS 0.005 / 0.005 / 0.004 at
  GW20/26/32 (SE of a difference <= 0.016; none beyond 4 SE). Brier/skill per origin: item -0.0751 /
  +0.2405 / +0.2093, mine -0.0736 / +0.2418 / +0.2109.
- Primary: item **+0.0839**; mine +0.0854 (seed 1), +0.0843 (seed 2), +0.0861 (seed 3).
  **Monte Carlo error of the pooled skill: SD 0.0010 over four independent 2,000-sim runs** (mean +0.0849);
  the bar is 34 MC SDs below the estimate. Bootstrap 90% CI over leagues, my implementation of the pinned
  procedure: [-0.0219450, +0.1684927] = the item's to full precision; with my p_win [-0.0197, +0.1698];
  with a different resampler (`random.choices`) [-0.0185, +0.1684].
- 20,000 sims on leagues 0-19: max |P(win) - the item's 2,000-sim| 0.016 (GW20) and 0.012 (GW32),
  RMS 0.003 / 0.002 — consistent with the pinned "MC SE of P(win) <= 0.011".
- Deciles reproduced (top decile 0.862 predicted v 0.728 observed; n = 600 each).
**Judgement:** the numbers are sound and reproducible; the PASS is exactly on the pinned bar (point estimate
>= 0.05). The league-sampling uncertainty is much larger than the MC error: the 90% CI straddles zero and the
GW20 origin is negative (the simulator is overconfident far from the end), so the evidence that the simulator
beats "the current leader wins" is positive but not significant at 90%. Information only, as the prereg says.

## Check 4 — prereg v code (metric, filter, bootstrap, bar), PASS
Pinned -> code: 200 leagues (`N_LEAGUES`), 4/3/3 template/mixed/differential (`STYLES`, weights s, s**0.5,
1/s; the test asserts w(4) = 4, 2, 0.25), seeds 7*100000 + 10 i + j (`leagues`), GW1 prices and 100.0
(`gw1_candidates`, `BUDGET_TENTHS`), fixed squads, no chips; truth GW2-38 (`FIRST_COUNTED = 2`) by
`point_in_time(u)` with S8's `realised` (rule_autosubs, captain doubled); origins (20, 26, 32); base GW2..T-1;
2,000 sims (`N_SIM`), seed 20261018 (`BT.SEED`); P(win) ties split; Brier with won = 1/k; leader baseline with
ties (`leader_p`); skill pooled (sum of squared errors over leagues x origins x managers); bootstrap over
leagues B = 10,000, seed 20261018, 5th/95th percentiles; bar `skill >= 0.05` (`PASS_SKILL`); deciles. No
metric was promoted and nothing was tuned: the simulator has no free parameter; the only post-test change to
`league_sim.py` (6958980 -> e17c5e5) adds `"base": base` to the result record for a test.

Design elements checked on the real data (the launch message's list): `sample_style(identity)` ==
`chips.sample_squads` on the real GW1 candidates (4 seeds); every squad legal (15, quotas, club cap 3, <= 100.0);
`point_in_time(T)` == `xp_v2_replay.Replay.xp_v2(T)` without zeros at T = 20, 26, 32 (336/327/320 players,
max |d| 0); `horizon(T)[1][T]` == `points_pmf.Season.pmfs(T)` exactly, `horizon(T)[0][T]` == its xp_v2; every
PMF sums to 1 (max dev 4e-16) with mean == xp_v2 (max |d| 0.0000); later weeks' sources all "fallback"; the
sub PMFs and bonus table from rounds < T; no autosubs inside `simulate`; one draw per (pid, week) per
simulation (`plan`/`simulate`); the captain's index repeated once (`mult - 1`).

## Check 5 — recording path, PASS (not applicable to the offline path)
`git diff --stat fef1edc e17c5e5`: only `tools/league_sim.py` (+532) and `tests/test_S17.py` (+211). No runner
file changed; the workflow runs only `fpl_nightly.py`/`fpl_publish.py`/`fpl_alert.py`; importing fpl_nightly,
fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish and fpl_alert loads none of league_sim/builder/points_pmf/
planner_2425/xp_v2_*/chips/backtest/odds_lambda/shares (checked in a subprocess: `[]`). The projection log
cannot move; I did not run the runner (it is the only writer).

## Check 6 — mutations (scratch copy of e17c5e5, `python -m unittest tests.test_S17`)
Red (7): ties not split in `simulate`; captain tripled in `plan`; `XL.core` at week u instead of origin t (the
point-in-time test catches it); leader baseline ignoring ties; captain = the lowest-xp XI player; base includes
round T; mixed weight s**0.6. **Survived (3):** the simulation loop skipping week T (`range(T + 1, ...)`);
`simulate` ignoring the base totals; a player-week missing from the matrix drawing 1 instead of 0. (An 11th
mutation of mine was a no-op and is discarded.) The surviving three are test gaps in `test()`'s simulation
loop, not code faults: my independent simulation confirms the week range T..38, the base and the {0: 1.0}
default (the P(win) agreement above). Recommended: a toy assertion on `test()`'s P(win) against a hand value,
or at least on the week range and the base inside `simulate`. The implementer's "12 of 12 red" could not be
re-run from its list (not in the repo); my own set stands as the spot check.

## Check 7 — secrets, PASS
`tools/league_sim.py`, `tests/test_S17.py`, `league_sim_test.txt`, `run.txt` and my live output contain no
API key, no `apiKey=` URL and no Authorization header; the only 32+-char strings are the commit hash and the
SHA-256 of the output. The live output names the snapshot source only ("later weeks odds 10", etc.).

## Live path (information only)
`tests.test_S17.Live` (S6d's toy) passes in the suite. Run read-only against `C:/GIT/FPL-data` (no pull — I
change nothing there; HEAD e1154ddc...) with `--out` in my scratch folder, 64 s: `git status --porcelain` and a
full `ls -la` of the data worktree are identical before and after ("DATA WORKTREE UNCHANGED"). Output: league
455565 GW8-38 from fpl_export_gw7_2026-10-19.json.gz, P(win) us 0.283 (2nd of 7 behind 0.304); dP for the
three captain options +0.000 (a one-week swap of < 0.3 xP moves P(win) by well under 0.001 — plausible); the
three single transfers +0.078 to +0.088 (a season-long upgrade of ~1 xP/week — plausible against the margin
density). The code's only writes are `--out` (the report, run.txt, the re-score CSV). PMF construction mirrors
`points_pmf.live_pmfs`; the lambdas use the Odds API snapshot where it prices the fixture, else the fallback
(the night ruling, point 5).

## Findings to carry into the report / CHANGELOG (none changes the verdict)
1. **The "lambda sources at the origins" line is double counted.** `Season2425.forecasts(u)` (the truth's
   choices) also appends sources with origin u, so for u in {20, 26, 32} the truth's weeks T..T+5 are counted
   again: "week T odds 62" is really 31 fixture-weeks (10 + 11 + 10) and "later weeks fallback 509" is really
   360 (149 duplicates). Information only; the primary is unaffected. Fix the counter (e.g. count only
   `horizon`'s entries) in a follow-up.
2. **The pinned differential style produces non-competitive squads.** Weight 1/selected picks players with mean
   GW1 ownership ~9.7k (template ~1.61M, mixed ~0.86M): mean final total 311 v template 1,571 and mixed 1,292;
   min 13; **0 wins in 600 league-origins** (template 184, mixed 16). As pinned, so not a deviation, but the
   test effectively measures 7 live managers per league and the lowest seven deciles are empty (P ~ 0, won ~ 0)
   for both the simulator and the baseline. Worth stating as a limitation.
3. Players outside the origin's matrix (mins_last4 < 45 or no fixture) draw 0 in the simulation but score
   their real points in the truth when the XI must field them — a limitation not among the prereg's stated
   ones (the "0 of a non-appearance" statement covers a different case).
4. Live chips are restricted to the current half (`HALF_END = 19`) and second-half chips are not modelled;
   the prereg says "best projected week" without the half. Information only.
5. One global draw per player-week per simulation is shared across all 200 leagues (not per league): correct
   for every league's P(win), and it only correlates the leagues' MC noise, which is negligible next to the
   league-sampling spread.
6. The bar is met on the point estimate as pre-registered, with a 90% CI that includes zero and a negative
   GW20 origin; adoption of the simulator for any live decision needs Boris, as the output itself says.

VERDICT: PASS

The prereg was committed before any S17 code and the code does what it pins: S7's sampler with the three style
weights, the truth by S6b's point-in-time xp_v2 (equal to `xp_v2_replay` at every origin) with S8's realised
on the re-score, the origin matrices and Step 14 PMFs (equal to `points_pmf.Season.pmfs` at T), shared draws
with the captain twice, 2,000 sims at seed 20261018, P(win) and Brier with ties, the leader baseline, the pooled
skill with a 10,000-resample bootstrap over leagues and the deciles. File-level truncation at GW20/26/32 leaves
the horizon, the choices and the base bit-identical and the timestamp audit finds no row at or after the cut;
the re-run reproduces every number and my independent truth/simulator/metrics agree within a Monte Carlo
error of 0.001 on the skill (+0.0849 +/- 0.0010 v +0.0839); suites go 723 -> 732 OK; 7 of 10 mutations red
(three test gaps in the simulation loop, covered here by the recomputation); no runner file, no secret.
PASS on the pre-registered bar (skill >= 0.05), noting that the 90% CI over leagues straddles zero and that the
pinned differential style yields dead squads — both to be recorded, neither a violation.
