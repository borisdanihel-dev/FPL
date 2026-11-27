# GW12 deadline pass — information only, no decisions (Fri 27 Nov, ~04:00 UTC)

Deadline Fri 27 Nov 18:30 UTC (19:30 Prague). 1 free transfer, bank 0.5.

**Data:** tonight's nightly committed data `2efc924` at 03:47 UTC with STATUS
WARN. The only warning is the standing 5 Nov price gap. The odds snapshot
`odds_2026-11-27T0347Z` prices all 20 events, so GW12 and GW13 are priced by
odds and GW14-17 by the fallback.

**Code:** everything ran from clean master `f587bce` with 0 modified files.
- The bundle is commit `71fb2ba` (point 1).
- The rest is in `worklog/gw_pass/gw12/` (points 2-4), each output with its
  run file.

The reading of points 2-4 was pinned in `prereg/bundle.md` before the code.

## Point 1: XI and captain (bundle)
- **xp_v2 (the default):**
  - XI 4-4-2: Verbruggen; Muharemović, De Cuyper, Van Hecke, Gabriel; Groß,
    Mbeumo, Rogers, Rudoni; Haaland, Barry.
  - Bench: Kelleher, Calafiori, Slater, Thiago.
  - Captain Muharemović 5.66 (LEE v COV at home, P(cs) 0.43).
- **Own:**
  - XI 5-3-2 with Calafiori in and Mbeumo on the bench.
  - Captain Gabriel 2.37.
- 12 slots differ.

## Point 2: transfer tables (1 free transfer, no hits; xp_v2 GW12-17)
Calafiori's model P(start) is 0.75. At 1.0 his xp_v2 rises by about 1.1-1.5
a week (GW12 3.59 → 4.69).

| case | best single move | score | gain | 2nd | roll |
|---|---|---|---|---|---|
| gated | **Calafiori → Silva (BOU, 5.1)** | 3.44 | 4.44 | Calafiori → Justin (LEE, 4.5) 2.94 | rank 18 of 267 |
| lifted (Thiago from GW14) | the same | 3.44 | 4.44 | the same | rank 18 |
| gated, Calafiori at 1.0 | Mbeumo → Tavernier (BOU, 6.8) | 0.16 | 1.16 | Rogers → Tavernier 0.07 | **rank 3** (0.00) |
| lifted, Calafiori at 1.0 | Mbeumo → Tavernier (BOU, 6.8) | 0.13 | 1.13 | Rogers → Tavernier 0.07 | **rank 3** (0.00) |

**Gated and lifted:**
- All of the top five sell Calafiori. Ranks 3-5 are Murillo (NFO) 2.77,
  Araujo (LIV) 2.77 and Hill (BOU) 2.57.
- Thiago's lift moves nothing in the top five.
- The simple rule beside the default picks Calafiori → Justin.

**With Calafiori at 1.0:** no move sells him, and the best move beats rolling
by 0.16.

**S8's own planner (information):** Thiago → N.Jackson (AVL), 4.06. Its
baseline is Thiago → McBurnie (HUL).

**Clean-sheet sensitivity (information):**
- Only P(cs) is flattened, GW12-17; everything else is unchanged.
- **(A)** the realised 2026/27 clean-sheet rate; **(B)** the model's own mean
  over the six fixtures.

| club | (A) | (B) | model P(cs), GW12-17 |
|---|---|---|---|
| ARS | 0.64 (7 of 11) | 0.49 | 0.30 0.36 0.61 0.52 0.59 0.54 |
| BOU | 0.36 (4 of 11) | 0.33 | 0.26 0.24 0.46 0.20 0.39 0.42 |
| LEE | 0.36 (4 of 11) | 0.41 | 0.43 0.12 0.51 0.35 0.69 0.38 |
| NFO | 0.09 (1 of 11) | 0.34 | 0.25 0.37 0.18 0.48 0.51 0.25 |

| move (lifted) | gain | flat A | flat B | no CS | CS share |
|---|---|---|---|---|---|
| Calafiori → Silva (BOU) | 4.44 | 3.78 | 4.29 | 1.96 | 56% |
| Calafiori → Justin (LEE) | 3.94 | 1.77 | 3.69 | 0.43 | 89% |
| Calafiori → Murillo (NFO) | 3.77 | −1.13 | 3.50 | 0.96 | 74% |
| Calafiori at 1.0: Mbeumo → Tavernier (BOU) | 1.13 | 1.61 | 1.20 | 0.69 | 39% |
| Calafiori at 1.0: Rogers → Tavernier (BOU) | 1.07 | 1.19 | 1.14 | 0.69 | 35% |
| Calafiori at 1.0: Kelleher → A.Becker (LIV) | 0.82 | 0.00 | 0.00 | 0.01 | 99% |

