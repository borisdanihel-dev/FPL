# runcommit — real runs record their code commit

Committed before any code for this item. Runner work (CLAUDE.md, Fast track
item 1): dry run, Boris's real dispatch and the freeze windows apply.

## The ruling (Boris's message verbatim)

Rulings, Tue 3 Nov night.
1. Yes: the test for a captain with no player_gw row (= 0 minutes). Put it on w3-wip so it lands with W3 on Sat 7 Nov; tonight's runner change is used, and Wednesday stays clear before the GW10 freeze.
2. Yes: real runs record their code commit (log line, status header, commit message), as dry runs do. Runner change: prereg first, then schedule it in the international break after W3 and the S8c landing (Mon 9 Nov or later).
3. CHIPS reading the previous night's archived export is fine as is: chips are only revealed after a deadline. If the section header doesn't already name the export's date, add that with W3.
Wednesday: no runner change. Resume Step 16 parts 3-4 on s16b-wip (offline). Thursday: the GW10 bundle on Boris's paste.

## The finding

- W2's final verifier (`worklog/verify_W2_final.md`) had to establish which
  code a real run used from the push history and the test count. Neither
  the log, the status file nor the commit message says.
- What a dry run records today (master `7841ef0`): only the commit message
  carries the commit, `dry run <date> <ref> <7 characters> [skip ci]`
  (`fpl_publish.py:177-179`, from `GITHUB_SHA`). A dry run's log header
  (`fpl_nightly.py:202-206`) and status line (`checks.status_line`) carry
  none, the same as a real run's.
- So "as dry runs do" holds for the commit message. **The log line and the
  status header are new for both kinds of run.** This item gives both kinds
  all three.

## The design, pinned before the code

- **The commit:** `GITHUB_SHA`, its first 7 characters, as in the dry-run
  message. The nightly's master checkout has no `ref:`, so `GITHUB_SHA` is
  the commit it checks out.
- **No `GITHUB_SHA`** (a run outside Actions): never a substitute.
  - The log line says `code commit: unknown (no GITHUB_SHA)`.
  - The status field says `code ?`, as the repo size says `? MB`.
  - The commit message omits the field, as the dry-run message collapses an
    empty one.
- **The log line:** `code commit: <7>` in the run header of
  `logs/run_<date>.log`, after `using:`.
- **The status header:** ` | code <7>`, the last field of the first line of
  `reports/status.txt` and `reports/status_dryrun.txt`.
  - It goes last, so the fields before it do not move.
  - `status_time`, and `fpl_publish.py`'s `STATUS FAIL` test, read only the
    fields before it. `tests/test_S3.py`'s exact-line test changes with it.
- **The commit message:** `nightly <date> <7> [skip ci]`. Nothing parses
  the message; `[skip ci]` stays.
- **Nothing else moves:** no forecast, no section, no check result, no
  `projection_log.csv` row. The recording path is proved unchanged by
  diffing the log under a frozen clock, as the change protocol requires.

## Acceptance tests

- `tests/test_runcommit.py`, hermetic:
  - all three records with `GITHUB_SHA` given, for a real run and a dry run;
  - all three with `GITHUB_SHA` absent: the log and status words above, and
    the message without the field;
  - `status_time` and the `STATUS FAIL` test still read the longer line.
- Each record shown red when its change is removed; mutations 1 per record
  and 1 for a substitute value (the commit read from anywhere but
  `GITHUB_SHA`).
- A push to `dry/runcommit`: `data-dryrun-runcommit`'s commit message, log
  and `reports/status_dryrun.txt` all carry the pushed commit's 7 characters.
- The whole suite before and after, bare and with the data; the verifier;
  the write guard.
- Boris's real run on master: the data commit's message, `logs/run_<date>.log`
  and `reports/status.txt` all carry master's 7 characters.

## The schedule

- No code before W3 (Sat 7 Nov) and the S8c landing (Sun 8 Nov) are on
  master. W3 changes `fpl_nightly.py` and `checks.py`, so this item builds
  on them.
- Monday 9 Nov or later, in the international break.
  - GW11's deadline is Sat 21 Nov 11:00 UTC, so its freeze starts Thu 19 Nov
    05:00 UTC. The push must land before that.
  - Never between 21:00 UTC and the end of that night's nightly.
- It starts only on Boris's word (Session operating mode a).

## Rulings, Fri 6 Nov morning (Boris's message verbatim)

