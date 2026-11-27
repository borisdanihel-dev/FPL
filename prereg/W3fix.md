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

## W3fix WARN ruling, Fri 27 Nov (Boris's message verbatim)

W3fix WARN ruling (Fri 27 Nov):
1. Yes. Switch the minor-mutant-2 test's toy player to a midfielder. Re-check only this: the test against both forms of mutant 2, plus one full-suite run. Then push dry/W3fix at or after 19:30 UTC as planned.
2. The GW12 refresh comes first. Do the W3fix change only when it won't delay the refresh commit (due 16:30 UTC).
3. The 3 surviving mutants of 42: list each one in the report with a one-line reason it can't change behaviour. That doesn't block tonight. If any of them can change behaviour, park it as a new question.
4. If the re-check isn't green by 19:30 UTC, the fallback stands: W3fix lands Sat 28 between 19:30 and 21:00 UTC, and runcommit moves to Sun 29.

## Question parked for Boris (exact wording), Fri 27 Nov 14:20 UTC, from the WARN ruling's point 3 (`worklog/cc_2026-11-27_W3fix.md` on `w3fix-wip` `d701c7f`); it does not block tonight

The narrow re-check of `f1c3704` PASSED (`a552b15`). Of the 3 surviving mutants of 42, the
frozen-value one is now red. Two can change behaviour, in the offline checkpoint tool
the GW15 tie rule uses (not the runner):

1. **A decimal-tie test for `xi_lex`.** "Two of the three surviving mutants (the key
   called but ignored, and `Fraction(float(v))`) can change the GW15 tie rule's XI when
   two legal XIs tie as written decimals but not as binary floats. Add a toy test with
   such a tie (0.1 + 0.2 against 0.3), where the rule must pick by the id list, before
   GW15 (yes), or accept (no)?"

## Rulings, Fri 27 Nov 15:30 UTC (Boris's message verbatim; for this item: points 1 and 2; point 3 is the GW12 pass's, in prereg/bundle.md)

Rulings (Fri 27 Nov, 15:30 UTC):
1. Changelog wording "starts with GW13": accepted — correct.
2. Decimal-tie test (0.1+0.2 v 0.3, decided by the id list): yes. Test-only, in the offline checkpoint tool. It must turn both surviving mutants (xi_key result ignored; Fraction(float(v))) red and pass on real code. Not in tonight's W3fix landing. Land it on any non-freeze day before the GW15 freeze; Sun 29 is fine.
3. GW12 is locked from the refresh: roll, no chip, captain Muharemović, vice De Cuyper, XI and bench as in gw12_post_refresh.md. Nothing more needed for GW12.

## Question parked for Boris (exact wording), Fri 27 Nov 15:55 UTC, after the 15:30 ruling's point 2; it does not block tonight's landing

Evidence: `worklog/w3fix_tie/check.py`, run on `w3fix-wip` `3fe7500` (`worklog/w3fix_tie/out/check.txt` and
`run.txt`). The landing report and CHANGELOG entry on `w3fix-wip` are corrected (`05825ec`, `3fe7500`, docs only).

1. **The decimal-tie test cannot be built as ruled.** "My 14:20 claim was wrong. No 15 can have a
   decimal-but-not-binary tie at the top of `xi_lex`. Legal XIs are the bases of a matroid, so every XI tied
   at the top holds the same values: in 3,000 random squads there were 1,798 ties at the top and 0
   exceptions. The ruling's shape (0.1 + 0.2 against 0.3) gives a legal 0.2 + 0.3 mix at 0.5 instead. So
   `Fraction(float(v))` never changes the XI, and the ignored key changes it only through float rounding no
   forecast reaches. Two test-only tests turn both mutants red and pass on the code:
   - T1: the 0.1 + 0.2 against 0.3 tie on the values `xi_lex` hands `xi_key`, decided by the id list (red on
     `Fraction(float(v))`).
   - T2: `xi_lex` returns the XI its key ranks first (red on the ignored key).
   Land T1 and T2 on Sun 29 in place of the toy (yes), or accept both mutants as unable to change an XI (no)?"

