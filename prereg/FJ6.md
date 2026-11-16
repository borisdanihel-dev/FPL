# FJ6 — the chip plan for GW11–19 (first-half Bench Boost and Free Hit; BUILD_PLAN Part F item F-J (6))

Committed before any code or run for this item. Offline, information for
Boris's chip decision; no runner change. Due: run by Wed 18 Nov, posted Wed
18 Nov, before the GW11 deadline (Sat 21 Nov 11:00 UTC). The design is pinned
in an addition to this file before the run.

## The rulings (verbatim)

### BUILD_PLAN Part F, F-J (RULINGS PART F, 19 Oct 2026)

F-J. GW10 checkpoint (Step 20), after GW10 locks down (about Mon 9 Nov): (1) the revert rule on GW8-10, per squad-gameweek paired differences on our squad and 50 squads sampled from 2026/27 GW1 ownership, using the recorded pre-deadline rows; (2) S6's validation rerun (cut 6); (3) F-E adoption if it passed; (4) every source's accuracy report and drift; (5) the DEF calibration re-check; (6) a chip plan for GW11-19.

### Boris's rulings of Thu 12 Nov night (verbatim; FJ point 3 and the Schedule's Wed 18 Nov are this item)

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

## Answers, Mon 16 Nov (Boris's message verbatim; for this item: the Revised schedule's Wed 18 (offline: the GW11-19 chip plan, S7 on candidate post-transfer squads with Thiago (banned GW11-13) and Thomas out, bb_timing with xp_v2 and xp_v2_g2, posted for the chat))

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