Notes on the table:
- **Calafiori → Silva stays first under every reading.**
- Under (A), Justin and Murillo fall away: Arsenal's realised rate (0.64) is
  above Leeds' (0.36) and Forest's (0.09).
- A.Becker's gain comes only from weeks he would outscore Verbruggen. Once
  flattened, he never does.
- The gain is the planner's decayed gain, before the lost-FT value.

## Point 3: captain (Arsenal v City in our XI both ways)
| player | xp_v2 | own | xg | bottomup | bottomup_lambda | why listed |
|---|---|---|---|---|---|---|
| Muharemović (LEE) | 5.66 | 1.99 | 5.99 | 5.67 | 4.90 | xp_v2 and own top 4 |
| De Cuyper (BHA) | 5.57 | 1.68 | 5.95 | 5.94 | 4.93 | xp_v2 top 4 |
| Van Hecke (TOT) | 5.37 | 2.21 | 5.86 | 5.02 | 4.61 | xp_v2 and own top 4 |
| Groß (BHA) | 5.30 | 1.51 | 5.27 | 4.64 | 4.64 | xp_v2 top 4 |
| Gabriel (ARS) | 4.95 | 2.37 | 5.21 | 5.05 | 4.18 | own top 4, ARS-MCI |
| Haaland (MCI) | 4.76 | 1.49 | 6.04 | 4.78 | 4.78 | ARS-MCI |
| Rogers (CHE) | 4.59 | 1.81 | 5.20 | 4.06 | 4.06 | own top 4 |
| Calafiori (ARS) | 3.59 | 1.27 | 3.41 | 3.68 | 3.03 | ARS-MCI (xp_v2 bench) |

- **Within 0.3 of xp_v2's captain:** De Cuyper and Van Hecke.
  - P(10+), from S14 (information): De Cuyper 0.156, Van Hecke 0.132,
    Muharemović 0.120.
- **Own captain table:** Gabriel first, with Van Hecke 0.17 behind.
  Muharemović is the allowed differential (threat-set EO 0.00).
- **The GW12 odds for ARS v MCI** (41 h2h and 18 totals books):
  - λ ARS 1.71, λ MCI 1.20.
  - P(cs): Arsenal 0.301, City 0.181.

## Point 4: chips
**S7 (own; chips left BB and FH), GW12-19 lines:**
- The current 15 is the bundle.
- (a) is after Calafiori → Silva (bank after 1.2).

| GW | V_BB now / (a) | V_FH now / (a) | action with all chips (both) |
|---|---|---|---|
| 12 | 3.24 / 3.24 | 5.24 / 4.60 | HOLD |
| 13 | 2.98 / 2.98 | 5.15 / 4.74 | HOLD |
| 14 | 2.96 / 2.96 | 4.79 / 4.09 | HOLD |
| 15 | 3.25 / 3.25 | 5.60 / 5.60 | PLAY FH |
| 16 | 2.74 / 2.74 | 4.14 / 3.44 | HOLD |
| 17 | 3.14 / 3.14 | 4.74 / 4.45 | PLAY FH |
| 18 | 3.35 / 3.35 | 4.72 / 4.03 | PLAY FH |
| 19 | 3.14 / 3.14 | 5.75 / 5.46 | PLAY BB |

GW12 action: HOLD on both squads.
- Margin +0.10 over the best other action.
- 90% interval [−11.40, +16.59] now and [−11.40, +16.65] for (a).
- Same action in 74% of resamples.

**bb_timing (bench value on xp_v2, squad held):**

| case | squad | GW12 | GW13 | GW14 | GW15 | GW16 | GW17 | GW14 − GW15 | best week |
|---|---|---|---|---|---|---|---|---|---|
| gated | current 15 | 9.50 | 9.67 | 11.09 | 11.67 | 11.00 | 10.98 | −0.58 | GW15 |
| gated | (a) | 10.13 | 9.81 | 11.09 | 11.67 | 11.00 | 10.98 | −0.58 | GW15 |
| lifted | current 15 | 9.50 | 9.67 | 14.97 | 14.93 | 15.21 | 15.08 | +0.04 | GW16 |
| lifted | (a) | 10.13 | 9.81 | 14.97 | 14.93 | 15.21 | 15.08 | +0.04 | GW16 |

