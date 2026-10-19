# verify_S8 — rolling-horizon transfer planner (tools/planner.py)

Verifier: Claude Fable 5.1 (claude-fable-5-1), effort high, run natively as
`backtest-verifier` with the agent file read from disk first (it matched the
loaded instructions). Repository `C:\GIT\FPL-b`, branch `lane-b`. Date
2026-10-19, 03:40-08:00 local. Nothing outside this file was written in the
repository; every scratch file lives in the session scratchpad. The data
worktree `C:\GIT\FPL-data` was read only.

Prereg: `prereg/S8.md` at `de7e1b3` (2026-10-19 01:13:44 +0200), untouched by
any later commit (`git diff de7e1b3..HEAD -- prereg/S8.md` is empty). Code:
`51520ef` (01:22:46), `7f8ba52` (01:24:16), `22a179c` (01:24:50). The prereg
precedes the first code commit. The results commit is `65b9232` (03:44:03);
the implementer's replay files are dated 03:42. The RULING Step 8 text is in
the prereg verbatim (points 1-5, "END RULING").

**Headline.** The planner as committed is point-in-time clean, matches the
prereg's definitions (one index ambiguity flagged), and the tests pass; but
the replay result recorded in the report and the CHANGELOG (+7.68, 90% CI
[-6.58, +22.06], planner 1919.5) is not the final code's result. My replay
of `22a179c` gives **+2.90, 90% CI [-12.74, +18.40], planner 1914.7 (12.58
hits, 49.5 transfers)**, baseline identical (1911.8, 36.98 transfers). The
cause: the first code commit's candidate generator skipped every pair of
swaps with `o1["id"] > o2["id"]`, which drops 30-45% of the distinct
two-transfer squads (every cross-position pair whose earlier-position
outgoing player has the higher id), so `51520ef` was not exhaustive; the
fix in `7f8ba52` was called score-neutral but is not, and the "run2 on the
final code, byte-identical to run1" claim cannot hold (details in check 3).
The bar is failed under both sets of numbers, so no decision moves; the
recorded measurement is wrong.

## Check 1 — point-in-time leak check

### 1a Truncation test (decides) — PASS

