# W3fix — CAPTAIN and BAN RISK read the current night's export; CHIPS values every player on one scale

Committed before any code for this item. Runner work (CLAUDE.md, Fast track
item 1): dry run, Boris's real dispatch and the freeze windows apply. Sun 15
Nov, as one change with two tests (rulings of Thu 12 Nov, Schedule). The
design is pinned below, before the code, in an addition to this file.

## The rulings (Boris's message of Thu 12 Nov, verbatim; Rulings 2 and 3 are this item, and point D(b))

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

## Where they come from

The W3 final verifier's report, `worklog/verify_W3_final.md`, "Decisions for
the chat" items 2 and 3 (data `6f9ecb8`).

## Ruling 2, pinned before its code (Thu 12 Nov)

- **Tonight's export:** `fpl_squad.current_export(data_dir)` reads the
  working export, the newest `fpl_export_gw<N>.json` in the data folder
  (`fpl_ship.newest_export`: the file tonight's sync writes and the archive
  step copies after the sections). None there: a `MissingInput`, so the
  section prints its one SKIPPED line (W2's rule), never a stale substitute.
- **CAPTAIN and BAN RISK** read it in place of `fpl_chips.newest_export`
  (the newest dated archive, i.e. last night's export). CAPTAIN's header
  already names its export; BAN RISK's header gains "from <export>".
- **Unchanged:** REALISED (it reads the database and the log); CHIPS's
  calculator stays on the dated archive (amendment 3, point 3). CHIPS's Free
  Hit screen is Ruling 3's, pinned separately after Boris's answer to the
  question below.
- **The test** (`tests/test_W3fix.py`, red on the current code): a data
  folder whose newest dated archive has one of our players at status `a`
  and whose working export has him flagged with chance 0. CAPTAIN names the
  working export and gives him no xp_v2 forecast; BAN RISK names the working
  export and gives him P(start) 0. The W3 test worlds gain the working
  export the nightly always has after its sync (or `--restore`).
- **Measured:** suite before and after, bare and with the data; the test red
  on the current code; mutations (each section back on the archive) red;
  CAPTAIN and BAN RISK on tonight's real data, before and after.

## Question parked for Boris (exact wording), before Ruling 3's code

"Ruling 3: the base report's Free Hit screen (item N's frozen metric) values
a player with no own row by bottomup, and CHIPS uses the same function. Own
records exactly the Free Hit gate, so on the same export the two screens
differ only through our own flagged players (no own row), whom the base
screen values by bottomup. To make the flag agree in every case: (a) count 0
in both, by an amendment to item N's frozen metric (the base report's screen
moves too), or (b) CHIPS counts 0 and reads tonight's export, and the flag
agrees except when one of our flagged players would make our XI on
bottomup?"

Measured for it: on the 8 exports of 29 Oct–6 Nov, own's recorded players
equal the Free Hit gate (status `a`, 45+ minutes in the last four) exactly,
0 differences either way.

## Rulings, Thu 12 Nov night (Boris's message verbatim; for this item: the Schedule (Sun 15 Nov); the Free Hit question above is not answered in it and stays parked)

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

## Answers, Mon 16 Nov (Boris's message verbatim; for this item: point 2 (Ruling 3: option (a), an amendment to item N's frozen metric, recorded here before the code) and the Revised schedule's Tue 17 (W3fix, Rulings 2 and 3, lands with fj-wip's tests))

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

## Ruling 3, option (a), pinned before its code (Mon 16 Nov): an amendment to item N's frozen metric

Item N's frozen definition is the CHANGELOG entry "2026-10-15 — item N: the
Free Hit screen"; that entry stays as written and this amends it (a CHANGELOG
amendment entry lands with the item, before the GW11 deadline).

- **The metric, amended** (`fpl_edge.one_week_points`): in a gameweek for
  which `projection_log.csv` holds own rows (in practice the first upcoming
  week; the log records one week ahead), a player with no own row counts 0
  (source `no own`), never bottomup. A gameweek with no own rows at all is
  bottomup for every player, as before (one scale within each week). A
  blank still scores 0. Unchanged: the gate, the bench, the budget, the
  solver, FH_GAP 8.0, FH_NOT_A 3, the "not a" count.
- **The note:** below the table, for each own week, one line: "GW<w>: a
  player with no own forecast counts 0 (W3fix Ruling 3, amending item N):
  <k> of our 15 (<names>), <m> in the Free Hit gate". Printed wherever
  the table is printed (`free_hit_lines`: the base report, the watch file,
  CHIPS).
