# FM — status gate v2 (BUILD_PLAN Part F item F-M, brought forward from GW15)

Committed before any code for this item: a prereg draft only. Boris rules
before any code (plan item 5).

## The rulings (verbatim)

### BUILD_PLAN Part F, F-M

F-M. Recorded by the Ruling of Tue 20 Oct, 21:00 Prague, point 3 (record only, no code), verbatim: "Record in BUILD_PLAN Part F as F-M (no code): the status gate drops 'd' players entirely whatever their chance. Each week, record what our flagged players actually score; revisit at GW15 with a prereg if the gate is costing points."

### Boris's plan of Sun 8 Nov (verbatim; its item 5 is this item)

International break plan, Sun 8 Nov (the item count resets to 0 of 6). GW11 deadline Sat 21 Nov 11:00 UTC; GW11 freeze from Fri 20 Nov 05:00 UTC. One runner change per night; no merges without Boris's click.
1. Mon 9 Nov: W3 merge (with the +02:00 committer test, the fetch-depth comment and the captain-without-row test); Boris clicks the real run.
2. Tue 10 Nov: the S8c landing (with the commit-signing test fix); Boris clicks the real run.
3. Wed 11 Nov: runcommit (real runs record their code commit), plus a fix for the nightly report's price-moves section matching players by name (it showed Coventry's Thomas at 5.5 -> 4.0; that was Hull's Thomas).
4. GW10 checkpoint once GW10 is locked (data_checked): BUILD_PLAN Step 20 and F-J: the paired own v xp_v2 metric over GW8-10 from the pre-deadline bundle CSVs and the projection log, the revert rule, and the model re-grade. Report only; no change without Boris.
5. Status gate v2 (F-M, brought forward from GW15): draft the prereg only, no code yet. Proposal: status 'd' = P(start) x chance in the next gameweek and as normal after; 's' = 0 for the known ban length, then as normal (Thiago: GW11-13 out, back GW14); 'i' with an unknown return = 0 for two gameweeks, then scaled by the last known chance. State how it can be checked, given that historical flags aren't archived. Boris rules before any code.
6. Step 16: finish it (type the 2026/27 cup and European CSVs, the verifier's row checks, the single backtest run, the report), then Step 18's prereg (the second-half chip plan).
Thu 19 Nov: the GW11 bundle, with Thiago and Thomas out, on Boris's paste.

### Boris's rulings of Thu 12 Nov (verbatim; point C is this item)

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

## The draft

To follow in this file, before Boris's ruling.