- The GW14 bench, lifted: Kelleher 3.50, Barry 4.40, Thiago 3.88, Slater 3.19.
- From GW14, Calafiori → Silva leaves the bench unchanged.

## Also
- **Flagged:** Thiago is suspended until 5 Dec (no xp_v2). The other 14 are
  status a.
- **Ban risk (tonight's report):** Groß is one booking from a ban, P(ban)
  0.326.

**Today:** after your real run (about 14:00 UTC), I refresh points 1-4 and
commit before 16:30 UTC. After the deadline come the W3fix landing and the
F-N draft.

## Parked questions, one batch
The wording is exact, from the prereg files.

### W3fix
Parked Thu 19 Nov 22:25 UTC, after the re-check WARN of `5385c57`
(`prereg/W3fix.md`). The item stops; its dry run and merge wait.

1. **The float-sum mutant.** "Point 4's test for the float-sum survivor checks
   xi_key with exact values it builds itself, so a float conversion inside
   xi_lex still passes (it changes no XI in 6,000 random squads on Python
   3.14). Add a small test of what xi_lex hands to its key (yes), or accept
   the gap (no)?"
2. **Four minor green mutants** (the screen's log read through the archive's
   deadlines; the frozen value by three-layer terms; the archive's table
   printed above the "not built" line; the generated time's "unknown"
   branch). "Add tests (yes), or accept them (no)?"
3. **The dry run's timing** (updated for today; the original asked about the
   GW11 freeze). Your schedule lands W3fix after today's deadline. Dry runs
   skip from 17:30 to 19:30 UTC (1 h either side of the deadline) and from
   21:30 UTC, and master takes no push from 21:00 UTC. That leaves 19:30-21:00
   UTC for the dry run, the merge and your real run. "May dry/W3fix be pushed
   before the deadline today (a dry run writes nothing to data), or does it
   wait for 19:30 UTC?" If 1 or 2 is yes, the new tests get a short re-check
   before the dry run.
4. **CHIPS's screen label.** "It says 'tonight's export' with no time; on a
   night the sync fails that file is the restored copy of last night's. Print
   its generated time there too, as in the CAPTAIN and BAN RISK headers
   (yes), or leave it (no)?"
5. **The changelog wording** (information, no answer needed unless you
   object): the Ruling 3 pin said the item N amendment lands before the GW11
   deadline; with the landing after it, the entry will say the amended screen
   starts with GW12.

### runcommit
Parked Fri 20 Nov 00:55 UTC, after the pre-check WARN of `7f44c65`
(`prereg/runcommit.md`). It lands Sat 28 with the price-moves fix and the RMSE
column.

1. **The bug as it happened.** "With the name lookup put back on the previous
   export's side, the suite stays green and tonight's report prints Hull's
   Thomas move again (the toy only catches the current-side lookup). Add tests
   with the namesake after our player in the previous export, for all three
   blocks (yes), or accept (no)?"
2. **Two pinned tests missing.** "No test reads FORM MOVERS, and no test passes
   GITHUB_SHA through checks.main for a real and a dry run. Add both (yes), or
   accept (no)?"
3. **No substitute, everywhere.** "'Never a substitute' is tested for
   checks.code_commit only. Add a decoy variable to the log and message tests
   (a), or route all three records through checks.code_commit (b)?"
4. **Calibration wording and checks.** "Add value checks for the calibration
   summary line and the two surviving verdict cases, and name RMSE and rconst
   in the section's DEFINITIONS and the minutes note (yes), or leave the
   report text as pinned (no)?"
5. **The merge date.** "The pin and the code were made before the GW11
   deadline on a work branch. Confirm that 'After the GW11 deadline' governs
   the merge only (yes)?"
6. **Order with W3fix** (information): whichever of W3fix and runcommit lands
   second is rebased onto the first and gets a short re-check before its dry
   run. On your schedule, runcommit is second.

### F-N (for its prereg draft after the deadline)
7. **"Season-average" clean-sheet rate.** Which reading does F-N test on
   2024/25:
   - (A) the team's realised clean-sheet rate before each deadline;
   - (B) the model's own mean P(cs) over the planner's six fixtures;
   - or both, as two pre-registered arms?
