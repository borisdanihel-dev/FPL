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

### The draft (Thu 12 Nov, for Boris's ruling; no code before it)

#### What the model does now (measured, `s8c-wip` `3a72ddb`, the GW11 matrix)

- The gate: a player whose status is not `a` has no value in any of the six
  weeks (`builder.live_matrix`, `tools/xp_v2_live.py` and the runner's
  `fpl_xpv2.py`: `gate = status == 'a'`). The status is today's, applied to
  every week.
- The chance is already inside the model: `fpl_edge.start_probability` gives
  P(start) = starts in the last four ÷ 4 × chance/100, and
  `xp_v2_live.core` scales P(sub) by the same chance. So lifting the gate for
  a `d` player gives exactly "P(start) × chance" for the next gameweek.
- One P(start) serves all six weeks, so lifting the gate alone leaves a `s`
  player at 0 in every week (chance 0). "As normal" must therefore mean the
  player taken as status `a` with no flag.

#### The rule as proposed, written against the code

| status | week t (the next gameweek) | later weeks |
|---|---|---|
| `a` | unchanged | unchanged |
| `d`, chance c | the gate lifted: P(start) × c, P(sub) × c (as the model already scales) | as normal: status `a`, no flag |
| `s`, ban end known | 0 for every club fixture before the ban ends | as normal from the first fixture on or after it |
| `i`, return unknown | 0 | 0 in week t+1; from t+2, as normal × the last known chance |
| `u`, `n` | 0 | 0 (unchanged) |

- The ban's end comes from the news text "Suspended until <date>"; the first
  club fixture kicking off on or after that date is the first one available.
- One function would serve the matrix (planner, bundle), the live week-t
  forecast and the runner's record. Week t changes for `d` players, so by
  the model-change protocol the new rule is recorded under a new source name
  (proposed `xp_v2_g2`; equal to `xp_v2` for every unflagged player) and
  replaces nothing until its test passes and Boris accepts it.

#### What it changes for our three players in the GW11 matrix

Export `fpl_export_gw10_2026-11-12`, odds `odds_2026-11-12T1745Z`, data
`6f9ecb8`; a copy of `builder.live_matrix` that equals it in every week with
nothing changed, and moves no other player (scratch, information only).

| player | status now | | GW11 | GW12 | GW13 | GW14 | GW15 | GW16 | sum |
|---|---|---|---|---|---|---|---|---|---|
| Thiago (BRE) | `s`, "Suspended until 5 Dec" | v1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| | | v2 | 0 | 0 | 0 | 4.71 | 4.26 | 5.26 | 14.22 |
| Thomas (COV) | `d`, 50%, calf | v1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| | | v2 | 1.26 | 2.15 | 2.32 | 2.08 | 2.14 | 1.90 | 11.84 |
| Calafiori (ARS) | `a` | v1 = v2 | 4.03 | 3.61 | 4.18 | 4.83 | 4.68 | 5.03 | 26.36 |

- Thiago: BRE's GW14 match is on 5 Dec, so he is out GW11–13 and back GW14,
  as the plan says. "As normal" uses P(start) 1.00 (four starts in the last
  four, GW10's red card included). By GW14 his real window will hold three
  missed matches, so the model will then read about 0.25: the matrix made
  today overstates his return weeks by the model's own later reading.
- Thomas: as normal, P(start) 0.50 (two starts in four); GW11 is half of it.
  At 1.26 he would still be our fifth defender in GW11 (Gabriel 5.62,
  Muharemović 4.42, Calafiori 4.03, Tarkowski 3.94), so the XI does not move.
- Calafiori is `a` now, so nothing changes. Before GW9 he was flagged, v1
  gave him 0 in the GW9 bundle, and he played 90 minutes for 6 points.
- Where it matters: the planner. Thiago's six-week value goes from 0 to 14.2
  and Thomas's from 0 to 11.8, so the planner would no longer see either as
  worth nothing beyond the next gameweek.

#### How it can be checked without archived historical flags

- The historical files (2025/26 and earlier) carry no status, chance or news
  by gameweek, so no historical backtest of the gate is possible (S6's
  replays took every player as available).
- Our own nightly exports do carry them: 53 dated exports on the data branch,
  from 11 Sep 2026 (before GW4) to now. The last export before each deadline
  gives the flags as they stood, point-in-time.
- **Retrospective check, 2026/27 GW4–10:** at each deadline, rebuild the v1
  and v2 matrices from the last export before it (and the odds snapshot
  before it where one exists, else the fallback, as the live matrix does).
  The W3 verifier has already rebuilt archived xp_v2 rows this way, exactly.
  Score every flagged player-week (status `d`, `s` or `i` at the deadline
  with 45+ minutes in the last four) in the horizon weeks already played
  (through GW10) against realised points.
- **Proposed primary metric:** the paired difference |v1 − realised| −
  |v2 − realised| per flagged player-week; bootstrap with unit = deadline
  gameweek, B 10,000, seed 20261018, 90%. **Proposed bar:** the 90% lower
  bound above 0 (v2 closer to what flagged players actually score).
- **Secondary, information:** F-M's own record: what our flagged players
  actually scored against v1 and v2, week by week.
- **Prospective:** from GW11 every nightly export is archived, so the same
  check grows weekly and is re-run at GW15 (F-M's revisit point).
- The sample is small (flagged players with 45+ recent minutes, seven
  deadlines), so the interval will be wide; the bar is stated before any
  number is seen.

#### Questions for Boris (exact wording)

1. "'i' with an unknown return: 'scaled by the last known chance' - FPL
   usually shows 0 for 'i', which would keep him at 0 for good. Use (a) the
   last non-zero chance in our archived nightly exports, (b) a fixed 50%, or
   (c) the chance shown now, even if 0?"
2. "'i' with a return date in the news (for example 'Expected back 28 Nov'):
   treat it like 's', 0 until that date then as normal?"
3. "'s' with no end date in the news: 0 for one gameweek, then as normal, or
   treat as 'i' with an unknown return?"
4. "Record the new rule under a new source name, xp_v2_g2, with the check
   above as its test and the bar as stated?"
5. "After a ban, P(start) falls because the banned matches count as missed
   starts in the last-four window (Thiago would read about 0.25 at GW14).
   Leave it (the model's own reading), or count suspended matches as neither
   started nor missed?"

## Rulings, Thu 12 Nov night (Boris's message verbatim; for this item: its part "FM, status gate v2" and the Schedule (Tue 17 Nov))

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