Rulings, Fri 6 Nov morning. GW10 first: run the GW10 deadline pass (Boris's paste) before anything else. Step 16 resumes after the GW10 deadline (18:30 UTC).
Step 16:
1. Yes: type the 2024/25 and 2025/26 European calendars from the Wikipedia season pages under CC BY-SA (F-I (3)), with the revision id and attribution in each CSV header; the verifier checks every row against its source. After the GW10 deadline.
2. Keep the Elo as built (K 20, home 60, tier starts 1500/1400/1300/1200/1100, non-league 1000).
3. Keep 0.5 per European knockout round for English clubs.
4. Keep the FA Cup third-round rule (the 44 tier-1/2 clubs plus 20 placeholders rated 1250).
Record all four in the prereg verbatim before the single backtest run.
Tuesday's two:
5. The 68 tests that fail with commit signing on: make the tests' temporary repos disable signing locally (git -c commit.gpgsign=false or per-repo config). Tests only, no behaviour change; land with the S8c landing on Sun 8 Nov.
6. runcommit: yes, the log line and the status header on both dry and real runs, plus the commit message on real runs. In the international break after W3 and S8c, prereg first.

## Amendment 1: the date, the price-moves name fix and a correction (Boris's plan of Sun 8 Nov, item 3, and his rulings of Thu 12 Nov, verbatim)

Recorded before any runcommit code.

- The item now also carries the price-moves fix (plan item 3): the nightly
  report's price-moves section matches players by name, and showed
  Coventry's Thomas at 5.5 -> 4.0; that was Hull's Thomas.
- The date: Sat 14 Nov (rulings of Thu 12 Nov, Schedule).
- **Correction to "The schedule" above (it is not edited):** GW11's freeze
  starts Fri 20 Nov 05:00 UTC, 30 hours before the deadline of Sat 21 Nov
  11:00 UTC, as Boris's plan says; not Thu 19 Nov 05:00 UTC.

### Boris's plan of Sun 8 Nov (verbatim)

International break plan, Sun 8 Nov (the item count resets to 0 of 6). GW11 deadline Sat 21 Nov 11:00 UTC; GW11 freeze from Fri 20 Nov 05:00 UTC. One runner change per night; no merges without Boris's click.
1. Mon 9 Nov: W3 merge (with the +02:00 committer test, the fetch-depth comment and the captain-without-row test); Boris clicks the real run.
2. Tue 10 Nov: the S8c landing (with the commit-signing test fix); Boris clicks the real run.
3. Wed 11 Nov: runcommit (real runs record their code commit), plus a fix for the nightly report's price-moves section matching players by name (it showed Coventry's Thomas at 5.5 -> 4.0; that was Hull's Thomas).
4. GW10 checkpoint once GW10 is locked (data_checked): BUILD_PLAN Step 20 and F-J: the paired own v xp_v2 metric over GW8-10 from the pre-deadline bundle CSVs and the projection log, the revert rule, and the model re-grade. Report only; no change without Boris.
5. Status gate v2 (F-M, brought forward from GW15): draft the prereg only, no code yet. Proposal: status 'd' = P(start) x chance in the next gameweek and as normal after; 's' = 0 for the known ban length, then as normal (Thiago: GW11-13 out, back GW14); 'i' with an unknown return = 0 for two gameweeks, then scaled by the last known chance. State how it can be checked, given that historical flags aren't archived. Boris rules before any code.
6. Step 16: finish it (type the 2026/27 cup and European CSVs, the verifier's row checks, the single backtest run, the report), then Step 18's prereg (the second-half chip plan).
Thu 19 Nov: the GW11 bundle, with Thiago and Thomas out, on Boris's paste.

### Boris's rulings of Thu 12 Nov (verbatim)

Rulings and tonight's plan, Thu 12 Nov (Boris is here; no runner pushes to master until tonight's nightly has finished; no merges tonight).

Rulings:
1. W3 verifier FAIL (record only): paste Boris's Sun 8 Nov plan text verbatim into prereg/W3.md, marked "recorded after the fact on 12 Nov: the landing moved from Sat 7 Nov to 11 Nov by Boris's plan of Sun 8 Nov". Then re-run the verifier's record check only. No code change. Rule kept: each plan item's text goes into its prereg before acting on it.
2. One night behind: CAPTAIN and BAN RISK must read the current night's export (availability matters before a deadline). CHIPS may stay one night behind, as amendment 3 allows. Fix with a test.
3. False Free Hit flag: CHIPS values every player on one scale. A player with no own forecast counts as 0, with a note, never on a different scale; the FH flag must agree with the base screen in the same report. Fix with a test.
4. Two runs in one day: the S2 rule stands (same-day rows replaced). Note in the report that the scheduled run's xp_v2 rows survive at data 2e0b948.
5. Effort level: note "launched at high, not confirmable" in the report; nothing else.
Schedule (one runner change per night; Boris clicks each real run; all before the GW11 freeze, Fri 20 Nov 05:00 UTC): Fri 13 Nov S8c; Sat 14 Nov runcommit plus the price-moves name fix; Sun 15 Nov points 2 and 3 as one change with two tests.

Tonight, in this order:
A. The W3 record fix (Ruling 1).
B. GW10 checkpoint, report only (BUILD_PLAN Step 20 and F-J). GW10 should now be locked. The paired own v xp_v2 decision metric over GW8-10: each model picks its XI, captain and bench from our actual 15; realised points with autosubs; using the pre-deadline bundle CSVs (gw8 6034baa, gw9 e708c91, gw10 c0c6c3f) and own's last pre-deadline rows from the projection log. Per-week numbers, the mean and its 90% interval, the revert rule's verdict, and the model re-grade (calibration for every source over GW4-10). Post it here for the chat.
C. Status gate v2 prereg draft (break plan item 5). The rule as proposed: 'd' = P(start) x chance in the next gameweek, then normal; 's' = 0 for the known ban length, then normal; 'i' with an unknown return = 0 for two gameweeks, then scaled by the last known chance. Say how it can be checked without archived historical flags, and what it changes for Thiago, Thomas and Calafiori in the GW11 matrix. Draft only; post it here for Boris's ruling tonight.
D. Branch prep for the coming nights: (a) s8c-wip ready to land; push dry/S8c for its automatic dry run once tonight's nightly has finished. (b) A branch with Rulings 2 and 3, their tests and the verifier, ready for Sunday.
E. If there's time: Step 16 (the 2026/27 CSVs, the row checks).
Stop at 6 items; park questions with the exact wording. Also post the status of Step 16.

## Rulings, Thu 12 Nov night (Boris's message verbatim; for this item: the Schedule (Sat 14 Nov))

Rulings, Thu 12 Nov night (chat review: the item count resets to 0 of 6).

FJ, the GW10 checkpoint:
1. xp_v2 stays (revert rule: upper bound +8.00). Fix the report's sentence: own's GW9 tie was settled by the squad's slot order (our actual GW9 line-up), not by id. Add the verifier's figures for a lowest-id tie rule (d = +0, -1, +12, mean +3.67, 90% [-0.67, +8.00]; same verdict). The pinned result stays primary.
2. Add tests/test_FJ.py (the sign of d; the revert verdict on a toy; the tie order), since F-L re-runs this script at GW15. In prereg/FJ.md, pin an explicit, model-neutral tie rule (lowest player id) for the GW15 run, before that run.
3. Parked F-J items: the chip plan for GW11-19 (first-half Bench Boost and Free Hit) comes before the GW11 deadline. Prereg it, run it by Wed 18 Nov, and use S7 on the candidate post-transfer squads plus bb_timing with status gate v2 as information. The 50 squads, S6's rerun, F-E and the DEF re-check go with F-L at GW15.
4. Calibration: before reading anything into fpl_ep's numbers, re-run the calibration on the common player set at GW15 (its 3 gameweeks were scored on a different population). Note own's bias drift (about -1.4 since GW8) in BUILD_PLAN's revisit list.

FM, status gate v2 (Boris's answers to the five questions):
1. 'i' with an unknown return: 0 in weeks t and t+1, then a fixed 50% from t+2.
2. 'i' with a return date in the news: like 's': 0 until that date, then as normal.
3. 's' with no end date: 0 for one gameweek, then as normal.
4. Yes: record the rule under a new source name, xp_v2_g2, with the retrospective check (GW4-10 from our archived nightly exports) as its test and the bar as drafted (90% lower bound of the paired |error| difference above 0). xp_v2 keeps the v1 gate; xp_v2_g2 replaces nothing until it passes and Boris accepts it.
5. Suspended matches count as neither started nor missed in the last-four window.
Timing: code, the check and the verifier on a branch by Tue 17 Nov. The runner records xp_v2_g2 as a new source on Tue 17 Nov (one runner change). Its numbers go into the GW11 bundle as information whatever the check says.

S8c landing (answers to the verifier's decisions):
1. Yes: bring origin/s6f-wip 0b16969, origin/s6e2-wip d87f8aa and origin/s8b-wip cfa7a36 into s8c-wip; the full suite; a short re-check of the new head before the dry run.
2. Boris's OK for f1f5df2 (fpl_xpv2.forecast takes tools/xp_v2_live.forecast's text again, lift=()). Record this ruling verbatim in prereg/S8c.md before the merge.
3. Yes, with the landing: a W3 test on the toy with a status 'd' player, asserting the runner records no xp_v2 for him (tests only).
4. Make ChecksMain.setUp check its commit's exit code so the guard covers the twelfth line.
5. Mode (d): the 21:00 UTC-to-end-of-nightly window applies to master and to dry/* (anything that starts a workflow). Other work branches may be pushed at any time.
6. Add the CHANGELOG entry and report for point 5 and the copy fix to the landing (docs only, inside the re-check). Leave the duplicate W2 amendment 2 entry as recorded (append-only); note it in the S8c report.

Schedule (one runner change per night; Boris clicks each real run; all before the GW11 freeze, Fri 20 Nov 05:00 UTC): Fri 13 S8c (dry run after the re-check, then the merge on Boris's click); Sat 14 runcommit plus the price-moves name fix; Sun 15 W3fix (CAPTAIN/BAN RISK on the current export, CHIPS on one scale); Tue 17 xp_v2_g2 recorded; Wed 18 the chip plan posted; Thu 19 the GW11 bundle on Boris's paste.
Record each part of these rulings verbatim in its prereg before acting on it.

## Answers, Mon 16 Nov (Boris's message verbatim; for this item: the Revised schedule's Wed 18 (runcommit plus the price-moves name fix; it moves from Sat 14))

Answers, Mon 16 Nov (resume; the item count stays as it is).
1. S8c: yes, tonight. Confirm master has only gained state-file docs since dry/S8c's green run (13b07b2), then tag pre-S8c, merge s8c-wip 4bbb43c and push before 21:00 UTC, and tell Boris when his real run is needed. Final verifier on the real run; delete dry/S8c and data-dryrun-S8c after.
2. W3fix Ruling 3: option (a). Both the main report's Free Hit screen and CHIPS count a player with no own forecast as 0, with a note. Record it as an amendment to item N's frozen metric in prereg/W3fix.md before the code.
3. FJ WARN: (i) add an end-to-end test of checkpoint.py's main() on a toy (it must catch a reversed d and a wrong revert verdict); (ii) pin the GW15 tie rule across positions in prereg/FJ.md: when two formation-legal XIs have equal sums, choose the one whose sorted player-id list is lexicographically smallest. Both on fj-wip, landing with W3fix.
Revised schedule (one runner change per night; Boris clicks each real run; GW11 freeze Fri 20 Nov 05:00 UTC):
- Mon 16: S8c. Offline: start status gate v2 (xp_v2_g2) code and its retrospective check (GW4-10) on a branch.
- Tue 17: W3fix (Rulings 2 and 3) plus fj-wip's tests. Offline: finish xp_v2_g2's check and its verifier.
- Wed 18: runcommit plus the price-moves name fix. Offline: the GW11-19 chip plan (first-half Bench Boost and Free Hit; S7 on candidate post-transfer squads with Thiago (banned GW11-13) and Thomas out; bb_timing with xp_v2 and xp_v2_g2), posted for the chat.
- Thu 19: no runner change. The GW11 bundle on Boris's paste, with xp_v2_g2 numbers as information.
- After the GW11 deadline: xp_v2_g2 recorded by the runner if its check passed and Boris accepts.
Record each part verbatim in its prereg before acting. If a question blocks you while Boris is away, park it, carry on with the next item, and post all parked questions together.

## Answers, Thu 19 Nov night (Boris's message verbatim; for this item: Sun 22 (runcommit plus the price-moves name fix))

Answers, Thu 19 Nov night. Standing rule from now on: a WARN or FAIL stops that item only. Park its questions in the state file and carry on with the next independent item; never sit idle waiting for the chat.

W3fix (lands after the GW11 deadline, on the first free night from Sat 21 Nov):
1. (i) CHIPS's Free Hit screen reads tonight's export, so its flag always matches the base screen.
2. No: the "3+ of our XI not 'a'" trigger counts our best XI before the zero (it exists to catch an injury crisis; zeroing first would hide it).
3. (a) Keep tools/chips.py matched to fpl_chips: one rule everywhere, and the GW pass and planner take the zero too.
4. Yes: add tests for the five surviving mutants before the merge.
5. Yes: print the export's own generated time beside its name in the CAPTAIN and BAN RISK headers.
FM (xp_v2_g2):
6. (A) P(start) uses the last four gameweeks in which the player was not suspended.
7. (A) Score all seven origins, GW4-10.
FJ:
8. Yes: regenerate checkpoint.txt with the landing.
After the GW11 deadline: Sat 21 W3fix (with fj-wip's tests), Sun 22 runcommit plus the price-moves name fix, Mon 23 xp_v2_g2 recorded if its check passed and Boris accepts.

GW11 deadline pass, now (deadline Sat 21 Nov 11:00 UTC; freeze from Fri 20 Nov 05:00 UTC: tools and worklog only):
a. Tonight: git pull --ff-only in C:\GIT\FPL-data; run the GW11 bundle from master (the S8c tools are now on master; clean worktree) on the newest export. Commit gw11_pass.txt, xp_v2_all.csv and run.txt to master under worklog/gw_pass/gw11/.
b. Transfers (2 FTs, bank 0.9, no hits). Thiago is banned GW11-13 (back GW14); Thomas is d 50% (calf). Post the best pairs with and without a Bench Boost in GW11, run twice: under the gate, and with Thiago lifted from GW14 and Thomas at his chance (information, as in GW10). Also the named options: Thiago + Thomas out; Thiago out only (roll one).
c. Chips (the GW11-19 chip plan, information for the chat): S7 on the current 15 and on the two best candidate squads (with and without a Bench Boost), with the GW11-19 lines; bb_timing for a Bench Boost in GW11 against later first-half weeks, on the post-transfer squads.
d. Post, no decisions: the planner, own and xp_v2 side by side, the captain table, the flagged-player block, ban risk, the S7 lines, the transfer tables and bb_timing. By Fri 20 Nov 09:00 UTC.
e. Friday, after Boris's real run (about 15:00 UTC, after the press conferences): refresh the bundle and re-run b and c; commit before 18:00 UTC.
Then, still offline: the FM code and its retrospective check (answers 6-7), then W3fix's tests (answer 4), ready for after the deadline.

## Boris's message of Thu 19 Nov late, verbatim (calibration: a squared-error column; it rides with runcommit, or with W3fix if that lands first)

After the GW11 deadline, with W3fix or runcommit: add a squared-error column (RMSE, and RMSE against the constant) beside MAE in the calibration section, so forecasts that run low or high are judged on the same scale as expected points. Report only; no bar changes.

(Recorded Thu 19 Nov 22:30 UTC. The design, the constant RMSE is measured against, and the tests are pinned here before the code, after the GW11 deadline.)

## Addendum, pinned before its code (Thu 19 Nov 22:55 UTC): the price-moves fix and the calibration RMSE column

### The price-moves fix (amendment 1)

- Found: `fpl_edge.sec_diff` matches players by `web_name` in all three of
  its player blocks - YOUR SQUAD price moves, NEW FLAGS, FORM MOVERS - so two
  players of one name collide (Coventry's Thomas showed Hull's price move).
- Pinned: all three blocks match by player id. The previous export's players
  are keyed by `id`; "our squad" and "owned by anyone in the league" are the
  `player_id`s of the export's `squads` rows (present since S2). A squads row
  without `player_id`: the block prints one line, "not comparable: squads
  rows without player_id", never a name match.
- The printed lines keep their format (name, club, prices).
- Test (`tests/test_runcommit.py`): two players named Thomas at two clubs,
  ours unchanged in price and the other moved: our price-moves block says
  "none" and NEW FLAGS / FORM MOVERS follow the ids; red on the current code.

### The calibration RMSE column (Boris's message of Thu 19 Nov late)

- `fpl_edge.sec_calibration`'s per-gameweek table gains two columns after
  `const`: `RMSE` = sqrt(mean((forecast - realised)^2)) and `rconst` =
  sqrt(mean((c - realised)^2)) with c the same constant as the MAE's `const`
  (the pool's mean realised points). The `minutes` row prints `-` for both,
  as for MAE (a start probability).
- The per-source summary line reads "MAE x vs constant y   RMSE x vs constant
  y   rho ...".
- Report only: the verdict column ("beats const" / "loses", on MAE), the
  "real signal" verdict and every bar are unchanged; p1_eval.py is untouched.
- Test: on a toy log the two numbers equal the formulas; the minutes row
  prints `-`; the verdicts are byte-identical to the current code's.

## Questions parked for Boris (exact wording), Fri 20 Nov 00:55 UTC, after the pre-check WARN of `7f44c65` (`worklog/verify_runcommit.md`)

The item stops (standing rule of Thu 19 Nov); its dry run and merge wait. Every
behaviour reproduced: the three records end to end with and without
GITHUB_SHA, real and dry; the price-moves fix on tonight's data (the six
removed report lines are other players' values); the RMSE columns and every
verdict; the recording path; 869 OK four ways. The gaps are in the tests.

1. **The bug as it happened.** "With the name lookup put back on the previous
   export's side, the suite stays green and tonight's report prints Hull's
   Thomas move again (the toy only catches the current-side lookup). Add tests
   with the namesake after our player in the previous export, for all three
   blocks (yes), or accept (no)?"
2. **Two pinned tests missing.** "No test reads FORM MOVERS, and no test passes
   GITHUB_SHA through checks.main for a real and a dry run. Add both (yes), or
   accept (no)?"
3. **No substitute, everywhere.** "'Never a substitute' is tested for
   checks.code_commit only. Add a decoy variable to the log and message tests
   (a), or route all three records through checks.code_commit (b)?"
4. **Calibration wording and checks.** "Add value checks for the calibration
   summary line and the two surviving verdict cases, and name RMSE and rconst
   in the section's DEFINITIONS and the minutes note (yes), or leave the
   report text as pinned (no)?"
5. **The merge date.** "The pin and the code were made before the GW11
   deadline on a work branch. Confirm that 'After the GW11 deadline' governs
   the merge only (yes)?"
6. **Order with W3fix** (information): whichever of W3fix and runcommit lands
   second is rebased onto the first and gets a short re-check before its dry
   run.

Correction: the commit message of `7f44c65` says 11 of the new tests are red on
the old code; with the fourteenth test (the verdict where RMSE disagrees,
added after that count) it is 12 (9 failures, 3 errors).

## GW12 deadline pass message, Thu 26 / Fri 27 Nov (Boris's message verbatim; for this item: its last paragraph, the schedule after the GW12 deadline)

GW12 deadline pass (deadline today Fri 27 Nov 18:30 UTC; GW12 freeze: tools and worklog only). 1 free transfer, bank 0.5; Thiago banned until GW14.
1. git pull --ff-only in C:\GIT\FPL-data; run the GW12 bundle from clean master on the newest export; commit gw12_pass.txt, xp_v2_all.csv and run.txt to master under worklog/gw_pass/gw12/.
2. Transfer tables (1 FT, no hits): the best single moves and roll, under the gate and with Thiago lifted from GW14, and with Calafiori at P(start) 1.0 (his GW8 cameo is still in the window). Also the clean-sheet-flattened gain for the top three moves (information, as in GW11).
3. Captain: Arsenal v City is in our XI both ways. Print the captain table, xg, bottomup and bottomup_lambda for the top four, and the GW12 odds for ARS-MCI (each side's lambda and P(cs)).
4. Chips: S7 GW12-19 lines on the current 15 and on the best post-transfer squad, and bb_timing for GW14 v GW15 (the Bench Boost plan is GW14).
5. Post, no decisions, by 10:00 UTC. After Boris's real run (about 14:00 UTC, after the press conferences): refresh 1-4 and commit before 16:30 UTC.
After the GW12 deadline, runner changes resume (one per night, Boris clicks each real run): Fri 27 W3fix (with fj-wip's tests); Sat 28 runcommit plus the price-moves name fix plus the RMSE column; Sun 29 free. Then the GW13 freeze from Mon 30 Nov 12:30 UTC. Also draft F-N's prereg and post the parked questions in one batch.

## Rulings, Fri 27 Nov (Boris's message verbatim; for this item: runcommit answers 1-6)

Rulings — Fri 27 Nov (GW12 deadline 18:30 UTC). Standing rule holds: a WARN/FAIL stops that item only; park it and carry on.

GW12 refresh
1. Boris dispatches a real run on master, nothing ticked, ~14:00–15:00 UTC. When green, refresh gw12_post points 1–4 on the new data (XI; captain table with xg/bottomup/P10+; transfers gated + Calafiori-lifted + CS-flat; flags) and commit to worklog by 16:30 UTC. Post a short delta vs data 2efc924: anything that moved >0.3 or changed rank.
2. Flags must include: status/news for all 15, yellow-card counts for our players (Groß), and status of the planner's top targets (Silva BOU, Justin, Tavernier).
3. Current lean: roll (2 FT for GW13), no chip, captain by the frozen rule. Give the numbers; don't re-argue the lean.
4. Freeze applies: tools and worklog only until after the deadline.

W3fix answers
1. Float-sum xi_lex test: yes.
2. Four minor mutant tests: yes, all four.
3. Push dry/W3fix at or after 19:30 UTC tonight. The merge needs Boris's click and must finish before 21:00 UTC. If dry run or verifier isn't green by 20:45 UTC, or Boris isn't available, land it Sat 28 in the same 19:30–21:00 UTC window and move runcommit to Sun 29.
4. CHIPS label shows the generated time: yes.
5. Changelog wording: accepted.

runcommit answers
1. Namesake test against the previous export: yes.
2. FORM MOVERS and GITHUB_SHA tests: yes, both.
3. Option (b): route all three records through checks.code_commit. No decoy.
4. Calibration value checks: yes. RMSE and rconst as drafted, computed on exactly the same rows as MAE, with rconst using the same constant as the existing MAE baseline. Write both formulas into the prereg.
5. "After the GW11 deadline" governs the merge only: confirmed.
6. Order: W3fix first; runcommit (with the Thomas/Thomas price-moves fix and the RMSE column) the next night. Sun 29 is the buffer. Nothing lands after Mon 30 Nov 12:30 UTC (GW13 freeze).

Weekend (after the deadline, tools only)
- Re-run S7 and bb_timing for GW13–19 assuming 2 FT in GW13, Thiago back GW14, and Groß's ban risk. Report BB and FH week candidates with and without the Calafiori lift.
- Draft the F-N prereg (CS shrinkage in the planner) for my review.

## Answers of Fri 27 Nov, pinned before their code (Fri 27 Nov 12:55 UTC)

### Answer 4: the two formulas (Boris: "Write both formulas into the prereg")

Take one cell of the per-gameweek table, (source, gameweek). Its rows R are
the `pairs` the MAE already uses. They are every logged forecast for that
source and gameweek whose team played: a blank (no row) is graded as 0, and
only settled gameweeks count (data_checked = 1 and every fixture finished).
Each row is (p_i, a_i), the forecast and the realised points, for i = 1..n,
with n = |R|.

- c = (1/n) · Σ a_i: the mean realised points over R. This is the constant of
  the existing MAE baseline, `const` = (1/n) · Σ |c − a_i|.
- MAE = (1/n) · Σ |p_i − a_i| (unchanged).
- **RMSE = sqrt( (1/n) · Σ (p_i − a_i)² )**
- **rconst = sqrt( (1/n) · Σ (c − a_i)² )**: the same c, the same rows. It is
  the population standard deviation of a_i over R.

The per-source summary line uses the same formulas over that source's pooled
rows: the union of its graded cells. c is the mean a_i of that pool, which is
again the summary's own MAE constant.

The `minutes` source (a start probability) prints `-` for RMSE and rconst, as
it does for MAE and const.

Report only:
- No verdict reads RMSE or rconst.
- "beats const" / "loses" stays MAE < const.
- "real signal" stays rho − 1.96·se > 0.10.
- `p1_eval.py` is untouched.

### The other answers, read for the code

- **Answer 4, tests and text:**
  - Value checks for the summary line (both RMSE values, in their places).
  - Value checks for the two verdict cases that survived: one test where
    RMSE beats its constant and MAE loses (verdict "loses"), and one where
    the "real signal" line stands while RMSE loses to rconst.
  - Each test must be red on V24, V28, V29 and V30 of
    `worklog/verify_runcommit.md`.
  - DEFINITIONS gains the line `RMSE  sqrt(mean((predicted - actual)^2));
    rconst = RMSE of predicting the mean actual for everyone (report only, no
    bar)`.
  - The minutes note names RMSE and rconst among the undefined columns.
- **Answer 1:** a test with the namesake listed after our player in the
  previous export, for all three blocks (YOUR SQUAD price moves, NEW FLAGS,
  FORM MOVERS). It must be red with the name lookup put back on the previous
  export's side.
- **Answer 2:**
  - A test that reads the FORM MOVERS block.
  - A test that passes `GITHUB_SHA` through `checks.main` for a real run and
    a dry run, checking all three records.
- **Answer 3, option (b):**
  - The run log line, the status header and the commit message all take the
    commit from `checks.code_commit` (the one reader of `GITHUB_SHA`). No
    other code reads the variable for them.
  - The tests patch `checks.code_commit` and see its value in all three
    records. There is no decoy test.
  - A mutant that reads `GITHUB_SHA` directly in one record must be red.
- **Answer 5:** confirmed. "After the GW11 deadline" governs the merge only.
- **Answer 6, order:** W3fix lands first. runcommit, with the price-moves fix
  and the RMSE column, lands the next night in the 19:30-21:00 UTC window,
  after a rebase onto W3fix and a short re-check before its dry run. If W3fix
  slips to Sat 28, runcommit goes on Sun 29. Nothing lands after Mon 30 Nov
  12:30 UTC (the GW13 freeze).

## Rulings, Fri 27 Nov 16:25 UTC (Boris's message verbatim; for this item: point 3, the fallback: if tonight's W3fix misses, runcommit moves to Tue 1 Dec 19:30-21:00 UTC)

Rulings (Fri 27 Nov, 16:25 UTC). This replaces my 16:10 UTC text, which was never delivered. Record verbatim.

1. Advance approval for merges (protocol change, from tonight). Record it in BUILD_PLAN.md's protocol section; record each item's approval in that item's prereg.
- Boris may approve a landing in advance, per item, in chat.
- With an advance approval you merge yourself, but only if ALL hold: verifier PASS (WARN or FAIL holds it); dry run green; full suite passes on a fresh clone; write guard clean; inside 19:30–21:00 UTC; not in a deadline freeze; no other runner change that night; Boris hasn't revoked it.
- If any condition fails, don't merge: park the question and carry on, as usual.
- After merging, post the merge commit and the report in the worklog.
- Advance approval never covers changes to the decision rules, chips or transfers.
- Boris approves in advance under this rule: W3fix tonight (dry run 19:31 UTC from 3fe7500), and T1/T2 (w3tie-wip 82977fe, after rebase) on Sat 28.

2. Item — scheduled pre-deadline run.
- Naming: if lane A's W4 in BUILD_PLAN.md is already this item, call it W4. If W4 is a different item, give this one the next free W id. The Sun 29 slot goes to this item, not to anything else called W4.
a. Prereg verbatim first, then code. Standard library only.
b. Trigger: an hourly schedule on the nightly workflow (or a thin workflow running the same job), in the nightly's concurrency group so there's never a second writer. Queue, never cancel.
c. Gate, a pure function predeadline_due(now_utc, deadline_utc, last_predeadline_event):
   - due only if deadline − 6h ≤ now ≤ deadline − 2h and there's no pre-deadline run yet for that event;
   - the deadline is the next event's deadline_time from the FPL API, read at gate time so a moved deadline is followed;
   - not due if there's no next event.
   It exits within seconds, before any odds call or any write.
d. When due: run exactly the manual-dispatch path (master, nothing ticked). Commit to data as "predeadline GW<N>" with a marker (event id and time) that the gate reads.
e. Tests on fixed clocks: both window edges exactly, one minute outside each, already ran, moved deadline, no next event. Mutants: flip each comparison, swap the bounds, drop the marker check. All must go red.
f. No clock or force override on master. One exists only on dry/ branches, for the dry run.
g. Dry run via W1b. Recording-path files byte-identical to a manual dispatch on the same export.
h. CHANGELOG entry; report worklog/cc_<date>_<id>.md.
i. Landing: Sun 29 19:30–21:00 UTC, with Boris's click. Not advance-approved: it's the first scheduled writer, so he sees it first. Missed → the first free night after the GW13 deadline; Boris clicks manually until then.
j. Once live: when a pre-deadline run lands, do the GW refresh unprompted and commit it to the worklog within 1h.

3. Fallback if tonight's W3fix misses: W3fix lands Sat 28 (still advance-approved). Sun 29 stays with the pre-deadline run. runcommit moves to the first free night after the GW13 deadline (Tue 1 Dec 19:30–21:00 UTC). T1/T2 ride with the next landing, since they're test-only.

4. Optional, information first: check whether gh is installed and authenticated on the PC (gh auth status, never paste a token). If yes, propose rules for dispatching recovery runs yourself: nightly on master only, nothing ticked, clean master, not within 2h of a deadline, not 21:00 UTC to nightly end, at most 2 a day, each logged with a reason. Don't use it until I rule.

Standing rule holds: a WARN or FAIL stops that item only; park it and carry on.

- **Session reading (16:30 UTC):** runcommit has no advance approval; it lands on Boris's click. If W3fix lands tonight, runcommit keeps Sat 28 (answer 6's order). If W3fix misses tonight, it lands Tue 1 Dec 19:30-21:00 UTC.
- **Time label correction:** the "Session reading (16:30 UTC)" above was committed at 16:23:02 UTC (`86e50b3`);
  the label ran ahead of the clock.

## Rulings, Fri 27 Nov 16:30 UTC (Boris's message verbatim; for this item: point 1's order: runcommit merges first on Sat 28, then T1/T2)

Rulings (Fri 27 Nov, 16:30 UTC). Record verbatim.

1. T1/T2 on Sat 28: merge under the advance approval, after runcommit.
- Clarification of the approval rule (add to BUILD_PLAN.md Part B under point 1): "no other runner change that night" applies only when the item being merged is itself a runner change.
- A test-only item can merge the same night as a runner change. Test-only means its diff touches only tests/, worklog/, prereg/ or docs, nothing the runner imports or executes, and the verifier confirms that.
- Order: runcommit first. Then rebase T1/T2 on the merged master and run the full suite on a fresh clone.
- If 21:00 UTC comes first, T1/T2 wait for the next free night, still approved in advance.

2. W5 naming accepted (W4 stays the later queue item).

3. Recovery dispatch: proposal_recovery_dispatch.md accepted, effective now, with two amendments:
a. Boris's explicit request in chat overrides rule 2a (recovery only) and rule 5 (not standing in for W5), but never 2b–2f.
b. Review after W5 has run live for two deadlines.
Report every dispatch in your next status message.

4. Time-label correction noted; no further action.

Standing rule holds: a WARN or FAIL stops that item only; park it and carry on.

## Rulings, Sat 28 Nov 10:25 UTC (Boris's message verbatim; for this item: point 1, runcommit approved in advance under the 16:25 UTC rule, landing tonight 19:30–21:00 UTC, first; point 2, the ninth pre-merge check)

Rulings (Sat 28 Nov, 10:25 UTC). Record verbatim.

1. Boris approves runcommit in advance under the 16:25 UTC rule. It lands tonight, 19:30–21:00 UTC, first. T1/T2 follow if there's time, as already approved.

2. W3fix decision 1: yes, your reading is right. Add to BUILD_PLAN.md Part B under point 1, and as a ninth pre-merge check:
"'Never covers changes to the decision rules, chips or transfers' means:
(a) no chip is played and no transfer is made by anyone but Boris, in the FPL app;
(b) advance approval cannot introduce or change a decision rule (Part C, the frozen chip rule, the three-layer rule) that hasn't already been ruled.
An item that implements a change already ruled and recorded verbatim in its prereg may be approved in advance even if it touches chip, captain or transfer code, but only when Boris names that item explicitly."

3. W3fix decision 2: yes. The verifier may read public GitHub pages and the public API (run list, run metadata, commits) without logging in. Never through gh or any token. Log each read in its report with the URL and time. Add this to the agent file.

4. W3fix point 3 (the window counts an unplayed gameweek as zero minutes):
a. The weekend S7 and bb_timing re-plan for GW13–19 runs on the first nightly after GW12's last match (Sun 29, 16:30 UTC), so Sunday night's data, committed Monday. Not before. The freeze allows tools, so Monday is fine. Report Calafiori's P(start) on that data.
b. Queue a small item after W5: a gameweek enters a player's last-four window only once his team's fixture in it is finished.
   Pre-registered replay test: nights with no unfinished gameweek in the window stay byte-identical; only nights between a deadline and that gameweek's last match change.
   Prereg first. It changes forecast inputs, so it isn't advance-approved: Boris names it when the prereg is ready. Earliest landing is the first free night after the GW13 deadline.

Standing rule holds: a WARN or FAIL stops that item only; park it and carry on.

- **Session reading (written 10:34 UTC):** point 1 supersedes the 16:30 UTC reading above ("runcommit has no
  advance approval; it lands on Boris's click"). The session merges runcommit itself tonight only if all nine
  checks of BUILD_PLAN.md Part B hold: the eight of 16:25 UTC and point 2's scope check, run against the
  rebased diff. If any fails, it does not merge; the question is parked and the next free night applies.
