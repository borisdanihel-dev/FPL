# GW12 refresh — information only, no decisions (Fri 27 Nov, ~14:10 UTC)

Deadline 18:30 UTC (19:30 Prague).

**Data:** your real run committed data `0768766` at 14:00 UTC with STATUS
WARN. The only warning is the standing 5 Nov price gap. The odds snapshot
`odds_2026-11-27T1400Z` prices 20 of 20 events, and all 10 GW12 fixtures come
from odds.

**Code:** everything ran from clean master `1b3b52b` with 0 modified files.
The outputs are in `worklog/gw_pass/gw12/refresh/`, each with its run file.
The morning's files are unchanged.

## Delta against data `2efc924` (`refresh/delta.txt`)
**0 items listed.** No number moved by more than 0.3 and no rank changed:
- XI and bench, own and xp_v2;
- both captains;
- every table's top five and roll's rank;
- the clean-sheet columns;
- the captain block and its order;
- S7's values and actions;
- bb_timing.

Largest moves:
- Murillo +0.05 in the tables. Rogers → Tavernier went 0.07 → 0.10.
- Van Hecke's xp_v2 went 5.37 → 5.41, De Cuyper's 5.57 → 5.55.
- Arsenal's P(cs) went 0.301 → 0.302.

Outside our 15 and the targets, B.Fernandes (MUN) and Alderete (SUN) dropped to
0, so tonight's run recorded 301 rows of own and xp_v2, not 303.

## The lean's numbers (roll, no chip, captain by the frozen rule)
| table | roll | best move |
|---|---|---|
| gated | rank 18, 0.00 | Calafiori → Silva (BOU) 3.44 (gain 4.44 − lost FT 1.00) |
| lifted (Thiago from GW14) | rank 18, 0.00 | Calafiori → Silva (BOU) 3.44 |
| gated, Calafiori at 1.0 | rank 3, 0.00 | Mbeumo → Tavernier (BOU) 0.16 |
| lifted, Calafiori at 1.0 | rank 3, 0.00 | Mbeumo → Tavernier (BOU) 0.13 |

Clean-sheet flattening, lifted:

| move | gain | flat A | flat B | CS share |
|---|---|---|---|---|
| Calafiori → Silva | 4.44 | 3.78 | 4.29 | 56% |
| Calafiori → Justin | 3.94 | 1.77 | 3.70 | 89% |
| Calafiori → Murillo | 3.82 | −1.11 | 3.54 | 74% |

**S7, GW12, current 15:**
- Values: HOLD 8.95, PLAY BB 8.85, PLAY FH 8.59.
- HOLD's margin is +0.10, 90% [−11.40, +16.59], same action in 74%.
- After Calafiori → Silva it is the same: HOLD +0.10, 74%.

**bb_timing, GW14 − GW15:** gated −0.58 (best week GW15); lifted +0.04 (best
week GW16).

**Captain by the frozen rule:**
- The highest xp_v2 in xp_v2's XI is **Muharemović 5.66**, then De Cuyper
  5.55 and Van Hecke 5.41.
- Own's captain is Gabriel 2.37.
- P(10+): De Cuyper 0.156, Van Hecke 0.133, Muharemović 0.120.

The XI is unchanged:
- xp_v2's XI, 4-4-2: Verbruggen; Muharemović, De Cuyper, Van Hecke, Gabriel;
  Groß, Mbeumo, Rogers, Rudoni; Haaland, Barry.
- Bench: Kelleher, Calafiori, Slater, Thiago.

## Flags (`refresh/flags.txt`)
- **Status:** 14 of our 15 are status a. Thiago is s, chance 0, "Suspended
  until 5 Dec". No other player of ours has news.
  - FPL's news time is not held (neither the export nor fpl.sqlite has it).
- **Cautions** (S12's count, league matches before the deadline):
  - **Groß 4, one booking from a ban, P(ban) 0.326**, and Thiago 4 (P(ban) 0,
    suspended).
  - The rest: De Cuyper 3, Rogers 3, Gabriel 2, Van Hecke 2, Mbeumo 2,
    Slater 2, Muharemović 1, Rudoni 1; Kelleher, Verbruggen, Calafiori,
    Barry and Haaland 0.
- **Targets:** all three are status a, no news, 4 starts in the last four,
  P(start) 1.00.

| target | price | xp_v2 GW12 | cautions | P(ban) |
|---|---|---|---|---|
| Silva (BOU) | 5.1 | 5.14 | **4, one from a ban** | 0.318 |
| Justin (LEE) | 4.5 | 5.61 | 1 | – |
| Tavernier (BOU) | 6.8 | 5.20 | **4, one from a ban** | 0.336 |

## W3fix (separate)
- The midfielder toy is committed on `w3fix-wip` as `f1c3704`: 890 OK plain
  and with the data, and the mutant-2 test is red on both forms.
- The verifier's narrow re-check is running. The dry run goes at 19:30 UTC.