Scratchpad `trunc_1a.py`, origins 2 (earliest), 20 (middle), 38 (latest).
For each origin t a copy of `historical/2025-26` was written in which every
numeric outcome cell of every `merged_gw.csv` row with round >= t and the
scores of every `fixtures.csv` row with event >= t were replaced by random
numbers (identity and pairing columns kept: element, round, fixture, team,
was_home, opponent_team, kickoff_time, position; the origin round's `value`
kept because the prereg defines the market as "prices of the origin round";
later rounds' `value` garbled). Cells garbled: 1,019,159 (t=2), 545,560
(t=20), 28,664 (t=38). On the original and the garbled copy, for the first 3
of S7's 50 squads (seed 7) and k = 1 and 2 banked transfers:

| origin | forecast values (week, player) | max abs diff forecasts / P(start) | market rows equal | ranked candidates (squad 0..2, k=1 / k=2) | order and scores | baseline plan |
|---|---|---|---|---|---|---|
| 2 | 1,320 over GW2-7 | 0.0 / 0.0 | yes (705) | 17,220/37,107; 12,640/46,959; 14,156/21,168 | same order, max abs score diff 0.0 | equal |
| 20 | 1,920 over GW20-25 | 0.0 / 0.0 | yes (790) | 20,498/44,670; 15,013/45,789; 11,224/21,235 | same order, max abs score diff 0.0 | equal |
| 38 | 321 over GW38 | 0.0 / 0.0 | yes (841) | 323/43,837; 292/44,885; 76/21,561 | same order, max abs score diff 0.0 | equal |

Worst absolute difference over everything compared: 0.0 (bar 1e-9). The
chosen plan at each origin is the same with every round >= t garbled (e.g.
origin 20 squad 0: outs (5, 381) ins (417, 683), score 36.250326 both ways).

Live path: `python tools/planner.py --out <scratch>` on the newest dated
export reproduces the implementer's `tools/out/planner_live.txt`
byte-identically (diff empty); its inputs are one export and the projection
log, both dated before the GW8 deadline (1b).

### 1b Timestamp audit (decides) — PASS

Replay: `fpl_edge.canonical_through` was instrumented in the 1a script. At
every origin it was called with gw = t-1, and the slice it returned had its
newest training row and newest team match at event t-1 (recorded as
(1, 38, 1, 1), (19, 38, 19, 19), (37, 38, 37, 37) = (gw asked, newest row
offered, newest row kept, newest team match kept)). `reliability_inputs` is
built from that slice with `gws_played = t-1`; P(start) and positions come
from the same inputs; clubs from `hist_pit.club_at(cm, pid, t)` (rounds <= t,
pre-registered); prices from the round-t `value` column via `price_at`
(rounds <= t). Rows of round >= t reach the origin-t decision only through
(i) the fixture pairings of weeks t..t+5 (`team_matches`, the fixture list the
prereg declares "known in advance", as in S7) and (ii) the round-t `value`
(the prereg's "prices of the origin round"). Realised points (`actual[t]`,
points and minutes) are read in `Replay.realised` only, which the replay loop
calls after the plan is applied; nothing in `rank_plans`, `evaluate`,
`build_pool`, `baseline_plan` or `market` touches `actual` (grep "actual" in
tools/planner.py hits lines 331-341 only).

Stated limitation (pre-registered, shared by planner and baseline): the
vaastav `value` of round t is the price as scraped for that round; a price
change between the deadline and the scrape would be visible. Across 2025/26
a player's value differs from his previous round's in 2,087 of 28,088
player-rounds (7.4%), so the exposure is small and symmetric.

Live: export `fpl_export_gw7_2026-10-18.json.gz`, `generated`
2026-10-18T21:58:06+00:00; GW8 `deadline_time` 2026-10-23T17:30:00Z. The
rows `fpl_edge.forecasts` selects for GW8 are the 21:58:06 snapshot for
`own` (285 players) and `minutes` (264 players, values 0.25-1.0, a
probability: 48% at or above 0.8); the newest row in the 5,756-row log is
made_at 2026-10-18T21:58:07+00:00. Every input precedes the deadline.

### 1c Shift probe — not applicable

The primary metric is realised season points (planner minus baseline), not a
correlation of forecasts with points.

## Check 2 — clean-checkout test runs — PASS

`git archive` of each commit into the scratchpad, `FPL_DATA_DIR` unset:
- before (`5aceef2`, the commit before `51520ef`): `python test_fpl.py`
  Ran 386, OK (skipped=8).
- after (`22a179c`): `python test_fpl.py` Ran 386, OK (skipped=8);
  `python -m unittest tests.test_S8` Ran 7, OK; `python -m unittest
  discover -s tests -t .` Ran 159, OK (skipped=2).
Matches the implementer's 386 OK (8 skipped) and 7 OK.

## Check 3 — re-run of the pre-registered evaluation — FAIL

My run: `P.replay(historical/2025-26, n_squads=50)` in-process on the
working tree (tools/planner.py, tests/test_S8.py, tools/chips.py,
tools/backtest.py, tools/hist_pit.py, fpl_edge.py and fpl_hist.py all have
the same blob at `22a179c`, HEAD `d8a2ee5` and the working tree), writing
the CLI's text plus the raw per-squad results (scratchpad `s8_verify/`,
14,116 s wall; my first CLI copy of the same run was killed at 07:18 after
it turned out to still be running alongside, and plays no part).

| | planner pts | hits | transfers | baseline pts | baseline transfers | paired gain | 90% CI | bar | robustness (first 5) |
|---|---|---|---|---|---|---|---|---|---|
| implementer, run1 (51520ef) and run2 (claimed 22a179c), byte-identical | 1919.5 | 11.5 | 48.5 | 1911.8 | 37.0 | +7.68 | [-6.58, +22.06] | FAIL | [7, 8, 7, 4, 5] |
| verifier, 22a179c | 1914.7 | 12.58 | 49.5 | 1911.8 | 36.98 | +2.90 | [-12.74, +18.40] | FAIL | [9, 4, 7, 3, 11] |

The baseline agrees to the printed digit (the forecasts, prices, autosubs
and realised points are shared); the planner's path does not. Full
precision from my results: mean gain 2.9, lo -12.74, hi 18.4, bootstrap
p 0.7382; per-squad gain sd 67.67, range -148 to +179, 26 of 50 squads
positive; baseline hits 0 in every squad. My own percentile bootstrap
(seed 20261018, B = 10,000, written independently) reproduces the
harness's interval to 0.0; seeds 1-3 give [-12.5, +18.6], [-12.7, +18.3],
[-12.2, +18.3].