## Ruling, Fri 27 Nov 16:00 UTC (Boris's message verbatim)

Ruling (Fri 27 Nov, 16:00 UTC): yes.
1. Land T1 and T2 on Sun 29 in place of the ruled decimal-tie test. Test-only, offline checkpoint tool. Both must pass on real code and, together, turn both mutants red.
2. Record in prereg/W3fix.md why the XI-level test can't exist: formation-legal XIs form a matroid, so by Gale's theorem every max-weight XI has the same sorted values, and different-value ties can't top xi_lex. Cite the 3,000-squad check (1,798 top ties, 0 exceptions).
3. Information, non-blocking: does any other caller (S15 builder, the FH/WC paths) use xi_lex's key function where a budget or club limit applies? Those constraints break the matroid property, so a different-value tie could top the ranking there. If yes, list the callers in the Sun 29 report. Don't fix anything yet.
4. Tonight unchanged: dry run 19:31 UTC from 3fe7500, merge on Boris's click before 21:00 UTC.

## Why the XI-level decimal-tie test cannot exist (the 16:00 ruling's point 2)

- **The matroid.** A formation-legal XI is 11 of the 15 with 1 GK, DEF 3-5, MID 2-5 and FWD 1-3. These XIs are
  the bases of a matroid: they satisfy the base exchange axiom. Take legal XIs A and B and a player a in A but
  not in B, of position p.
  - If A holds more players of p than B, some position q has fewer in A than in B. A player b of q in B but
    not in A exists, and A - a + b is legal: every count stays between A's and B's.
  - Otherwise B holds at least as many players of p as A. Then B has a player b of p that is not in A, and
    A - a + b keeps every count.
- **Gale's theorem.** In a matroid, the greedy basis's sorted weights are at least those of every other basis,
  place by place. So every basis of the highest total weight has the same sorted weights. With the weights
  `xi_lex` uses (`_exact`, the decimal written), every XI tied at the top holds the same sorted values.
- **So no different-value tie can top `xi_lex`.** A tie of 0.1 + 0.2 against 0.3 + 0.0 at the top would need two
  top XIs with different sorted values. Directly: with both XIs legal, the exchange gives a legal mix of one
  player from each pair that beats both. In the toy of `worklog/w3fix_tie/` that mix is 0.2 + 0.3 = 0.5.
- **The same argument covers `Fraction(float(v))`.** Which XIs score highest depends only on how the single
  values are ordered (they are the bases the greedy rule can produce), and the binary and the decimal value
  order them alike. So that mutant's tie set and id choice are the code's.
- **Measured** (`worklog/w3fix_tie/check.py` on `w3fix-wip` `3fe7500`; `out/check.txt`, `out/run.txt`): 3,000
  random 15s with forecasts on coarse decimal grids gave 1,798 ties at the top and 0 exceptions. Every tie's XIs
  held one multiset of values, and neither mutant changed an XI, a bench or a keeper.
- **Limit (point 3).** The argument needs the formation limits alone. A budget or a club limit (at most three a
  club) breaks the exchange axiom, so in a builder with those limits a different-value tie can top the ranking.

## T1 and T2, pinned before their code (Fri 27 Nov 16:05 UTC; the 16:00 ruling's points 1 and 3)

- **Where:** `tests/test_FJ.py`, class `GW15TieRule`, beside the `xi_lex` spy test. It is test-only, with no change
  to `worklog/checkpoint_gw10/checkpoint.py`. The branch is `w3tie-wip`, from `w3fix-wip` `3fe7500`, because
  `xi_lex` reaches master only with tonight's W3fix merge. It is rebased onto master after that merge.
