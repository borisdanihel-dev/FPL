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