Why the numbers differ (scratchpad `short_replay.py`, candidate comparison):
- `51520ef`'s `plan_candidates` skipped pairs with `if o1["id"] > o2["id"]:
  continue`. `singles` is ordered by the squad's row order (position, then
  id at GW1; after transfers the incoming players are appended), so for
  outgoing players at different positions this drops the pair whenever the
  earlier one has the higher id. On real squads at origin 2 the final code
  yields 37,107 / 46,959 / 21,168 distinct 15s for squads 0-2 against
  25,953 / 25,855 / 8,517 under `51520ef` (11,154 / 21,104 / 12,651
  missing, 0 extra); at origin 20, 13,715 / 20,734 / 12,818 missing, and
  the top plan differs for squads 1 and 2 (e.g. squad 2: final (381, 507)
  -> (16, 683) score 34.86; `51520ef` (507, 625) -> (283, 683) score
  31.75). `7f8ba52` replaced the id test with a seen-set, which is the
  exhaustive set; the commit message and the report describe the change as
  removing duplicates only, "score-neutral". It is not.
- Both versions are deterministic: a 3-squad GW2-12 replay gives identical
  per-squad results under PYTHONHASHSEED 0, 1, 2 for the final code
  (planner 592 / 512 / 522) and under 0, 1 for `51520ef` (569 / 509 /
  612), the baseline 596 / 500 / 513 in all five. So the final code has one
  answer, and it is mine; `51520ef` has a different one.
- Hence `tools/out/s8_run2/` (01:19 start per the launch message, output
  byte-identical to run1 on `51520ef`) did not execute the final code's
  `plan_candidates`; whichever copy it imported, its numbers are the
  `51520ef` planner's. The CHANGELOG entry and
  `worklog/cc_2026-10-19_S8.md` record those numbers as the final code's
  result and state the byte-identity "confirmed in the verifier's report";
  it is refuted here.

Both runs fail the bar on both halves (mean below +10, lower bound below
0), so the conclusion "FAIL, nothing adopted" stands; the recorded
measurement, the hits and transfers counts and the robustness line do not.

## Check 4 — metric, filter, bootstrap, threshold — PASS, with one flag

Verbatim prereg against the code (`tools/planner.py` at `22a179c`):
- Primary metric: season points per squad net of hits (weekly XI + captain
  with autosubs, minus 4 x hits), planner minus baseline, paired per squad:
  `st["pts"] += rp.realised(...) - HIT * hits` per week, `gains = planner -
  baseline` per squad (lines 409, 412). Exactly as pre-registered.
- Sample: 2025/26 GW2-38 (`REPLAY_FIRST, REPLAY_LAST = 2, 38`, GW2 the
  first origin with one training round as the prereg says), S7's 50 squads
  (`CH.sample_squads(..., 50, CH.SQUAD_SEED = 7)`), 1 FT a week, bank to 5
  (`MAX_FT = 5`, `st["k"] = min(5, max(k - used, 0) + 1)`), no chips.
- Forecasts: `project_reliability` point-in-time, clubs of the origin
  (`BT.canonical_at` -> `hist_pit`), pairings t..t+5 (`HORIZON = 6`, capped
  at 38), prices of the origin round, selling prices by `E.selling_price`.
- Planner configuration: decay 0.85 (`DECAY`), Boris's schedule
  (`SCHEDULES["boris"] = (1.5, 1.0, 0.6, 0.3)`), hit buffer 1.5
  (`HIT_MIN_GAIN = 4 + 1.5`); hit rule: decayed gain >= 5.5, the gain minus
  its largest decayed single-gameweek term > 0, every incoming P(start) >=
  0.8 (`evaluate`, lines 199-205; a missing P(start) refuses the hit);
  rolling at 5 banked refused (line 187); pool = top 25 per position by
  decayed six-week xP outside the 15 (`build_pool`, `POOL = 25`);
  candidates 0, every single same-position swap, every unordered pair of
  swaps, each legal under the selling budget, club cap 3 and 2 GK+DEF per
  club (`plan_candidates`, `legal`) — exhaustive in the final code only
  (check 3); XI and captain re-optimised per gameweek (`xi_value`: every
  formation, captain = the highest xP in the XI, which every formation
  contains).
- Baseline: the best one-week move with the free transfer when its gain > 0
  (strict), else roll, never a hit (`baseline_plan`: at most one swap, only
  with k >= 1, `v - base > best_gain` from 0.0).
- Bootstrap: unit = squad, B = 10,000 (`BT.B`), 90% percentile (`BT.CI =
  0.90`), seed 20261018 (`BT.SEED`), paired on the per-squad difference.
- Pass: mean >= +10 (`PASS_GAIN = 10.0`) and lower bound > 0 (line 414).
- Secondary: decay 0.80 and 0.90 reruns with a disagreement flag (live) and
  a count on the first 5 squads (replay); both schedules printed live.
No metric was promoted and nothing was re-tuned after the results: the
three code commits are 01:22-01:24, the replay output 03:42, and the only
code change after the first commit is the candidate-set fix in
`plan_candidates` (`git diff 51520ef..22a179c -- tools/planner.py`), made
before any result was seen; its effect on the result was misdescribed, not
hidden.

**Flag (ruling needed, not by itself a FAIL): the lost banked-FT value's
index.** The prereg's acceptance test 1 reads "using a transfer when k are
banked loses the k-th value". The code (`lost_ft_value`, docstring "against
rolling": `V(min(5, k+1)) - V(k')`) charges the (k+1)-th value: with 1
banked a move costs 1.0 (Boris) / 1.8 (solver) — the live table's lostFT
column — where the literal text gives 1.5 / 2.1; with 2 banked 0.6 instead
of 1.0; with 4 banked 0 instead of 0.3. The code's own test pins its reading
(`lost_ft_value(boris, 1, 1) == 1.0`, "use 1 of 1: stock 1 instead of 2").
Among transfer plans at one k the two readings shift every 1-transfer plan
equally, so the live top-5 order is unaffected, but the roll-versus-move
threshold is one schedule step lower under the code, and 2-transfer plans at
k >= 2 shift differently; a replay result holds for the code's reading only.
The reading was fixed in the first code commit, before any result, and is
stated in the code, the report and the CHANGELOG, so it is a definitional
ambiguity, not a post-hoc change. The launch message calls it "the prereg's
own reading"; the words "against rolling" are not in `prereg/S8.md`.

Two smaller notes, both consistent with the prereg: the live market is the
S7 recording gate (status "a", 45+ minutes in the last four; the prereg's
"through the recording gate; a gated-out player scores 0"); the baseline
chooses from the same top-25 pool as the planner (the prereg does not name
the baseline's pool).

## Check 5 — recording path and isolation — PASS

- `git diff 5aceef2..22a179c --stat`: `tests/test_S8.py` (+249) and
  `tools/planner.py` (+458) only; no runner file, `test_fpl.py` untouched.
- The nightly: `.github/workflows/nightly.yml` and `fpl_nightly.py` contain
  no reference to `tools/` or `analysis/`; the suite's isolation test (a
  subprocess importing fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate,
  fpl_publish and listing any module under /tools/) prints `[]`.
- The tool writes only under `--out`: the live run to a scratch folder
  produced `planner_live.txt` alone; `tools/out/` is git-ignored.
- `C:\GIT\FPL-data`: `projection_log.csv` sha256 e466c9cd... before and
  after the live run; `git status` unchanged; data HEAD `9da6ff1` (nightly
  2026-10-18). `C:\GIT\FPL-b` `git status` after my runs shows only the main
  session's S12 files, which are not this item's. The projection log is never
  opened for writing by `tools/planner.py` (it calls `E.read_log` only).

## Check 6 — mutation spot-check — PASS (15 of 20 red; 5 survivors are test gaps)

Scratch copy of `22a179c`; one line changed at a time; `python -m unittest
tests.test_S8`; the file restored (clean run 7 OK after).

Red (15): hit buffer 1.5 -> 0 (test_hit_rule); lost-FT value -> 0
(test_score_hand_case); rolling at 5 allowed (same); GK+DEF cap 2 -> 3
(test_exhaustive); duplicate pair of swaps allowed (same); replay training
through the target round (test_point_in_time); one-fixture rule dropped
(test_hit_rule); incoming P(start) rule dropped (same); baseline moving
without a free transfer (test_point_in_time); captain not added
(test_xi_value); pool 25 -> 20 (test_exhaustive); price line invented
(test_live_cli); budget ignored (test_exhaustive); decay not applied
(test_score_hand_case); DECAY 0.85 -> 0.80 (test_live_cli).

Survived (5), each a gap in the tests, none a defect in the final code
(verified by reading and by the live table): club cap 3 -> 4 (the test's "a
fourth from one club" case holds six ARS players, so it cannot tell cap 3
from 4 or 5; `CLUB_MAX = 3` by reading); "- 4 x hits" removed from the
score (the hand case has hits = 0; the live table shows the term applied:
plan 3 score 4.60 = gain 9.60 - 4 x 1 - 1.00); the replay's realised hit
charge removed; the replay's realised points read from t+1 (the toy replay
test checks structure, not the points; `realised(rows_after, t, ...)`
reads `actual[t]` by reading); HORIZON 6 -> 3. The implementer's 19 of 19
red are mutations of a different grain (e.g. "the club cap ignored"); mine
are finer. The oracle test that exposed the `51520ef` omission
(`keys == want_keys`) exists only since `7f8ba52`, which is why the first
commit's tests were green on a non-exhaustive generator.