- **T1, `test_a_decimal_tie_on_xi_lex_values_goes_to_the_smaller_ids`:**
  - Input: the class's TOY with PROJ, and DEF 13 at 0.1, MID 24 at 0.2, DEF 5 at 0.3 and FWD 300 at 0.0.
  - A spy on `xi_key` records the values `xi_lex` hands it.
  - A = the core (ids 1, 10, 11, 12, 20, 21, 22, 23, 30) + 13 + 24; B = the core + 5 + 300.
  - Asserts: both are legal; `xi_key(A, val)` and `xi_key(B, val)` have equal sums (the decimal tie); and
    `xi_key(B, val) < xi_key(A, val)`, so the smaller sorted ids win (5 < 13).
- **T2, `test_xi_lex_returns_the_xi_its_key_ranks_first`:**
  - `xi_key` is patched to rank the lowest exact sum first, then the sorted ids.
  - Asserts:
    - `xi_lex(TOY, PROJ)`'s XI is the first of every formation-legal XI under that key, computed in the test;
    - that XI is not the unpatched `xi_lex`'s, so the test cannot pass by coincidence.
- **The mutants**, exactly as in `worklog/w3fix_tie/check.py`:
  - m03: `xi_key` is called and its result ignored; float sums, then the ids.
  - m04: `val = Fraction(float(v))`.
  - T1 must be red on m04 and T2 red on m03, each in the full suite. Both must pass on the code.
- **Suites:** the whole suite by discovery before (890 on `3fe7500`) and after (892), plain and with
  `FPL_DATA_DIR`. After the rebase onto master, it runs again.
- **Then:**
  - a narrow verifier re-check (fable, high, the read-from-disk opening), then the write guard;
  - the report `worklog/cc_2026-11-29_W3fix_tie.md`, with point 3's answer;
  - the dry run `dry/W3fix_tie` in the 19:30-21:00 UTC window on Sun 29;
  - the merge on Boris's click, Boris's real run, and the CHANGELOG entry.
  - If runcommit falls to Sun 29 (the fallback), T1 and T2 take the next non-freeze evening before the GW15
    freeze: one runner change a night.
- **Point 3 (information), checked before the code:** no caller uses `xi_key` or `xi_lex` outside
  `worklog/checkpoint_gw10/checkpoint.py` (its `realised_lex` and `score(..., "id")`), `tests/test_FJ.py` and
  `worklog/w3fix_tie/check.py`, on any branch of origin (`git grep` over every remote branch).
  - `tools/builder.py` (S15) has its own `week_value` and a local search under the budget and club limits.
  - The Free Hit and Wildcard paths (`fpl_chips.free_hit_value`, `fpl_edge.sec_wildcard`, `_best_xi`) have
    their own selection.
  - The Sun 29 report states this; nothing is changed.

## Ruling, Fri 27 Nov 16:20 UTC (Boris's message verbatim)

Ruling (Fri 27 Nov, 16:20 UTC):
1. T1/T2 accepted: 890 → 892, each mutant caught by exactly one test, test-only, pinned before code. Point 3 (no other callers of xi_lex or its key) accepted.
2. Sequencing: Sun 29's slot goes to W4 (scheduled pre-deadline run) so it's live for GW13. T1/T2 land on any free night before the GW15 freeze: Sat 28 alongside runcommit is fine because they're test-only and don't count as the night's runner change; otherwise Tue 1 Dec after the GW13 deadline.
3. If the advance-approval rule (my 16:10 UTC rulings, point 1) is recorded, Boris approves T1/T2 in advance under it. If not, T1/T2 wait for his click.

### Session reading (Fri 27 Nov 16:20 UTC; amends the landing dates of the pin of 16:05, which is otherwise unchanged)

- **Point 3.** No "16:10 UTC rulings" have reached this session. No advance-approval rule is recorded in
  `prereg/`, `CLAUDE.md`, `BUILD_PLAN.md` or the state file. So T1 and T2 wait for Boris's click.
- **Point 2.**
  - T1 and T2 (`w3tie-wip`) land Sat 28 in the 19:30-21:00 UTC window, alongside runcommit, after a rebase onto
    master, the suite and a narrow verifier re-check. They have their own dry run (`dry/W3fix_tie`) and Boris's
    click.
  - If that window is missed, they land Tue 1 Dec after the GW13 deadline, with the same steps.
  - The report becomes `worklog/cc_<landing date>_W3fix_tie.md`.
