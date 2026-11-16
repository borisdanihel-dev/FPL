# verify_FJ — the GW10 checkpoint, report only (master `99c9161`), Thu 12 Nov 2026

**VERDICT after the rerun of the two failed checks (Thu 12 Nov night): WARN.** Both checks are
cleared as ruled: the report's text is true, and the three ruled tests exist and work on
branch `fj-wip`. Open for Boris: the test is not on master yet, no test runs the script's
`main()`, and the GW15 tie rule has a gap across positions. See the last section. The GW10
result is unchanged (xp_v2 stays).

First run, kept below as written: **FAIL — on the report's text and on test cover only. Every
number, the interval and the revert rule's verdict (xp_v2 stays) reproduce exactly; nothing
needs recomputing.**

Verifier: Fable 5.2 (`claude-fable-5-2`); effort: launched at high, not confirmable.
`.claude/agents/backtest-verifier.md` read from disk first; it is the same text as my loaded
instructions. No transcript or chat log was read. Read-only: the only file written in the
repository is this one.

## What fails (two things, both small)

1. **One sentence of the report is false** (`worklog/cc_2026-11-12_FJ.md`, "Where the
   difference came from", GW9): "…needed a third defender, and **the lower id won**."
   - The ids: Calafiori 8, Thomas 173, Branthwaite 230. Branthwaite has the **highest** id
     of the three, and he is the one who started.
   - What actually broke the tie: `fpl_edge._best_xi` sorts each position by xP with a
     stable sort, so equal forecasts keep the order of the squad passed in.
     `checkpoint.py` passes our picks in slot order (`ORDER BY p.position`). Branthwaite was
     in slot 3 of our actual GW9 team; Calafiori and Thomas were in slots 14 and 15. So
     own's tie was settled by **our own actual line-up that week** (which was xp_v2's XI),
     not by id.
   - Shown with the repository's own `fpl_realised.realised_on` (a4cb2df), same 15, same
     forecasts, three input orders: slot order 72 (Branthwaite); ascending id **69**
     (Calafiori); descending id 72.
   - So the rule the report states would have given own 69 and d(GW9) = −1, not the −4 it
     prints. The −4 is what the pinned code gives; the explanation is wrong, not the number.
   - The first version of the sentence (commit `5d45151`: "the lower id, Branthwaite") was
     wrong in the same way; `99c9161` reworded it but kept the error.
   - Effect on the decision: none. With the lowest-id tie rule d = +0, −1, +12, mean +3.67,
     90% [−0.67, +8.00]; the upper bound stays +8.00 and xp_v2 stays. The tie as scored
     favours own by 3 points, so it is the conservative side for the revert rule.
   - Mitigating fact for the chat: own's previous-night snapshot (29 Oct 22:17 UTC) still
     had Branthwaite at 1.553; with that row own would have started him without any tie.
2. **Check 6 (mutation): no test covers the item's only new code.** The item adds no test
   (787 before, 787 after) and nothing under `tests/` or in `test_fpl.py` mentions
   `checkpoint.py`. Two one-line mutants of `checkpoint.py`, each in a scratch copy, run to
   the end with exit 0 and a wrong output, and the suite cannot see either:
   - `boot["hi"] < 0` → `boot["lo"] < 0`: the output says "Upper bound +8.00: own returns".
   - `d.append(pts_v2 - pts_own)` → reversed: d = −0, +4, −12, mean −2.67, 90% [−8.00, +2.67].
   The definitions the script imports are covered: removing the captain's doubling in
   `fpl_realised.realised_on` turns 2 of 30 tests in `tests/test_W3.py` red (30 OK
   unmutated). By the letter of check 6, and by the precedent of `verify_SMOKE.md`, an item
   whose own lines no test guards does not pass. Either a small `tests/test_FJ.py`, or
   Boris's ruling that a one-off report script under `worklog/` needs none (this run's
   independent recompute then stands in for it). That is his decision, not mine.