## Check 7 — secrets — PASS

`tools/planner.py`, `tests/test_S8.py`, `prereg/S8.md`,
`worklog/cc_2026-10-19_S8.md`, the CHANGELOG S8 entry, the three output
files and both run logs, and `git show` of the four item commits: no
`apiKey=`, `api_key=`, `Authorization`, `Bearer`, `x-api-key`,
`ODDS_API_KEY` value or 32+-character key-like string. The planner reads no
network and no environment variable.

## The prereg's acceptance tests 1-6

1. Score and FT values: `test_score_hand_case_and_ft_values` (hand case
   with hits = 0; stock values; 5 banked refused) green; mutations red for
   the lost-FT value, rolling at 5 and the decay; the "- 4 x hits" term is
   untested (gap above) but present and applied (live plan 3). The k-th /
   (k+1)-th reading: flagged in check 4.
2. Hit rule: `test_hit_rule` green; the three mutations (bar, one-fixture,
   P(start)) red; the gain band 4-5.5 is searched and refused.
3. Exhaustive candidates and caps: in the final code, brute force equals
   the planner's best on the toy at three banks and the candidate key set
   equals the legal 0/1/2-transfer combinations (each unordered pair once);
   budget, GK+DEF cap and pool size mutations red; the club-cap mutation
   survives at 4. **The replay whose numbers are recorded ran a generator
   that failed this test on real squads (check 3).**
