# Verifier report: S6e2 (xp_v2 + discretised save points, tested on 2024/25)

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high
(`.claude/agents/backtest-verifier.md` read from disk first; it matches the
loaded instructions). Date 2026-10-19.

Scope: branch `s6e2-wip` in the scratch worktree, HEAD `d80644c`; base
`3f666d8` (s6f-wip with s6e-wip merged). Code `639a11a`
(`tools/xp_v2_saves2.py`), tests `d80644c` (`tests/test_S6e2.py`). Prereg on
master `f485223:prereg/S6e2.md`. Inputs read only:
`C:/GIT/FPL/historical/{2024-25,2023-24,2026-27}` and the worktree's tracked
`tools/odds/E0_2024-25_fetched_2026-10-19.csv`. All my scratch work lives in
`C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-.../scratchpad/verify_s6e2/`
(`check.py`, `mutate.py`, their logs, the regenerated run and three truncated
input copies). Nothing outside this file was written in the worktree or in
`C:\GIT\FPL`. No key-like string occurs in anything the item adds; hashes
below are shown masked anyway (first 4 characters, "...").

## Prereg before code: PASS

`f485223` (prereg, 2026-10-19 22:28:31 +0200) precedes `639a11a` (code,
22:31:25) and `d80644c` (tests, 22:33:44). The prereg holds RULING 19 Oct
evening verbatim (point 2 quoted at the top and the whole ruling at the end).
The code commit's message names the prereg commit. `git diff --stat 639a11a
d80644c` touches only `tests/test_S6e2.py`: no code changed after the result
was seen.

## Check 1: point-in-time leak check

### 1a Truncation test (decides): PASS

For t = 5, 21, 38, inputs rebuilt at file level in a scratch copy of
`historical/` (the S6e verifier's design, now on 2024/25): every
`2024-25/merged_gw.csv` row of round >= t junked in its outcome columns
(minutes 90, starts 1, saves 99, points 50, goals/assists/bonus 9, ICT 99,
xG/xA 9.00, scores 9-9; identity columns kept), `fixtures.csv` with every
fixture of event >= t scored 9-9, the odds file with every row the book would
match to a fixture of event > t removed (round t's own pre-closing odds kept,
as S5 designs), the 2023/24 prior untouched, the re-scored file with every
round != t lifted by 1000 points. Then `Season2.forecasts(t)` and the whole
per-gameweek record (`test_2526(first=t, last=t)` under `discretised()`)
from the truncated inputs against the untruncated:

| t | rows junked | odds rows removed / kept | fixtures priced by odds | max abs diff xp_v2 (n) | xp_v2 + pts | E[saves] (n GK) | per-GW record (diff, base, plus, differ, n GK, MAE v2, MAE +pt) | k |
|---|---|---|---|---|---|---|---|---|
| 5 | 25,055 | 330 / 50 | 10 of 10 | 0.0 (324) | 0.0 | 0.0 (27) | 0.0 | identical |
| 21 | 14,151 | 171 / 209 | 10 of 10 | 0.0 (337) | 0.0 | 0.0 (27) | 0.0 | identical |
| 38 | 804 | 0 / 380 | 10 of 10 | 0.0 (332) | 0.0 | 0.0 (24) | 0.0 | identical |

Key sets identical; nothing of round >= t, no later odds row and no other
round of the re-scored file reaches origin t (bar 1e-9; observed 0.0).

### 1b Timestamp audit (decides): PASS

Over every origin t = 5..38 (2024/25 has no recorded deadlines; the
harness's cut is round t's first kickoff, `Season2526.deadline(t)`, checked
equal to the fixtures' minimum per event):
- rows of rounds < t used at origin t (`keeper_rates` reads `range(1, t)`;
  `canonical_through(c, t-1)`) with kickoff at or after the cut: 0 of
  482,696 row-uses;
- the fallback's results of event < t kicking off at or after the cut: 0;
  and no fixture used the fallback: 340 of 340 round fixtures GW5-38 are
  priced by odds, every matched odds row dated the same day as the kickoff
  (380 of 380 fixtures: date offset {0 days: 380});
- k and the priors come from 2023/24, last kickoff 2024-05-19 15:00 UTC,
  before 2024/25 round 1 (2024-08-16 19:00 UTC); k from the prior folder is
  17.402 (r 0.371, 37 keepers); for contrast, 2024/25's own split-half would
  give 33.325, so the pinned rule (not the test season's own k) was used;
- 2026/27 inputs used only as a rule table and position map for the
  re-score (`game_config.json`, `elements_positions.csv`);
- the tool contains no reference to 2025/26 (grep "2025": none); SEASON,
  PRIOR and ODDS are S6f's constants (2024-25, 2023-24, the 2024/25 odds
  file).

### 1c Shift probe (warns only): no WARN

The primary is a keeper-choice difference and the secondary an MAE, not a
correlation. For information, pooled over GW5-37 among goalkeepers with a
forecast and 60+ re-scored minutes in g and g+1 (n = 544): xp_v2 + save
points Spearman +0.030 unshifted, +0.020 shifted; xp_v2 +0.072 / +0.064.
Both far under 0.25 and the differences under 0.10.

## Check 2: clean-checkout test run: PASS

`git archive` of each commit into a fresh folder, `FPL_DATA_DIR` unset,
`python -m unittest discover -p "test*.py"`:
- `3f666d8` (base): Ran 703 tests in 273.5 s, OK (skipped=10);
- `d80644c` (item): Ran 708 tests in 276.1 s, OK (skipped=10).
Exactly the implementer's counts; the 5 new tests are `tests/test_S6e2.py`.

## Check 3: re-run through the harness: PASS

`python tools/xp_v2_saves2.py --test --hist C:/GIT/FPL/historical --out
<my folder>` in the worktree: the report is identical to the real run's
`tools/out/xp_v2_saves2/s6e2_2024-25.txt` except the re-score note's output
path; `rescored_2024-25.csv` sha256 `49f8...` on both sides. Numbers:
primary +0.024 per squad per gameweek, 90% CI [-0.016, +0.066] (n = 34,
p = 0.3200), season +0.8; MAE +0.305 [+0.254, +0.355]; choice differs 0.05;
mean E[floor(S/3)] 0.767 against E[S]/3 1.100 over 846 keeper forecasts;
k 17.402 (r 0.371, 37 keepers); bar FAIL. Differences from the
implementer's: 0.0 (well within 1e-6).

## Check 4: prereg compliance: PASS

Read side by side with `f485223:prereg/S6e2.md`:
- model: for keepers `xp_v2 + P(start) x sum over fixtures f of
  E[floor(S_f/3)]`, `S_f ~ Poisson(mu_f)`, `mu_f` = S6e's `expected_saves`
  on that one fixture (`[f["lam_opp"]]`, S6e's `keeper_rates`, `lam_bar`
  over both sides of every fixture, `pos_mean_start`), `floor_points` = sum
  over j >= 1 of P(S >= 3j) with a 1e-15 tail constant; k by S6e's
  `saves_k` on the prior folder's keepers (2023/24): as pinned;
- sample: 2024/25 GW5-38 (`XR.FIRST, XR.LAST`), S6f's harness
  (`F.season_names("2024-25")`, `F.rescore` with `check_rescored`,
  `F.check_no_counts`), starters P(start) >= 0.8 for the MAE
  (`SV.STARTER_P` = `BT.STARTER_P` = 0.8): as pinned;
- comparison: S6e's `test_2526` loop called unchanged (the only change is
  `SV.Season` swapped for `Season2` inside `discretised()`, restored in
  `finally`), S7's 50 squads (seed 7, `CH.N_SQUADS`, `CH.SQUAD_SEED`),
  `choose_keeper` / `keeper_points` with the keeper substitution: as pinned;
- primary: per gameweek, the mean over squads of keeper points (plus minus
  base); bootstrap unit gameweek, `BT.B` = 10,000, seed `BT.SEED` =
  20261018, `BT.CI` 90%; bar `boot["lo"] > 0`: as pinned;
- secondary: MAE, share differing, mean E[floor(S/3)] against E[S]/3: as
  pinned, reported as information only.
No metric was promoted and nothing was re-tuned after the result (the only
later commit is the tests file). The code reads the prior season's k from
`prior_dir` via S6e's `Season.__init__`, unchanged.

Independent re-run of the primary (my own keeper choice and points, from
`Season2.forecasts` and my own reading of the re-scored CSV, my own
bootstrap with the same rule): per-gameweek diffs, differ shares and MAEs
equal the harness's to 0.0 for all 34 gameweeks; primary +0.024118
[-0.016471, +0.066471], p 0.3200, season +0.820; MAE +0.305287
[+0.254105, +0.355450]; differ 0.0500. The FAIL on the bar stands.

## The item's own checks (the main session's list)

1. `floor_points` against my own computation: PASS on values, with a
   defect in the tail stop (below). Against a direct sum
   `sum_k floor(k/3) P(S=k)` in log space (2,000 terms) and a survival sum
   with my own stricter stop, at mu in {0, 1e-9, 0.05, 0.3, 0.9, 1.2, 2.0,
   2.999, 3.0, 3.001, 4.7, 9.0, 12.0, 25.0, 60.0}: worst absolute
   difference 5.4e-12 (the direct sum's own rounding at mu 25-60; at
   mu <= 12 the agreement is 1e-14 or better). mu <= 0 gives 0.0; per = 1
   gives the mean (5.0). Within the run's domain the tail stop loses
   nothing (the 1e-9 case drops 1.7e-28).
   **Defect (not reached by the run):** the loop stops only when
   `1 - cdf < 1e-15`; once the pmf has underflowed to 0 the accumulated
   `cdf` is frozen and, for many mu, sits at 1 - (1 to 3)e-15 by rounding,
   so the stop is never met and the function never returns.
   `floor_points(120.0)` did not return within 20 s (subprocess timeout);
   a guarded replica of the loop finds 346 non-terminating mu values in
   [0.001, 40] at step 0.001, the smallest 12.765 (then 13.818, 14.592,
   16.173, ...), and 81 of the integers 41..399 (57, 68, 76, 82, 96, 105,
   114, 118, 120, ...). The item's test goes to mu = 60, which happens to
   terminate. In the real run the largest per-fixture mu_f is 8.4337 and 0
   of the 846 x fixtures values are >= 12.765, so the measured result is
   unaffected; an expected-saves value above 12.7 in one fixture is
   outside anything the model produces on these seasons, but the
   function's contract is unconditional and the formula is the item's core.
2. `Season2.forecasts` v S6e's `Season.forecasts` on the real 2024/25
   inputs, every origin 5..38: xp, E[saves], P(start) and pos identical
   (`==`, not approximately); non-keepers unchanged (10,278 forecasts);
   846 keeper forecasts (11 in a double gameweek, 0 blank); per-fixture
   mu_f rebuilt by me from `club_fixtures` and `lam_opp` sum to S6e's
   E[saves] and `plus2 = xp + P(start) x sum of my direct floors` to
   5.8e-15; every keeper's discretised term is below S6e's E[S]/3 term;
   my mean E[floor] 0.767 against E[S]/3 1.100 over 846 reproduces the
   report's secondary. Code diff: `forecasts` is S6e's line for line
   except the keeper term (per-fixture `expected_saves`, `floor_points`
   summed, `p_start` multiplied) and the `sizes` record. PASS.
3. The loop is S6e's `test_2526`, called unchanged with `SV.Season`
   swapped inside `discretised()` (try/finally; `SV.Season is not
   T.Season2` after my runs and after a raised exception); exactly one
   `Season2` instance is demanded; k from 2023/24 (17.402, not 2024/25's
   33.325); 2024/25 only; squads, outcomes and bootstrap as S6e/S6f (check
   4); every input point-in-time (check 1). PASS.
4. Independent primary: above; FAIL on the bar confirmed. PASS.
5. Tests: 5 in `tests/test_S6e2.py`; suite 703 -> 708, 10 skipped both
   sides (check 2). My own 15 mutations of `tools/xp_v2_saves2.py` in the
   clean `d80644c` export, `tests/test_S6e2.py` after each, the file
   restored and shown unmutated (OK) at the end: 14 red (no floor; one
   floor of the sum; P(start) dropped; tail 1e-3; Season not restored;
   Season2 never used; k from the test season; bar wording swapped; the
   2024/25 names not applied; per = 2; keeper gate on DEF; last gameweek
   dropped; counts unchecked; tail loop off by one). 1 survived: recording
   `sizes` as (E[S], pts) instead of (E[S]/3, pts), which feeds only the
   report's secondary "E[S]/3" figure (the test asserts b < a, true for
   both); information only, and my own recomputation gives the reported
   1.100. PASS, with that gap noted.
6. Provenance `run.txt`: tool, args, commit `639a11a`, 0 modified tracked
   files, start/end UTC (12 s), outputs with sha256 (`49f8...` for the
   re-score, `f0cb...` for the report; both recomputed by me and equal).
   No runner file changed (`git diff --name-only 3f666d8 d80644c`: the two
   files only); nothing tuned after the result; no secrets. PASS.

## Check 5: recording path: PASS

Offline item: the two changed files are `tools/xp_v2_saves2.py` and
`tests/test_S6e2.py`. The tool never reads `FPL_DATA_DIR`,
`projection_log.csv` or `C:\GIT\FPL-data` (grep: no hit) and has no record
path; `.github/workflows/nightly.yml` runs `fpl_nightly.py` only; importing
`fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish` in the
clean `d80644c` export loads nothing under `tools/` and none of
`xp_v2_saves2`, `xp_v2_saves`, `xp_v2_2425` (the item's isolation test and
my own probe). The projection log cannot have moved: no file on the
recording path changed, and `--record` is never run locally by rule.

## Check 6: mutation spot-check: PASS

Above (item 5): 14 of 15 of my mutations red; the implementer's claim of
11 of 11 red is consistent with what the tests catch.

## Check 7: secrets: PASS

`grep -Ei 'apikey=|authorization|api_key|bearer |[a-f0-9]{32}'` over the two
added files and `f485223:prereg/S6e2.md`: no hit. The odds file is named by
season and fetch date, no key.

## Write guard

`git status --short` in the worktree before writing this file: empty
(`tools/out/` is gitignored). After: only `worklog/verify_S6e2.md`,
untracked.

## VERDICT: WARN

The item was done as pre-registered and its recorded result is right: the
prereg with the ruling verbatim precedes the code; `Season2` reproduces
S6e's xp, E[saves] and P(start) exactly and adds per-fixture
E[floor(S/3)] x P(start) as pinned; k is 2023/24's; the harness is S6f's
2024/25 one with S6e's loop unchanged; the truncation test at GW5/21/38 and
the timestamp audit over all 34 origins find no leak; my independent re-run
reproduces the primary to 0.0 (+0.024 [-0.016, +0.066], p 0.320, FAIL on
the bar, as recorded); the suite is 703 -> 708 OK; 14 of 15 of my mutations
go red; no runner file, no secret. The WARN is for one defect in the new
logic that the run never reached but that the tests do not exclude:
`floor_points` loops forever for mu values from 12.765 upward
(`floor_points(120.0)` does not return; 346 such values below 40), because
its stop compares a rounding-frozen `1 - cdf` to 1e-15; the run's largest
per-fixture mu is 8.43, so no number in the report is affected. Before this
code is reused or adopted, the stop should also end when the pmf has
underflowed (or bound j), with a test at mu = 120.0 and at 12.765; that is a
code change and a re-verification, which the recorded FAIL does not need.