- **CHIPS's calculator** (`fpl_chips.own_week_points`): in the own week, a
  player with no own row counts 0 (source `no own`) in place of the own
  formula (`own-model`); the other weeks are unchanged (the own formula for
  gated players, 0 for gated-out and blank, every player on that one
  scale). Its header notes the rule. CHIPS's Free Hit screen calls
  `free_hit_table` and takes the amended metric with it.
- **Unchanged:** CHIPS reads the dated archive (amendment 3, point 3;
  Ruling 2: "CHIPS may stay one night behind"). Whether its Free Hit screen
  should read tonight's export instead is parked below, with a measurement.
- **The test** (`tests/test_W3fix.py`, red on the current code): the 12 Nov
  case. CHIPS's export (last night's) has a player at status `a` in the
  gate, with a high bottomup and no own row; tonight's export has him at
  `d`. Before: CHIPS's screen puts him in the FH XI and flags (gap > 8),
  and the base screen does not. After: both screens give the same FH XI
  points, gap and flag. Also: one of our flagged players without an own row
  counts 0 in "ours" in both screens, and in CHIPS's own week; weeks with
  no own rows are unchanged; the note names them.
- **Measured:** the suite before and after; the test red on the current
  code; mutations (bottomup back in `one_week_points`; `own-model` back in
  `own_week_points`; the note dropped) each red; the 12 Nov data
  (`6f9ecb8`) reproduced before (30.8, +8.5, flagged) and after; tonight's
  report, watch file and CHIPS before and after.

### Ruling 3, addendum pinned before its code (Mon 16 Nov, 18:05 UTC): W2's byte-identity

- Found by the suite: `tests/test_W2.ReportSections.test_byte_identical_to_the_tools`
  (W2's frozen rule) requires the runner's CHIPS section (`fpl_chips.live`)
  to print exactly what `tools/chips.py`'s `live` prints. The pin above named
  only `fpl_chips`, so the suite went red (1 failure, bare and with the data).
- Pinned: `tools/chips.py` takes the same three changes, byte for byte
  (`own_week_points`' own-week rule, the header note, the Free Hit screen's
  label), so W2's rule holds unchanged. Its other users,
  `tools/gw_pass.py` and `tools/planner.py`, then count a gated player
  without an own row 0 in the own week too (offline; on tonight's data no
  player is affected: "0 in this export").
- Parked for Boris (exact wording, with the other parked questions): "W2's
  byte-identity made Ruling 3 reach tools/chips.py, so the GW pass and the
  planner take the zero too. Keep that (a), or (b) amend W2's identity test
  to allow exactly Ruling 3's lines and leave tools/chips.py as it was?"

## Questions parked for Boris (exact wording), Mon 16 Nov 19:20 UTC, after the verifier's pre-check WARN (`worklog/verify_W3fix.md`)

Recorded late: the Ruling 3 pin said the CHIPS-export question was "parked
below, with a measurement" and it was not written here; the verifier found
the gap (its decision 1). The dry run waits for the answers.

1. **CHIPS's export.** "Under (a), CHIPS's Free Hit screen still reads last
   night's export, and its flag disagrees with the base screen's in 15 of 186
   week-rows since 19 Oct (the implementer's count; the verifier's over all 35
   data commits: 16 of 207), one of them an own week (1 Nov GW10: base +8.31
   flagged, CHIPS +7.95 not), the rest bottomup weeks around match days
   (before the change: 24 of 186). Make CHIPS's Free Hit screen read tonight's
   export, the base screen's own table, so the flag agrees by construction
   (i), or keep it on last night's export (ii)?"
2. **The not-'a' trigger** (the verifier's decision 2). "Under (a) a flagged
   player of ours without an own row counts 0 in the own week, so he drops
   out of our best XI: the gap rises (flags added on 2 of 35 past commits,
   none removed) and the trigger '3+ of our XI not a' can no longer fire in an
   own week (it reached 3 twice under the old metric, at most 1 under the
   new). Is that the intended reading of (a) (yes), or should the not-'a'
   count read our best XI before the zero (no)?"
3. **`tools/chips.py`** (in the addendum above, unchanged): "Keep the mirror
   (a), or (b) amend W2's identity test?"
4. **Surviving mutants** (the verifier's decision 4): five of its 35 survive -
   CHIPS's header note dropped; the note's gate count from every status-'a'
   player; float sums in `xi_lex`; a missing forecast counted 1 in `xi_lex`;
   own-model back in `tools/chips.py` alone. "Add small tests for them before
   the merge (yes), or accept them (no)?"
5. **The headers' export** (the verifier's decision 5): "CAPTAIN and BAN RISK
   now name the working export, `fpl_export_gw10.json`, which on a night the
   sync fails is the restored copy of last night's. Print the export's own
   `generated` time beside its name (yes), or leave it (no)?"

Measured besides (the verifier): 31 Oct GW10 also changes reason under the
new metric ("3 of our XI not 'a'" at +5.6 becomes "gap > 8" at +8.8), a
rollover night the implementer's script skipped.

## Answers, Thu 19 Nov night (Boris's message verbatim; for this item: the standing rule, points 1-5 (W3fix lands after the GW11 deadline, from Sat 21 Nov) and the dates)

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

## Answers of Thu 19 Nov night, pinned before their code (W3fix points 1, 2, 4, 5; Thu 19 Nov 21:10 UTC)

Committed locally before any code; pushed after tonight's nightly (mode (d):
the 21:00 UTC window covers master).

- **Point 1 (i), CHIPS's Free Hit screen on tonight's export:** the screen
  printed at the end of CHIPS (`fpl_chips.live`, and `tools/chips.py`'s
  `live` byte for byte, W2's identity) is built from tonight's working export
  (`fpl_ship.newest_export`, the file CAPTAIN and BAN RISK read since Ruling
  2) with tonight's log, so it is the base screen's own table. Its label names
  that export. No working export: one line, "FREE HIT SCREEN not built: no
  working export (...)", never last night's. The calculator above it (V_BB,
  V_FH, the induction) stays on the dated archive (amendment 3, point 3).
- **Point 2 (no), the not-'a' trigger:** `free_hit_table` counts "not a" on
  our best XI chosen by the metric before Ruling 3's zero (item N as frozen:
  own where recorded, else bottomup), so an injury crisis still shows; the gap
  ("ours") keeps the amended metric. The flag rule itself is unchanged.