4. Point-in-time: test green (forecasts at 5 unchanged with every round >=
   5 row altered; a transfer planted at 6 invisible at 5; training through
   t red); my truncation test at 2/20/38 (1a) and the instrumented
   `canonical_through` (1b) confirm it on the real season; the baseline
   never takes a hit (0 hits in all 50 squads of my replay).
5. Robustness: decays 0.80/0.90 re-run live (no flag on the GW8 table) and
   in the replay (final code, first 5 squads: [9, 4, 7, 3, 11] of 37 weeks;
   the recorded [7, 8, 7, 4, 5] is the `51520ef` planner's); the price line
   prints "price predictor: no source" and the mutation that prints a
   number is red.
6. CLI: `python tools/planner.py` wrote `planner_live.txt` and nothing else
   under `--out` (byte-identical to the implementer's); `--replay` writes
   `planner_replay_2025-26.txt`; the nightly imports nothing under
   `tools/`; tests in `tests/test_S8.py`; `test_fpl.py` untouched.

## What has to change before a re-verification

1. Re-run the replay on `22a179c` (or later) and record its numbers; delete
   or relabel `tools/out/s8_run2/` and the "byte-identical" sentences in
   `worklog/cc_2026-10-19_S8.md` and the CHANGELOG entry. My full-precision
   results are in the scratchpad only; the numbers to expect are the second
   row of the check 3 table.
2. Correct the description of `7f8ba52`: a missing-candidate fix, not a
   duplicate removal.
3. A ruling on the lost-FT index (check 4 flag); if the literal "k-th
   value" is meant, the code and its test change and the replay runs again.
4. Optional test hardening (check 6 survivors).

## VERDICT: FAIL

The planner is point-in-time clean (0.0 difference at origins 2, 20 and 38
with every later outcome garbled; every live input before the GW8
deadline), its definitions match the prereg apart from a flagged index
ambiguity in the lost banked-FT value, the clean-checkout tests pass
(386/8 skipped before and after, 7 new), the recording path is untouched
and no secret is present; but the pre-registered evaluation does not
reproduce: my replay of the committed code gives a paired gain of +2.90
[-12.74, +18.40] against the recorded +7.68 [-6.58, +22.06], because the
recorded numbers come from the first commit's generator, which silently
dropped 30-45% of the two-transfer candidates (not "duplicates"), and the
"final-code run byte-identical to run1" claim is refuted by a deterministic
re-run. A failed pre-registered test honestly reported is not a verifier
FAIL; a recorded measurement that is not the committed code's measurement
is.