To clear: correct the one sentence (suggested: "…needed a third defender; the three were
tied at 0 and the tie went to the first in our pick order, Branthwaite (slot 3 of our
actual team); by id it would have been Calafiori, own 69, d −1"), settle point 2, and rerun
those two checks only.

## What passes

| Check | Result | Evidence in one line |
|---|---|---|
| Prereg before the computation | PASS | `a4cb2df` committed 21:01:10 UTC, pushed 21:01:21 UTC; run.txt start 21:03:13 UTC |
| 1a truncation | PASS | own's graded snapshot rebuilt from the log as it stood at the last data commit before each deadline: 0 differences, GW8, 9, 10 |
| 1b timestamp audit | PASS | 0 of 55,421 log rows made at or after their deadline; the three bundle commits pushed 3 h, 21 h 45 min and 9 h before their deadlines |
| 1c shift probe (warns only) | no WARN | highest unshifted rho +0.074; largest unshifted minus shifted +0.019 |
| 2 clean-checkout suite | PASS | `a4cb2df`: 787 OK, 11 skipped; `99c9161`: 787 OK, 11 skipped |
| 3 re-run | PASS | the script rerun on my own copies: identical but for the "generated" minute; my own code: identical |
| 4 prereg definitions | PASS, with notes | metric, sample, B 10,000, seed 20261018, 90%, threshold: as pinned |
| 5 recording path | PASS | the item changes no file the runner runs or imports; the log is untouched |
| 6 mutation | **FAIL** | above |
| 7 secrets | PASS | no key, no `apiKey=` URL, no Authorization value in the six files |
| The report's claims | **FAIL** (one sentence) | above; every other claim checked true |

## The launch's eight checks

### 1. The prereg precedes the computation; the method is what the script does; the rulings

- `prereg/FJ.md` was added in `a4cb2df`, committer time 2026-11-12 22:01:10 +01:00 =
  21:01:10 UTC. The local record of pushes (`git reflog show origin/master`) has it pushed
  at 21:01:21 UTC. It has not been edited since (`git diff a4cb2df 99c9161 -- prereg/FJ.md`
  is empty).
- `run.txt`: start 21:03:13, end 21:03:15 UTC. The implementer's scratch folders agree:
  data copied 21:02:07, the code worktree made 21:02:09, `checkpoint.py` written 21:03:07,
  `checkpoint.txt` written 21:03:15 UTC. The script and its output were committed at
  21:13:08 UTC (`5d45151`).
- I found no earlier computation of the xp_v2 side in the scratch files dated before the
  prereg (a limited search, 60 files). It cannot be proven from files that none was made.
  What was already public before the prereg: the nightly report of 12 Nov (data `6f9ecb8`)
  prints, from the frozen W3 code, own 41, 72, 62 and xp_v2 41 for GW8 (GW9 and GW10
  "xp_v2: not recorded before the deadline", because the nightly reads the bundle for GW8
  only). So own's three scores and d(GW8) = 0 were known; the method was nonetheless fixed
  by earlier text (the revert rule of 19 Oct, S6c's `realised_on`, S6b's bootstrap) and by
  point B, not chosen tonight.
- Method against script, line by line: lockdown guard (stops with "nothing is
  substituted"); 15 picks of entry 3073318; `fpl_squad.bundle_csv` and a stop if the reader
  picks another commit than the ruling's; `fpl_squad.recorded`; `fpl_realised.realised_on`
  unchanged (no code file differs between `47ac1ea` and `a4cb2df`); d = xp_v2 − own;
  `fpl_bt.bootstrap_mean` with its defaults (B 10000, SEED 20261018, CI 0.90); verdict
  `hi < 0`. All as pinned.
- The rulings, checked against the record only:
  - F-J: the identical line is in `BUILD_PLAN.md` (Part F).
  - The revert rule: the identical line is in `prereg/S6b.md` and `prereg/S6c.md`.
  - The plan of Sun 8 Nov (8 lines) and the rulings of Thu 12 Nov (15 lines): every line is
    identical in `prereg/W3.md`, `S8c.md`, `runcommit.md` and `FM.md` (the 12 Nov block
    also in `W3fix.md`).
  - Limit: those five files were filed by the same commit, `a4cb2df`. The record is
    consistent with itself; whether it matches what Boris typed I cannot check and do not
    try to.

### 2. Lockdown guard

`fpl.sqlite` of data `6f9ecb8` (SHA-256 `23e7...`, the same file as in `C:\GIT\FPL-data` and
in the implementer's copy): GW8, GW9, GW10 each `data_checked = 1`, 10 of 10 fixtures
`finished = 1`. GW4–7 the same. GW11: not finished, `data_checked = 0`. PASS.

### 3. Inputs

- Our 15: 15 picks each week; no chip in GW8–10 (`chips` holds none for those events).
- Bundle CSVs (my own reader, `git show` on each commit):

  | GW | deadline (UTC) | commit | committed (UTC) | pushed (UTC) | run.txt end (UTC) | SHA-256 in run.txt = CSV | newest before the deadline |
  |---|---|---|---|---|---|---|---|
  | 8 | 23 Oct 17:30 | `6034baa` | 23 Oct 14:26:29 | 14:26:32 | 14:26:18 | yes (`76a1...`) | yes (of 3 commits) |
  | 9 | 31 Oct 11:00 | `e708c91` | 30 Oct 13:14:32 | 13:14:35 | 13:14:19 | yes (`5435...`) | yes (the only one) |
  | 10 | 6 Nov 18:30 | `c0c6c3f` | 6 Nov 09:23:26 | 09:23:29 | 09:23:17 | yes (`e88c...`) | yes (the only one) |

  Each bundle's run.txt: tools commit `d9071b8`, modified 0. All of our 15 are in each CSV.
- own: the last snapshot before each deadline, 0 rows at or after it:
  GW8 23 Oct 14:22:52 UTC (278 players, 3 h 07 min before); GW9 30 Oct 22:13:59 UTC (293,
  12 h 46 min); GW10 6 Nov 01:48:17 UTC (300, 16 h 42 min).
- Truncation: `projection_log.csv` as committed on `data` at `a88168a` (23 Oct 14:22:56
  UTC), `c77c603` (30 Oct 22:14:05 UTC) and `fa31a48` (6 Nov 01:48:27 UTC), each the last
  log commit before its deadline (the next one is after it). The graded snapshot of every
  source, own included, is identical then and now, value for value.
- No own row, counted 0 as pinned: GW9 Branthwaite, Calafiori, Thomas; GW10 Thomas.
  For information: Branthwaite was in own's seven earlier GW9 snapshots (last 29 Oct,
  1.553) and dropped out of the last one; Calafiori and Thomas were last in the 23 Oct one.
  xp_v2 has Calafiori and Thomas at 0.00 in GW9 and Thomas at 0.00 in GW10 (rows present).

### 4. Independent recompute (my own code, no import from the repository)

All 1,365 elevens of the 15 enumerated, the legal ones kept (1 GK, 3–5 DEF, 2–5 MID, 1–3
FWD), the best by xP taken; bench = keeper, then outfield by xP then id; my own autosub
rule; captain = highest xP, ties to the lower id, doubled.

| GW | own | xp_v2 | d | captain (both) | optimal elevens own / xp_v2 | autosubs |
|---|---|---|---|---|---|---|
| 8 | 41 | 41 | +0 | Haaland | 1 / 1 | none |
| 9 | 72 | 68 | −4 | Haaland | **3** / 1 | none |
| 10 | 62 | 74 | +12 | Gabriel | 1 / 1 | none |

- Identical to `checkpoint.txt` in every XI, bench order, captain and total.
- GW9, own: three elevens tie on xP (the third defender); they score 72 (Branthwaite),
  69 (Calafiori) and 69 (Thomas; he played 0 minutes and Calafiori comes on). See fail 1.
- No starter of either model played 0 minutes in any of the three weeks, so autosubs moved
  nothing; without them the six totals are the same. No captain tie.
- Bootstrap, my own loop on `random.Random(20261018)`, B 10,000: mean 2.666…, lo −2.666…,
  hi 8.0, two-sided p 0.5772. Matches to the last digit (report: +2.67, [−2.67, +8.00],
  0.577).
- The interval does not depend on the seed: over the 27 equally likely resamples the exact
  5% and 95% points are −2.67 and +8.00 (exact two-sided p 0.593). With three gameweeks the
  upper bound is always (2 × largest d + middle d) / 3.
- Verdict: upper bound +8.00, not below 0: **xp_v2 stays**. Confirmed.
- Cross-check from a different run: the nightly's REALISED section of 12 Nov prints own
  41, 72, 62 and xp_v2 41 (GW8, bundle `6034baa`).
- The script itself, rerun on my clone at `a4cb2df` (modified 0) and my own data copy:
  `checkpoint.txt` identical except the "generated … UTC" minute.

### 5. Provenance

- `run.txt`: commit `a4cb2df` (full hash matches), modified tracked files 0; it records
  `checkpoint.txt` SHA-256 `fb86...`; the committed `checkpoint.txt` hashes to the same
  (working file and blob).
- `checkpoint.txt` prints the script's SHA-256 `864a...`; the committed `checkpoint.py`
  hashes to the same (working file, blob at `5d45151` and at `99c9161`, and the
  implementer's scratch copy).
- Two things to know, neither a failure:
  - The script ran from a scratch folder, outside the worktree, before it was committed.
    run.txt's `tool:` line is a label and "modified 0" does not cover the script; the
    printed SHA-256 is what ties the run to the committed file, and it matches.
  - The run's commit is `a4cb2df`, the item's last commit is `99c9161`. Between them only
    `prereg/FM.md` and files under `worklog/` changed, so the code that ran is the final
    code.
- `calibration.txt` has no run.txt and says so in its first line (`fpl_edge.py` writes
  none). I regenerated it (next check).

### 6. Calibration

- My rerun (`fpl_nightly.py --restore`, then `fpl_edge.py --section calibration`, both in my
  own copy, code `a4cb2df`, `ODDS_API_KEY` unset): identical to `calibration.txt` below its
  header line, all 87 lines. The database and the log in my copy are unchanged by it.
- My own arithmetic, no repository code: all 31 source-gameweek rows match on n, MAE,
  const, rho, starters rho, n_st and bias. Pooled MAE, rho and its ± (1.96 / √(n − 3))
  match for every source; the pooled constant matches with one mean over all graded
  forecasts (own 2.308, xg 2.336, bottomup 2.292, bottomup_lambda 2.180, fpl_ep 1.665).
- The report's table against `calibration.txt`: all six rows and their notes are right
  (own 7 GWs 2.082 / 2.308 / +0.308 ±0.044; fpl_ep 3, 1.139 / 1.665 / +0.730 ±0.044;
  bottomup 6, 2.228 / 2.292 / +0.285 ±0.050, loses in GW6; bottomup_lambda 2, 2.019 / 2.180
  / +0.354 ±0.084; minutes 6, +0.292 ±0.050; xg 7, 2.445 / 2.336 / +0.283 ±0.046, loses in
  6 of 7).
- Shift probe (warns only; players with 60+ minutes in g and g+1, pooled; Spearman, 90%
  interval by bootstrap over player-gameweeks, B 2,000):

  | source | GWs | n | unshifted | shifted to g+1 | difference |
  |---|---|---|---|---|---|
  | own | 4–9 | 941 | +0.066 [+0.013, +0.119] | +0.047 [−0.010, +0.100] | +0.019 [−0.054, +0.096] |
  | xg | 4–9 | 929 | +0.060 [+0.003, +0.109] | +0.075 [+0.019, +0.125] | −0.014 [−0.085, +0.058] |
  | bottomup | 5–9 | 766 | +0.033 [−0.030, +0.098] | +0.070 [+0.012, +0.130] | −0.038 [−0.124, +0.046] |
  | minutes | 5–9 | 766 | +0.030 [−0.028, +0.089] | +0.041 [−0.015, +0.101] | −0.012 [−0.095, +0.072] |
  | fpl_ep | 8–9 | 346 | +0.004 [−0.086, +0.095] | +0.144 [+0.050, +0.236] | −0.141 [−0.269, −0.003] |
  | bottomup_lambda | 9 | 158 | +0.074 [−0.062, +0.212] | +0.104 [−0.029, +0.231] | −0.030 [−0.219, +0.155] |

  Nothing above 0.25, no difference above 0.10: no WARN.

### 7. The report's claims

True as written: the lockdown lines; the table; totals 175 v 183; mean, interval, p; "10
possible resample multisets"; the bundle commits and "the reader picks exactly the ruling's
commits"; the three snapshot times; "GW9: the whole −4 is the keeper" (the two XIs differ
only in Verbruggen 11 v Kelleher 7); "both XIs started Branthwaite (9)"; own had no row
for the three; GW10 Groß 10 v Thiago −2 (22 minutes, red card in `player_gw`); the
calibration table; "xp_v2 has no graded gameweek in the projection log" (299 rows, all
GW11).

False: "the lower id won" (fail 1).

The drift note is true but incomplete; the chat should read it with this:
- own's bias by gameweek, GW4–10: +0.07, −0.27, −0.55, −0.96, −1.36, −1.30, −1.53. It has
  fallen every week since GW5. "Since GW8" and the table's jump from GW4 to GW8–10 leave
  out GW5–7; it is not a step at GW8.
- Where it comes from: own's mean forecast fell from 3.04 (GW4) to 1.18 (GW10) while the
  mean actual stayed between 2.62 and 3.11. Among the 157 players in all seven snapshots
  the bias runs −0.42, −0.65, −0.31, −1.09, −1.66, −1.57, −1.76, so it is not a change in
  who is forecast.
- "Its rank correlation held": GW8–10 average 0.344 against 0.353 for GW4–7, but GW8
  itself was own's lowest week (0.210 whole, −0.018 among starters).
- "Beats the constant in every gameweek": true, 7 of 7.

### 8. What the prereg pins and the report leaves out; the parked items

- Nothing the prereg pins is missing from the report or its output files.
- Reported but not pinned: the two-sided bootstrap p (0.577). It decides nothing and is not
  promoted.
- The parked list is consistent with the rulings as filed. Point B names "BUILD_PLAN Step
  20 and F-J" and then lists what to compute: the metric on **our actual 15**, per-week
  numbers, the mean and interval, the rule's verdict, the calibration for every source.
  The prereg listed the rest of F-J as parked before anything was computed; the report
  repeats it and carries the question to Boris in exact wording, as the 12 Nov text asks.
- Step 20's own GW10 item, the saves term, is F-E (`prereg/S6e.md`); it is inside parked
  item (3).
- One thing to keep in view: F-J (1) defines the revert rule on our squad **and 50 sampled
  squads**. Tonight's "xp_v2 stays" is point B's verdict on three squad-gameweeks; F-J's
  own sample has not been run. The report says so in its parked question, but its bold
  verdict line does not.

## Notes for the chat (not failures)

- The pinned scoring takes ties in the XI from the order of our actual picks. Where a
  model has no row for several players, its XI then leans on the line-up we really played.
  It happened once here (GW9, own) and helped own by 3 points.
- Master moved to `e692192` while I ran (two commits, `prereg/S8c.md` and `prereg/W3fix.md`
  only). The six FJ files are the same at `99c9161` and `e692192`.

## How this was run

- Code: my own clones of `C:\GIT\FPL` in the scratch folder `vfy_fj` (a detached checkout
  of `a4cb2df` and one of `99c9161`); no worktree added, no git write in `C:\GIT\FPL`.
- Data: a file copy of `C:\GIT\FPL-data` at `6f9ecb8` (clean); `--restore` only in the
  copy. `C:\GIT\FPL-data` and `C:\GIT\FPL-b` untouched. No `fpl_sync.py`, no `--record`.
- Data files opened only by Python with `-I`; the repository's scripts with `-E -s`.
- Check 5 was made from the list of changed files; regenerating forecasts would need
  `--record`, which my launch forbids, and no model or runner file changed.
- My scripts and outputs: `vfy_fj\scripts` (`recompute.py`, `truncate.py`, `calib.py`,
  `tie_real_code.py`, `poolconst.py`, `verbatim.py`) and `vfy_fj\*.txt`.

**VERDICT: FAIL.** The checkpoint's numbers are right: the prereg came first, the inputs
are point-in-time (truncation and timestamp audit clean, no shift-probe warning), my own
code and a rerun of the script both give d = +0, −4, +12, mean +2.67, 90% [−2.67, +8.00],
and the revert rule keeps xp_v2; the calibration regenerates identically and matches my own
arithmetic. It fails on two narrow points. The report explains GW9's tie with a rule that
was not applied ("the lower id won": Branthwaite has the highest id; the tie went to our
pick order, and by id own would have scored 69 and d would be −1), and the item's only new
code has no test, so two one-line mutants of it produce a wrong verdict or a reversed sign
with the suite green. Neither changes the decision. Correct the sentence, settle the test
question with Boris, and rerun those two checks.

## Rerun of the two failed checks, Thu 12 Nov night

**VERDICT: WARN.** Both failed checks are cleared as ruled. Three things stay open for
Boris: the test is not on master yet, no test runs the script's `main()`, and the GW15 tie
rule has a gap across positions. Nothing here changes the GW10 result.

Verifier: Fable 5.2 (`claude-fable-5-2`); effort: launched at high, not confirmable.
`.claude/agents/backtest-verifier.md` read from disk first; it is the same text as my loaded
instructions. No transcript or chat log was read. Read-only: the only file written in the
repository is this one. Scope: the two failed checks only, as launched. The rest of the first
run stands, except one sentence of mine, corrected below.

State checked: master `3d6ab3d` (the FJ files last changed in `66db35e`);
`origin/fj-wip` `44dcaeb` (the local ref and `git ls-remote` agree); data `6f9ecb8`.
`checkpoint.py` is the same blob at `b7e4716`, `3d6ab3d` and `44dcaeb`.

| Launch check | Result | Evidence in one line |
|---|---|---|
| 1 the report's text | PASS | the GW9 sentence is true; my own code gives the lowest-id figures; the slot-order result stays primary |
| 2 the regenerated run | PASS, one note | commit `b7e4716`, modified 0, output hash matches, all 326 numbers equal the first run's; the printed script hash is of a CRLF checkout |
| 3 test cover (check 6) | PASS on `fj-wip` for the three ruled tests; **WARN** | 8 of 8 mutants of the helpers red; 0 of 8 mutants of `main()` red; my own "d reversed" line is not caught by a test; the test is not on master |
| 4 the GW15 tie rule | PASS on the order and inside a position; **WARN** | across positions a tie goes to the formation order, not to the lower id |
| 5 the suite on `fj-wip` | PASS | 792 OK, 11 skipped (master `3d6ab3d`: 787 OK, 11 skipped) |

### 1. The report's text

- The facts, from `fpl.sqlite` (GW9 picks of entry 3073318): Branthwaite slot 3, id 230,
  9 points; Calafiori slot 14, id 8, 6 points; Thomas slot 15, id 173, 0 points, 0 minutes.
  All three are defenders, and own had no row for any of them.
- My own code (no import from the repository; all legal elevens of the 15 enumerated):
  own has three tied optimal elevens in GW9, all 3-4-3, differing only in the third defender.
  - Slot order: Branthwaite starts, own 72.
  - Lowest id: Calafiori starts, own 69.
  - xp_v2 scores 68 either way.
- Both rules, three weeks:

  | tie rule | own | xp_v2 | d | mean | 90% interval | verdict |
  |---|---|---|---|---|---|---|
  | slot order (pinned, primary) | 41, 72, 62 | 41, 68, 74 | +0, −4, +12 | +2.67 | [−2.67, +8.00] | xp_v2 stays |
  | lowest id (information) | 41, 69, 62 | 41, 68, 74 | +0, −1, +12 | +3.67 | [−0.67, +8.00] | xp_v2 stays |

  The exact quantiles over the 27 resamples are the same as the bootstrap's.
- GW9's own tie is the only tie in the three weeks that changes an eleven. (xp_v2 has
  Calafiori and Thomas both at 0.00 in GW9; both are on its bench, in the same order under
  either rule.)
- So the corrected sentence is true in every part: slot 3 before slots 14 and 15; not by
  id; the lowest id is Calafiori, 6 points, own 69. "The first two wordings said the lower
  id won" is also true (`5d45151`, `99c9161`).
- Primary and secondary: the report's table, mean, interval and verdict are the slot-order
  ones. The lowest-id figures are marked "secondary, information". `checkpoint.txt` does the
  same: its summary is the slot-order run and its last line gives the other order.
- One sentence in the report's "Verifier" part repeats an error of mine. See "A correction
  to my first report".

### 2. The regenerated run

- `run.txt`: commit `b7e4716` (the full hash matches), modified tracked files 0,
  22:53:30–22:53:31 UTC. `b7e4716` was committed at 22:53:12 and pushed at 22:53:30 UTC.
- It records `checkpoint.txt` SHA-256 `18a0...`; the committed `checkpoint.txt` hashes to
  the same (working file and blob).
- Against the first run's `checkpoint.txt` (`99c9161`): three lines differ. They are the
  code and script-hash line, the "generated" minute, and the new last line (the tie order).
  All 326 numeric tokens from line 4 on are equal.
- My rerun (my own clone at `b7e4716`, modified 0; my own copy of the data, the same two
  hashes `23e7...` and `7125...`): `checkpoint.txt` is identical to the committed one except
  the "generated" minute.
- Final code: after `b7e4716` only files under `worklog/` changed on master, and `fj-wip`
  adds only `tests/test_FJ.py`. Between `a4cb2df` and `b7e4716` the only Python files
  changed are `checkpoint.py` and `worklog/fm_draft/gate2_matrix.py`; no imported module
  changed.
- **Note, the script hash.** `checkpoint.txt` prints script SHA-256 `330f...`. The committed
  `checkpoint.py` hashes to `5e34...` (the blob, and the working file in `C:\GIT\FPL`).
  - `330f...` is the same text with CRLF line endings. The run's worktree was checked out
    with `core.autocrlf = true`, and the script hashes its own file as it lies on disk.
  - I rebuilt `330f...` from the blob by adding a CR to each line; my own clone prints it too.
  - So the run is on the committed text. But nobody can match the printed hash to the
    committed file without knowing this. The first run's `864a...` matched because that
    script ran from a scratch copy with LF endings.
  - Not a failure: the commit, modified 0 and equal content tie the run to the code.

### 3. Test cover (check 6)

`tests/test_FJ.py` at `44dcaeb`: 5 tests in 3 classes, standard library only, no data, no
network. It loads `checkpoint.py` from the repository by path.

- **The sign of d:** `paired([41, 72, 62], [41, 68, 74])` is `[0, −4, 12]`; on a toy where
  xp_v2 starts a 12-point forward and own benches him, d is above 0.
- **The revert verdict:** `verdict` at upper bounds −0.01, 0.0 and 8.0 with a negative
  lower bound; then through `fpl_bt.bootstrap_mean`: d = −5, −3, −4 gives "own returns",
  d = 0, −4, 12 gives lo −8/3, hi 8.0, "xp_v2 stays".
- **The tie order:** a toy 15 built like GW9 (ids 230 in slot 3, 8 in slot 14, 173 in slot
  15, none with an own forecast). Slot order starts 230, id order starts 8, the scores
  differ by 3; the default is slot; any other word raises.

That is what the ruling and the pin ask for. The mutants follow. Each is one line of
`checkpoint.py` changed in a scratch copy of the `fj-wip` archive (4 is two lines).
"Test" is `unittest discover -p test_FJ.py` in that copy. "Script" is that copy run on the
real data against my clone.

| # | Mutant | Test | Script on the real data |
|---|---|---|---|
| 0 | none | 5 OK | exit 0, the cited output |
| 1 | `verdict`: `boot["hi"]` → `boot["lo"]` (my first mutant) | red, 2 tests | exit 0: "Upper bound +8.00: own returns" |
| 2 | `main`: `d.append(pts_v2 - pts_own)` reversed (my second mutant, the same line as in the first run) | **green** | stops on its own `assert`, exit 1, no output written |
| 3 | `paired` reversed (the implementer's "d reversed") | red, 1 | stops on the `assert`, exit 1 |
| 4 | 2 and 3 together | red, 1 | exit 0: d +0, +4, −12 |
| 5 | `ordered`: slot and id swapped | red, 1 | exit 0: own 69 printed as the slot run |
| 6 | `ordered`: highest id first | red, 1 | exit 0: the id line shows own 72 |
| 7 | `score`: default order `id` | red, 1 | unchanged (`main` passes the order) |
| 8 | `score` ignores the order | red, 1 | exit 0: the id line shows own 72 |
| 9 | `score`: xp_v2 scored on own's forecasts | red, 1 | exit 0: d +0, +0, +0 |
| 10 | `main`: own and xp_v2 swapped in the call to `score` | **green** | exit 0: own 41, 68, 74; xp_v2 41, 72, 62; d +0, +4, −12; mean −2.67, 90% [−8.00, +2.67] |
| 11 | `main`: picks read `ORDER BY p.player_id` | **green** | exit 0: own 69, d −1, labelled "slot" |
| 12 | `main`: the run scored in the other order | **green** | exit 0: the same as 11 |
| 13 | `main`: `--tie` default `id` | **green** | exit 0: the id run without being asked |
| 14 | `main`: the verdict line reads another interval | **green** | exit 0: "Upper bound +8.00: own returns" |
| 15 | `main`: lockdown guard off | **green** | unchanged (the data is locked) |
| 16 | `main`: bundle-commit check off | **green** | unchanged (the reader picks the ruling's commits) |

- The four helpers (`ordered`, `score`, `paired`, `verdict`): 8 of 8 mutants red
  (1, 3, 4, 5, 6, 7, 8, 9).
- `main()`: 0 of 8 red (2, 10, 11, 12, 13, 14, 15, 16). No test runs `main()`. The tests
  reach the helpers. The lines that feed them the real data have no test: the slot order
  of the SQL, which model is which, which order the run uses, which interval the verdict
  line reads, the two guards.
- Five of those eight print a wrong result with exit 0 on the real data (10 to 14). Two of
  them are the wrong outputs of my first run's mutants again: 10 is the reversed sign, 14
  is "own returns".
- My second mutant (2) is stopped by the script's own `assert d == paired(...)`, not by a
  test. Under `python -O` the assert is gone: exit 0, d +0, +4, −12, mean −2.67.
- The launch's "3 of 3 red" is true for the implementer's three mutants. I read them from
  their scratch copies: the verdict on `lo`, `paired` reversed, `ordered` swapped. Their
  "d reversed" is line 99 (`paired`); mine is line 176 (`main`).
- **On master the cover is unchanged.** `tests/test_FJ.py` is only on `fj-wip`; master's
  suite (787) still has nothing that imports `checkpoint.py`. The reason given is sound:
  the nightly's gate runs `tests/` by discovery (`fpl_nightly.py`, `TEST_ARGS`), so the
  file is runner work by FAST-TRACK item 1. But the rulings' schedule names no night for it.
- For the GW10 result none of this matters: my own code gave the same numbers in both
  runs. It matters for the GW15 rerun (F-L), which is why the ruling asked for the test.
- `tests/test_W3.py` already builds a toy database, log and bundle repository
  (`toy_realised`). A test that runs `main()` on such a toy looks feasible. I did not try
  it; that is the implementer's work.

### 4. The GW15 tie rule

- **Pinned before the code.**

  | what | commit | committed (UTC) | pushed (UTC) |
  |---|---|---|---|
  | the rulings and the pin, `prereg/FJ.md` | `88c77df` | 22:49:09 | 22:49:15 |
  | `checkpoint.py` (`--tie`, the helpers) | `b7e4716` | 22:53:12 | 22:53:30 |
  | the report and the regenerated run | `66db35e` | 22:54:18 | 22:54:38 |
  | `tests/test_FJ.py` (branch `fj-wip`) | `44dcaeb` | 22:56:07 | 22:56:25 |

  The implementer's scratch files hold no copy of the new code older than the pin (the
  working file was last written at 22:52:46 UTC, the two smoke runs at 22:52:59). That
  cannot prove nothing was drafted earlier.
- **Pinned before any GW15 run.** GW15's deadline is 12 Dec 13:30 UTC; it is not finished,
  `data_checked = 0`; GW11 has not started. No GW15 checkpoint folder exists in any branch.
- **The ruling text.** The block "Rulings, Thu 12 Nov night" (3,608 characters) is identical
  in `prereg/FJ.md`, `FM.md`, `S8c.md`, `runcommit.md`, `W3fix.md` and `FJ6.md`. The same
  limit as in the first run: one commit filed all six, and I do not check it against the chat.
- **What `--tie id` does on the real data.** Equal to my own code in every eleven, bench
  order, captain and total, three weeks, both models. In GW9 own starts Calafiori and its
  bench is Kelleher, Slater, Thomas, Branthwaite.
- **Inside a position it does what it says.** The 15 go to `realised_on` sorted by id, and
  `_best_xi` sorts each position stably, so the lower id comes first. The bench and the
  captain already break ties by the lower id.
- **Gap: a tie across positions.** `_best_xi` tries the formations in a fixed order (3-4-3,
  3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-2-3, 5-3-2, 5-4-1) and keeps the first of equal totals.
  - Toy, run through the script's own `ordered`, `choice` and `score` at `b7e4716`: a
    defender with id 5 and a forward with id 300, equal xP, the last place between them.
    `--tie id` starts the forward (id 300) and scores 24. With the defender it would be 32.
  - The pin's rule says "the lower player id comes first, in the XI". Its next sentence,
    "In code: the 15 are passed to `realised_on` sorted by player id", is what was built.
    The two disagree in this one case.
  - It did not happen in GW8–10: the only tied optimum (own, GW9) is inside one position.
  - It is model-neutral and independent of our line-up either way.
  - It becomes likelier with F-J's 50 sampled squads at GW15: a sampled squad can hold
    several players of different positions with no own row, all counted 0.

### 5. The suite on `fj-wip`

- `git archive` of `origin/fj-wip` (`44dcaeb`), no `.git`, no `FPL_DATA_DIR`,
  `ODDS_API_KEY` unset, `python -E -s -m unittest discover -v -p "test*.py"`:
  **Ran 792 tests, OK (skipped 11)**, 320.6 s. The five `tests.test_FJ` tests are in it,
  all ok.
- Master `3d6ab3d` the same way: Ran 787 tests, OK (skipped 11). The difference is the five.
- Note: importing `checkpoint.py` puts the repository root and `tools/` at the front of
  `sys.path` for the rest of the discovery run. No module name exists in both folders, and
  the suite is green, so nothing is shadowed today.

### A correction to my first report

- My section 7 said of own's bias: "It has fallen every week since GW5." That is wrong for
  GW9. The series is +0.07, −0.27, −0.55, −0.96, −1.36, −1.30, −1.53: GW9 rose by 0.06.
- Right: it fell in five of the six steps and is lowest at GW10; there is no step at GW8.
- The report's "Verifier" part repeats my words ("has slid every week since GW5"). The
  figures printed beside them are right. The error is mine, not the implementer's.

### Secrets

No key, no `apiKey=` URL and no Authorization value in `tests/test_FJ.py`, `checkpoint.py`,
`checkpoint.txt`, `run.txt`, the report or `prereg/FJ.md`.

### Decisions for the chat

1. **When does `tests/test_FJ.py` land on master?** Until it does, master has no test for
   `checkpoint.py`. The schedule names no night for it. Mon 16, Wed 18 and Thu 19 Nov have
   no runner change before the freeze (Fri 20 Nov 05:00 UTC). Riding with another night's
   change would need Boris's word ("one runner change per night").
2. **`main()` has no test.** Five one-line changes print a wrong result with exit 0 and a
   green suite. Add a test that runs `main()` on a toy before the GW15 run, or accept the
   helper tests plus the verifier's own recompute at GW15?
3. **The tie rule across positions.** Either pin what the code does (equal totals go to
   the first formation in `_best_xi`'s order) or make the code follow the lower id there
   too. Before the GW15 run, and before the 50 squads.
4. **The script hash.** It depends on the checkout's line endings (`330f...` printed,
   `5e34...` committed). For the GW15 run: hash the text with LF endings, print the git
   blob id, or leave it and note it?
5. **One wording fix in the report** (my error): "has slid every week since GW5" → "fell
   in five of the six weeks since GW4 (GW9 rose by 0.06)". Docs only.

### How this was run

- Scratch folder `vfy_fj2`: `git archive` copies of `44dcaeb` and `3d6ab3d`; my own clone
  of master at `b7e4716` (the script needs the bundle commits and a clean tree); file
  copies of `fpl.sqlite` and `projection_log.csv` from `C:\GIT\FPL-data` (at `6f9ecb8`,
  not pulled, not changed). No git write in `C:\GIT\FPL`; `C:\GIT\FPL-b` untouched.
- Data files opened only by Python with `-I`; the repository's modules with `-E -s`.
- My scripts and outputs: `vfy_fj2\scripts` (`lowid.py`, `mutate.py`, `crosspos.py`) and
  `vfy_fj2\out` (`lowid.txt`, `mutants.txt`, `crosspos.txt`, `suite_fj.txt`,
  `suite_master.txt`, `slot\`, `id\`). In `mutants.txt` the mutants carry other labels
  (M1, M2a, M2b, M2c, M3a–M3d, M4–M11); the table above renumbers them 1 to 16.
- Run from about 23:20 to 23:45 UTC, Thu 12 Nov.

**VERDICT: WARN.** The two failed checks are cleared as Boris ruled. The report's GW9
sentence is now true, the lowest-id figures (d = +0, −1, +12, mean +3.67, 90% [−0.67,
+8.00]) match my own code, and the pinned slot-order result stays primary. The regenerated
run is on `b7e4716` with 0 modified files and equals the first run in every number. The
three ruled tests exist on `fj-wip`, the suite there is green (792 OK), and every mutant of
the four helpers turns them red. It is not a clean PASS for three reasons. The test is on a
branch, so master's suite still does not guard the script, and no night is scheduled for
it. No test runs `main()`: my own "d reversed" line is caught only by the script's assert,
and five other one-line changes print a wrong result with exit 0. And the GW15 tie rule as
built follows the lower id inside a position but not across positions. None of this touches
the GW10 result (xp_v2 stays); all of it should be settled before the GW15 rerun.