- **W4** has no `prereg/W4.md` and no ruling text in this session; `BUILD_PLAN.md` names it only in the lane A
  queue (Part A, point 8). Its Sun 29 slot is recorded here and in the state file. Its prereg waits for its
  ruling text.

## Rulings, Fri 27 Nov 16:25 UTC (Boris's message verbatim; for this item: point 1's advance approvals, W3fix tonight and T1/T2 on Sat 28, and point 3's fallback)

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

### Advance approvals for this item, and how tonight's conditions are checked (session, Fri 27 Nov 16:35 UTC)

- **Recorded approvals (point 1):** W3fix tonight, dry run 19:31 UTC from `3fe7500`; and T1/T2 (`w3tie-wip`
  `82977fe`, after its rebase) on Sat 28.
- **Tonight, every condition is checked before the merge; any failure holds it and parks a question:**
  1. Verifier PASS: the latest verdict is the narrow re-check of `f1c3704`, PASS (`a552b15`). The commits since
     then (`1855108`, `d701c7f`, `05825ec`, `3fe7500`) touch only worklog, prereg, CHANGELOG and the checkpoint
     output.
  2. Dry run green: `dry/W3fix` pushed at or after 19:31 UTC from `3fe7500`, read back from `data-dryrun-W3fix`.
  3. The full suite passes on a fresh clone. The merge commit is made in a fresh clone of origin (origin/master
     merged with `w3fix-wip` `3fe7500`). The suite runs there by discovery, and that same commit is what gets
     pushed.
  4. The write guard is clean (git status and git diff in C:\GIT\FPL, the w3fix worktree and FPL-data).
  5. Inside 19:30-21:00 UTC.
  6. Not in a deadline freeze: the GW12 deadline is 18:30 UTC, and the GW13 freeze starts Mon 30 Nov 12:30 UTC.
  7. No other runner change tonight.
  8. Boris has not revoked it.
- **Then:**
  - tag `pre-W3fix` = master before the merge;
  - post the merge commit and the report in the worklog;
  - tonight's 21:40 UTC nightly is the first run on the merged code, and the final verifier reads it;
  - the "W3fix done" CHANGELOG entry;
  - delete `dry/W3fix` and `data-dryrun-W3fix`.

## Question parked for Boris (exact wording), Fri 27 Nov 16:35 UTC; for Sat 28, it does not block tonight

1. **T1/T2's advance approval on a runcommit night.** "Your 16:20 ruling says T1/T2 don't count as the night's
   runner change. The 16:25 rule's conditions include 'no other runner change that night', and runcommit is one
   on Sat 28. Merge T1/T2 under the approval alongside runcommit (yes), or hold T1/T2 for your click that night
   (no)?"

## Correction of session time labels (Fri 27 Nov; the commit times, UTC, govern)

Several of the session's own time labels today were written ahead of the clock. The sections are not edited;
these are the commit times. Boris's ruling labels are his own and unchanged.
- "Question parked ..., Fri 27 Nov 15:55 UTC": committed 15:52:31 (`89e3987`).
- "T1 and T2, pinned before their code (Fri 27 Nov 16:05 UTC ...)": committed **15:56:13** (`1ba55c2`), before
  the code (`82977fe`, 15:57:30). The order pin, then code holds.
- "Session reading (Fri 27 Nov 16:20 UTC ...)": committed 16:17:57 (`f1a4b54`).
- "Advance approvals for this item ... (session, Fri 27 Nov 16:35 UTC)" and "Question parked ..., Fri 27 Nov
  16:35 UTC": committed 16:23:02 (`86e50b3`).
- The W3fix report's "Corrected Fri 27 Nov 15:45 UTC" (on `w3fix-wip`): committed 15:47:22 (`05825ec`).
