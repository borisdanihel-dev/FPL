# GW11 pass — information only, no decisions (Fri 20 Nov, 02:45 UTC)

Deadline Sat 21 Nov 11:00 UTC (12:00 Prague). Tonight's nightly ran on data
`0a54132`, committed 02:35 UTC with STATUS WARN; the only warning is the
standing 5 Nov price gap. The bundle ran from clean master `352dd36` with 0
modified files. Everything is committed in `worklog/gw_pass/gw11/` (master
`cc51a47`). The tables in this post use 2 free transfers, bank 0.9 and no
hits.

**What changed since the 19 Nov test:** Thomas went from 50% to **75%**
(calf). N.Jackson rose from 7.1 to 7.2. The best plans did not change.

## Flagged players (status not 'a')
- **Thiago** (BRE FWD): suspended until 5 Dec, s, chance 0. The picks treat
  him as 0. If he played, own would give him 1.61.
- **Thomas** (COV DEF): calf injury, 75%, d. The picks treat him as 0. If he
  played, xp_v2 would give him 1.88 (P(start) 0.38) and own 0.62.

## Own and xp_v2 side by side (GW11)
The XI is the same 11 players under both. Only slots 7 and 8 swap order
(Rudoni and Rogers).

| | own | xp_v2 as tested |
|---|---|---|
| GK | Verbruggen 2.17 | Verbruggen 3.88 |
| DEF | Gabriel 3.32, Muharemović 1.85, Calafiori 1.80, Tarkowski 1.25 | Gabriel 5.65, Muharemović 4.45, Calafiori 4.06, Tarkowski 4.00 |
| MID | Groß 1.86, Rudoni 1.84, Rogers 1.63, Mbeumo 1.45 | Groß 5.31, Rogers 4.95, Rudoni 4.78, Mbeumo 4.66 |
| FWD | Haaland 3.03, Barry 2.04 | Haaland 5.64, Barry 4.87 |
| bench | Kelleher 1.42, Slater 0.91, Thiago 0, Thomas 0 | Kelleher 3.19, Slater 3.12, Thiago 0, Thomas 0 |
| captain | Gabriel 3.32 | Gabriel 5.65 |

Under the standing rule (from GW8), xp_v2 as tested picks the XI, the bench
and the captain.

## Captain table
- **xp_v2 points distributions (S14, information only):**
  - Gabriel: 5.65, P≥10 0.141, P≥15 0.027, p90 11.
  - Haaland: 5.64, P≥10 0.171, P≥15 0.036, p90 12.
  - Haaland is within 0.3 of Gabriel, which is information only: the
    captain rule is unchanged and there is no tie-break.
  - Next: Groß 5.31, Rogers 4.95.
- **Own captain table:**
  - Gabriel: 3.32, EO 0.38.
  - Haaland: 3.03, EO 2.00, cost 0.29.
  - No allowed differential.

## Ban risk (S12's rule)
- **Groß** (BHA): 4 cautions, one booking from a ban, P(start) 1.00, so
  **P(ban) 0.350**.
- **Thiago**: 4 cautions, but P(start) 0, so P(ban) 0.

## Planner
- **xp_v2 no-hit default** (the tool's 1 free transfer): Calafiori → De
  Cuyper (BHA 5.5). Score 10.90.
- **The simple rule beside it:** Tarkowski → Van Hecke (TOT 5.1).
- **S8 on own** (2 free transfers):
  - Top plan: Thiago → N.Jackson (AVL 7.2) and Thomas → Van Hecke (TOT
    5.1), score 8.86.
  - Baseline: Thiago → N.Jackson.

## Transfer tables (2 free transfers, bank 0.9, no hits)
The score is S8's on xp_v2 over GW11-16. The BB score counts GW11's bench at
full weight.

| case | best with BB (BB score / no-BB) | best without BB (no-BB) |
|---|---|---|
| gated (Thiago, Thomas 0) | Thiago → N.Jackson + Thomas → De Cuyper: 21.54 / 13.48 | Calafiori → De Cuyper + Thomas → Van Hecke: 16.74 |
| lifted (Thiago from GW14; Thomas at 75% in GW11, then normal) | the same pair: 18.57 / 12.40 | the same pair: 16.18 |
| information: Thomas at 75% every week | the same as lifted | the same as lifted |

- The every-week version equals the lifted one because Thomas sits on the
  bench after GW11 in both.
- **Named options:**
  - Thiago + Thomas out: the best pair is the BB pair above.
  - Thiago out only (roll one): Thiago → N.Jackson, BB score 6.11 gated and
    5.02 lifted; no-BB 2.11 gated and 1.02 lifted.

## S7 chips on the current 15 and the two best squads
Own xP. The margin is over the best other action, with a 90% interval from
1000 resamples.

| squad | GW11 action | margin | 90% interval | same action |
|---|---|---|---|---|
| current 15 | PLAY FH | +0.17 | [-45.37, +10.90] | 13% |
| (a) the BB pair | HOLD | +0.06 | [-11.15, +16.08] | 77% |
| (b) the no-BB pair | HOLD | +0.12 | [-10.41, +17.11] | 78% |

The Free Hit value assumes no transfers (our 15 held fixed), so it is an
upper bound. The Free Hit screen for GW11 gives an FH XI of 28.7 against
ours at 22.7.

## bb_timing (bench value on xp_v2, squad held GW11-16)
| squad | GW11 | GW14 | GW15 | best week (gated / lifted) |
|---|---|---|---|---|
| current 15 | 6.30 / 8.18 | 6.44 / 13.07 | 7.60 / 13.21 | GW15 / GW15 |
| (a) | 14.36 | 15.64 | 15.15 | GW14 / GW14 |
| (b) | 10.30 / 10.30 | 10.98 / 15.64 | 11.07 / 15.15 | GW15 / GW14 |

GW11 ranks 5th of 6 weeks for every squad.

## Calibration through GW10: RMSE as information
These figures come from runcommit's RMSE column on `runcommit-wip`, which has
not landed.
- **own:** MAE 2.082 against the constant's 2.308, so it beats the constant.
  On RMSE it loses: 3.098 against 3.062.
- Own's bias has run low, from -0.96 to -1.53 in GW7-10.
- **xg** loses on both measures.
- **fpl_ep** beats the constant on both.

## Parked questions (in the preregs and the state file)
- **W3fix** (5), in `prereg/W3fix.md`:
  1. the float-sum mutant's test;
  2. four minor surviving mutants;
  3. `dry/W3fix` in the freeze or after the deadline;
  4. the generated time on CHIPS's screen label;
  5. the changelog says the amended screen starts with GW12.
- **runcommit** (6), in `prereg/runcommit.md`:
  1. the test with a namesake bought after;
  2. FORM MOVERS and `checks.main` tests;
  3. "no substitute" everywhere, a or b;
  4. the calibration value checks and wording;
  5. the merge date;
  6. the order with W3fix.
- **FM:** the result stands, not passed. Answer 3 is done on `fm-wip`
  `dfb4691`:
  - point 5 alone: n = 72, −0.315;
  - our own flagged players: n = 38, −0.253;
  - main()'s end-to-end test is in.

Next: point e, Friday's refresh after your real run (~15:00 UTC), committed
before 18:00 UTC.