- **Point 4, the five surviving mutants, one test each:** CHIPS's header note
  (fpl_chips and tools/chips); the note's gate count (a status-'a' player under
  45 minutes without an own row is not counted); float sums in `xi_lex` (its
  comparison key ties 0.1 + 0.2 with 0.3); a missing forecast in `xi_lex`
  counts 0 (a toy where 1 would start him); `tools/chips.own_week_points`'
  own-week rule on its own.
- **Point 5, the headers:** CAPTAIN's and BAN RISK's headers print the
  export's own `generated` time (UTC, to the minute) beside its name.
- **Tests:** each red on the current branch code (`7c40c6a`); the not-'a' rule
  on a toy where three of our XI are flagged without own rows; point 1 on a
  toy where last night's archive and tonight's export differ.
- **Measured:** the suite before and after; mutations; the 12 Nov case and
  tonight's report, watch file and CHIPS before and after; across the nightly
  data commits the CHIPS screen's flag equals the base screen's in every row.

## Questions parked for Boris (exact wording), Thu 19 Nov 22:25 UTC, after the re-check WARN of `5385c57` (`worklog/verify_W3fix.md`, appended)

The item stops (standing rule of Thu 19 Nov); its dry run and merge wait.
Every measured claim reproduced: CHIPS's screen equals the base screen on 38
of 38 replayed nights; the not-'a' count equals the pre-Ruling-3 code's on 228
of 228 week-rows; 884 OK three ways; no recorded row moves.

1. **The float-sum mutant.** "Point 4's test for the float-sum survivor checks
   xi_key with exact values it builds itself, so a float conversion inside
   xi_lex still passes (it changes no XI in 6,000 random squads on Python
   3.14). Add a small test of what xi_lex hands to its key (yes), or accept
   the gap (no)?"
2. **Four minor green mutants** (the screen's log read through the archive's
   deadlines; the frozen value by three-layer terms; the archive's table
   printed above the "not built" line; the generated time's "unknown"
   branch). "Add tests (yes), or accept them (no)?"
3. **The dry run's timing.** "May dry/W3fix be pushed during the freeze from
   Fri 20 Nov 05:00 UTC (a dry run writes nothing to data), or does it wait
   until after the GW11 deadline, Sat 21 Nov 11:00 UTC?"
4. **CHIPS's screen label.** "It says 'tonight's export' with no time; on a
   night the sync fails that file is the restored copy of last night's. Print
   its generated time there too, as in the CAPTAIN and BAN RISK headers
   (yes), or leave it (no)?"
5. **The changelog wording** (information, no answer needed unless you
   object): the Ruling 3 pin said the item N amendment lands before the GW11
   deadline; with the landing after it, the entry will say the amended screen
   starts with GW12.

## GW12 deadline pass message, Thu 26 / Fri 27 Nov (Boris's message verbatim; for this item: its last paragraph, the schedule after the GW12 deadline)

