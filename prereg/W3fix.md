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
