# GW11 refresh (point e) — information only, no decisions (Fri 20 Nov, ~19:55 UTC)

Deadline Sat 21 Nov 11:00 UTC (12:00 Prague).

**Data:** your real run committed data `fc543da` at 19:47 UTC with STATUS
WARN; the only warning is the standing 5 Nov price gap. The odds snapshot
`odds_2026-11-20T1947Z` prices all 20 events, against 19 this morning.

**Code:** everything ran from clean master `64b8df8` with 0 modified files.
- The bundle is commit `676dd33` (item 1).
- The rest is in `worklog/gw_pass/gw11/` (items 2-5).

The reading of items 3-5 was pinned in `prereg/bundle.md` before the code.

## What moved since this morning
- **xp_v2's captain is now Haaland, 5.69 against Gabriel's 5.66.** This
  morning it was Gabriel 5.65, Haaland 5.64.
  - Own still has Gabriel, 3.32 against 3.03.
  - The XI and the bench are unchanged.
- **Brighton v Newcastle (GW12) is now priced by odds** instead of the
  fallback. Brighton's GW12 P(cs) fell from 0.63 to 0.34. That cuts De
  Cuyper's GW12 gain from about +5 to about +2. Every De Cuyper plan's score
  falls by about 2.8, but the rankings hold.
- **Thomas** is 75%, as this morning. S7 and the ban risk are unchanged.
  bb_timing moved by 0.01.

## Item 2: transfer tables (2 free transfers, bank 0.9, no hits; xp_v2 GW11-16)
| case | best with BB: BB score / no-BB | best without BB: no-BB |
|---|---|---|
| gated | Thiago → N.Jackson + Thomas → De Cuyper: 18.80 / 10.73 | Calafiori → De Cuyper + Thomas → Van Hecke: 13.93 |
| lifted (Thiago from GW14; Thomas 75% in GW11, then normal) | the same pair: 15.84 / 9.64 | the same pair: 13.37 |
| Thomas 75% every week (information) | the same as lifted | the same as lifted |

**Thiago out only (roll one):** Thiago → N.Jackson, BB score 6.12 gated and
5.04 lifted.

**S7, unchanged from this morning:**

| squad | GW11 action | margin | same action |
|---|---|---|---|
| current 15 | PLAY FH | +0.17 | 13% |
| (a) the BB pair | HOLD | +0.06 | 77% |
| (b) the no-BB pair | HOLD | +0.12 | 78% |

**bb_timing (bench value on xp_v2):**
- Gated:
  - (a): GW11 14.37, best week GW14 15.64.
  - (b): best week GW15 11.07.
- Lifted: (a) and (b) are both 15.64 in GW14.
- GW11 ranks 5th of 6 weeks for every squad.

## Item 3: Calafiori at P(start) 1.0 (no BB; his xp_v2 rises by about 1.3 a week)
On the lifted matrix:

| plan | score | gain | rank |
|---|---|---|---|
| **best pair at 1.0: Tarkowski → De Cuyper + Thomas → Van Hecke** | 11.52 | 13.12 | 1 |
| Calafiori → De Cuyper + Thomas → Van Hecke | 7.81 | 9.41 | 26 |
| Calafiori → De Cuyper alone + roll one | 2.97 | 3.57 | 610 |
| Thomas → Van Hecke alone + roll one | **not legal**: bank 0.9 + Thomas 4.0 = 4.9 < 5.1 | | |

Beside it, Calafiori at the model's 0.75: Calafiori → De Cuyper + Thomas →
Van Hecke is the best pair (13.37), and Calafiori → De Cuyper alone scores
8.53.

Gated with Calafiori at 1.0: the same best pair, Tarkowski → De Cuyper +
Thomas → Van Hecke, at 12.18. The named Calafiori pair scores 8.38.

## Item 4: clean-sheet sensitivity
Only P(cs) is flattened, in GW11-16; the goals-conceded deduction, attack,
DEFCON and minutes are unchanged.
- **(A)** the team's realised 2026/27 clean-sheet rate.
- **(B)** the model's own mean over the team's six fixtures.
- **CS share** = (gain − gain with no CS term) / gain.

The four clubs of the moves:

| club | (A) | (B) | model P(cs), GW11-16 |
|---|---|---|---|
| ARS | 0.70 | 0.53 | 0.40 0.29 0.50 0.70 0.61 0.65 |
| BHA | 0.70 | 0.52 | 0.42 0.34 0.45 0.64 0.69 0.56 |
| COV | 0.10 | 0.12 | 0.24 0.14 0.12 0.08 0.09 0.05 |
| TOT | 0.40 | 0.39 | 0.37 0.31 0.60 0.34 0.44 0.29 |

| move (lifted) | gain | flat A | flat B | CS share |
|---|---|---|---|---|
| Calafiori at 1.0: Tarkowski → De Cuyper + Thomas → Van Hecke | 13.12 | 15.52 | 13.44 | 59% |
| Calafiori at 1.0: Calafiori → De Cuyper + Thomas → Van Hecke | 9.41 | 8.74 | 8.35 | 44% |
| Calafiori at 1.0: Calafiori → De Cuyper alone | 3.57 | 4.21 | 3.54 | 21% |
| Calafiori at 0.75: Calafiori → De Cuyper + Thomas → Van Hecke | 14.97 | 15.15 | 13.89 | 51% |
| Calafiori at 0.75: Calafiori → De Cuyper alone | 9.13 | 10.61 | 9.08 | 47% |
| Thomas → Van Hecke alone | not legal (budget) | | | |

The gain is the planner's decayed six-week gain before the lost-FT value. It
is not additive across terms, because the XIs are re-chosen in each column.

## Item 5: the captain tie
| | own | xg | bottomup | bottomup_lambda | xp_v2 (recorded) |
|---|---|---|---|---|---|
| Gabriel (ARS, at NEW) | 3.32 | 5.84 | 6.17 | 4.83 | 5.66 |
| Haaland (MCI, v FUL) | 3.03 | 5.96 | 4.63 | 4.63 | 5.69 |

**The opponents, in finished 2026/27 league matches:**
- Newcastle: 10 matches, scored 13 (1.30 a match), conceded 16 (1.60), 2
  clean sheets. At home: 5 matches, scored 6 (1.20), conceded 7 (1.40).
- Fulham: 10 matches, scored 10 (1.00), conceded 12 (1.20), 3 clean sheets.
  Away: 5 matches, scored 3 (0.60), conceded 4 (0.80).

**Tonight's odds:**
- NEW v ARS: λ 0.91 / 2.06, Arsenal's P(cs) 0.402.
- MCI v FUL: λ 2.51 / 0.94, City's P(cs) 0.390.

## Also (unchanged)
- **Flagged:** Thiago is suspended until 5 Dec. Thomas is 75% (calf).
- **Ban risk:** Groß is one booking from a ban, P(ban) 0.350.

**After the deadline:** a draft of prereg F-N goes to you for your ruling.