GW12 deadline pass (deadline today Fri 27 Nov 18:30 UTC; GW12 freeze: tools and worklog only). 1 free transfer, bank 0.5; Thiago banned until GW14.
1. git pull --ff-only in C:\GIT\FPL-data; run the GW12 bundle from clean master on the newest export; commit gw12_pass.txt, xp_v2_all.csv and run.txt to master under worklog/gw_pass/gw12/.
2. Transfer tables (1 FT, no hits): the best single moves and roll, under the gate and with Thiago lifted from GW14, and with Calafiori at P(start) 1.0 (his GW8 cameo is still in the window). Also the clean-sheet-flattened gain for the top three moves (information, as in GW11).
3. Captain: Arsenal v City is in our XI both ways. Print the captain table, xg, bottomup and bottomup_lambda for the top four, and the GW12 odds for ARS-MCI (each side's lambda and P(cs)).
4. Chips: S7 GW12-19 lines on the current 15 and on the best post-transfer squad, and bb_timing for GW14 v GW15 (the Bench Boost plan is GW14).
5. Post, no decisions, by 10:00 UTC. After Boris's real run (about 14:00 UTC, after the press conferences): refresh 1-4 and commit before 16:30 UTC.
After the GW12 deadline, runner changes resume (one per night, Boris clicks each real run): Fri 27 W3fix (with fj-wip's tests); Sat 28 runcommit plus the price-moves name fix plus the RMSE column; Sun 29 free. Then the GW13 freeze from Mon 30 Nov 12:30 UTC. Also draft F-N's prereg and post the parked questions in one batch.

## Rulings, Fri 27 Nov (Boris's message verbatim; for this item: W3fix answers 1-5)

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

## Answers of Fri 27 Nov, pinned before their code (Fri 27 Nov 12:40 UTC)

- **Answer 1 (the float-sum test):** a test with a spy on `xi_key` that asserts
  every value `xi_lex` hands it is a `Fraction` (the verifier's check, re-check
  section 3). It must be red on both green variants: `val` built with `float`,
  and an inline float key that bypasses `xi_key`.
- **Answer 2 (the four minor mutants, re-check Check 6), one test each, each red
  on its mutant:**
  1. the screen's log read through the archive's deadlines: a toy whose two
     exports have different deadlines;
  2. the frozen value by the three-layer terms rather than bottomup: a toy whose
     count depends on the scale;
  3. no working export, with the archive's table printed above the one line: the
     test checks the section holds that line and no table;
  4. an export with no readable `generated`: the section prints "unknown" and
     goes on.
- **Answer 4 (CHIPS's screen label):** the label prints the working export's
  generated time in the CAPTAIN and BAN RISK header form (`_gen`: UTC, minutes,
  "unknown" when unreadable). A test pins it, including the restored-copy case
  (the time is the copy's own field). The mirror in `tools/chips.py` gets the
  same label (W2's byte-identity).
- **Answer 3:** `dry/W3fix` is pushed at or after 19:30 UTC tonight. The merge
  is on Boris's click and finishes before 21:00 UTC. If the dry run or the
  verifier is not green by 20:45 UTC, or Boris is not available, it lands Sat 28
  in the same 19:30-21:00 UTC window and runcommit moves to Sun 29.
- **Answer 5:** the CHANGELOG entry says the amended screen starts with GW12.
- **Order:**
  1. Merge master into `w3fix-wip`.
  2. Make the changes above; run the suite before and after.
  3. The verifier's re-check of the new commit, then the write guard.
  4. The landing list: regenerate `checkpoint.txt` and `run.txt`; CHANGELOG;
     the report.
  5. `dry/W3fix` (at or after 19:30 UTC); tag `pre-W3fix`; the merge on
     Boris's click.
  6. Boris's real run; the final verifier.

## Question parked for Boris (exact wording), Fri 27 Nov 13:35 UTC, after the re-check WARN of `3847ebd` (`worklog/verify_W3fix.md` on `w3fix-wip` `e41cdaf`, appended)

The item stops (standing rule); its dry run and merge wait. Every measured
claim reproduces: 890 OK four ways; the label is the only changed line of the
654-line report; 0 recorded cells move; 39 of 42 new mutants red.

1. **The test for minor mutant 2.** "`OneScale.test_the_frozen_value_is_bottomup_with_all_terms`
   is red on the frozen value computed without the terms, but green on the same
   behaviour spelled `project_week(..., w, three_layer_terms(pos))`, because the
   toy player is a defender, for whom `three_layer_terms` returns `ALL_TERMS`.
   The pin asks for 'a toy whose count depends on the scale'. Pick the toy player
   from midfielders and forwards (a one-word change; the verifier showed both
   spellings red with it in scratch), then a short re-check, before tonight's
   19:30 UTC dry run (yes), or accept the gap (no)?"
2. **The spy of answer 1** (information; the verifier would accept it as it is):
   a value check in the spy (`val` equals `_exact` of each forecast) would also
   close a contrived variant that changes no XI in 9,000 random squads.
