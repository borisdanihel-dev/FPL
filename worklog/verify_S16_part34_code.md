# Verifier report: S16 parts 3-4, the code before its one real run

- Item: Step 16 parts 3-4 (the cup Monte Carlo and its point-in-time backtest), code commit `faf0d73` on `s16b-wip`, diff `53ba782..faf0d73`.
- Verifier: `backtest-verifier`, model Fable 5.1 (`claude-fable-5-1`), `.claude/agents/backtest-verifier.md` read from disk first (it governs). Thu 5 Nov 2026.
- Scope: the code, its tables and its tests, before the backtest's one run. Not in this pass: re-checking each CSV row against its source (F-I (2), the final verifier), the 2026/27 CSVs (they do not exist yet).

## The hard limit was kept

I did not run the backtest and computed no score on real outcomes. No `--run-once`; `cup_backtest.run`, `records`, `bss`, `bootstrap`, `reliability`, `report` and `base_rates` were never called on the real files by me; `Season.actual` was never read by me. The only thing I ran on real inputs was `cup_backtest.forecast` at n = 400 for the ten origins, and I compared those forecasts with other forecasts (truncated inputs, mutants), and inspected their shape (how many targets are 0, 1 or in between). Nothing I print pairs a forecast with what happened. Check 3 of the agent file (re-run the pre-registered evaluation) therefore does not apply yet, and I did not attempt it.

## Prereg and order of commits: PASS

`prereg/S16.md` carries the rulings verbatim (BUILD_PLAN Step 16 points 3-4; RULINGS PART F, F-I; Tue 20 Oct point 4; Wed 21 Oct point 3) and the pinned design (`df287ca`, 21 Oct), the amendment of 5 Nov (`f3b6b54`, 03:12:49 +0100) and "Item 6 sharpened" (`53ba782`, 03:16:02 +0100). The code commit `faf0d73` is 03:26:32 +0100. Both amendment commits precede it; both say no backtest run has been made.

## 1. Point-in-time: PASS (with one text-accuracy note)

**1a. Truncation test (decides): PASS.** `verify_pit.py` (my script, `python -I`, in a `git archive` copy of `faf0d73`), n = 400, seed 20261021, for all ten origins (GW10/15/20/25/30 of 2024/25 and 2025/26). For each origin the forecast from the full inputs was compared with the forecast from inputs truncated at the origin's UK date: every cup row with `draw_date` on or after the origin removed (66/34/32/7/1 rows in 2024/25; 66/66/32/15/3 in 2025/26), the `winner` of every tie not played before the origin replaced by a dummy (4/36/34/9/2; 4/4/34/17/5 ties), every league result dated on or after the origin removed (4431/4161/3848/3491/3018; 1834/1558/1239/963/569 rows). All ten pairs are identical as Python dicts of floats (exact equality, not a tolerance): `TRUNCATION: all 10 origins identical = True`.

**1b. Timestamp audit (decides): PASS, one note.** What each origin reads, confirmed in the code and by the probe:
- League results: `elo` skips `d >= before`; `clubs_by_tier` reads `[1 Jul, origin)`. Probe: the last result read at each origin is the day before the origin date (e.g. GW10 2024/25 origin 2024-11-02, last result 2024-11-01; 4431 later rows excluded).
- Cup rows: `cup_state` counts a round as drawn only if every `draw_date` is before the origin date and every tie of the round before it has its last `tie_date` before the origin date (amendment items 3-4); a winner is read only when the tie's last date is before the origin. The probe's per-origin state matches the amendment's text: the FA Cup R3 is drawn at random (the 44 + 20 field) at GW10 of both seasons and GW15 of 2025/26 (R3 draws 2024-12-02 and 2025-12-08 against origin dates 2024-11-02, 2025-11-01, 2025-12-06), and is "drawn, 0 of 32 played" at GW15 2024/25 and GW20 of both seasons.
- `round_dates.csv`: read for every round regardless of origin. For 2024/25 and 2025/26 these are the earliest tie dates of each round, a stand-in for the published dates, as the amendment pins. For the three blank rounds (Wembley dates and the QF weekend) the stand-in is the published weekend; for the midweek rounds a stand-in could differ from a pre-season date only if a whole round moved, which did not happen in either season.
- `fixtures.csv`: `id`, `team_h`, `team_a` (published before GW1), and `event` and `kickoff_time` (the final schedule). The amendment's stated limit names `kickoff_time` as "the only later information read" and says it "never carries a postponement (those leave the id block)". That is incomplete: the filter `event == block` reads `event`, which is exactly the information of which fixtures left the block. It feeds the deadlines, the blank-round days and the midweek table. Concrete case, from the prereg's own part 1 fact (GW15 2024/25, EVE-LIV postponed for weather): the computed GW15 deadline is Sat 2024-12-07 13:30 UTC (the earliest fixture still in the block, 15:00), while FPL's was 11:00 UTC (the postponed 12:30 fixture). The origin's UK date is unchanged (7 Dec), no Wednesday-noon window can move, so no forecast changes in these seasons; and the filter is what keeps a fixture replayed earlier than its block (2024/25 GW34 -> GW33) from pulling a deadline forward. Recommendation: a one-line amendment naming `event` as the second later field read, with this case; no code change.
- `Season.actual` is read only by `records` (the scoring); `simulate` reads `original`, `base`, `days`, `deadline`, `midweeks`, `blank_gw`, `window`, `clubs`, `gws` only.
- `club_ratings` iterates the club names of every row, later rows included, but only to look up a rating already computed from pre-origin results; a later row's club missing from `names.csv` would stop the run (a failure, never a value).

**1c. Shift probe:** not applicable (no correlation metric on points).

## 2. Clean-checkout suite: PASS

`git archive` copies of `53ba782` and `faf0d73`; `python -m unittest discover -p "test*.py" -s <tree> -t <tree>`; `ODDS_API_KEY` unset; `FPL_HISTORICAL=C:\GIT\FPL\historical` so the three real-file tests run.

| tree | bare | with `FPL_DATA_DIR=C:\GIT\FPL-data` |
|---|---|---|
| `53ba782` | Ran 755, OK (skipped=10), exit 0 | Ran 755, OK (skipped=3), exit 0 |
| `faf0d73` | Ran 811, OK (skipped=10), exit 0 | Ran 811, OK (skipped=3), exit 0 |

+56, the new file's count. No failure, no error.

## 3. Re-run of the pre-registered evaluation: NOT APPLICABLE YET

The backtest has one run, after Boris's rulings on the four questions; no run exists, and I made none.

## 4. Metric, sample, bootstrap, bar as pre-registered: PASS

Constants in the code against the prereg: Brier skill score `1 - BS_model / BS_base` pooled over blank and double of both seasons (`bss`, `report`); targets every `(club, gameweek)` with gameweek after the origin's, to 38 (`simulate`: `gws = [g for g in season.gws if g > origin_gw]`, all 20 clubs; probe: 560/460/360/260/160 targets per kind at GW10/15/20/25/30); origins `(10, 15, 20, 25, 30)`; `N = 20000`, `SEED = 20261021`; base rate per team-gameweek over part 1's seasons before the test season, events above 38 and the 2022/23 void round excluded, zeros counted (`BD.counts`); bootstrap over `(season, target gameweek)` blocks, `B = 10000`, seed 20261021, 90 % interval; 10 reliability bins; `PASS_BSS = 0.10`; Elo K 20, home 60, starts 1500/1400/1300/1200/1100, non-league 1000, placeholder 1250, European elimination 0.5. Nothing has been promoted or re-tuned: no result exists.

## 5. Recording path: PASS

Two copies of the data worktree (`C:\GIT\FPL-data` at `0f0b82d`, the 4 Nov nightly; copied without `.git`), a `sitecustomize` shim first on `PYTHONPATH` pinning `datetime.now()` to 2026-11-05T00:00:00Z (checked), `ODDS_API_KEY`/`GH_TOKEN`/`GITHUB_TOKEN` unset. On one copy the `53ba782` tree, on the other the `faf0d73` tree: `fpl_nightly.py --restore`, then the nightly's `fpl_edge.py --record --source {own,xg,minutes,bottomup,fpl_ep,bottomup_lambda} --status`, `--watch`, `--diff --out`, `--stuck`. Both: `RECORD OK own 305, xg 282, minutes 282, bottomup 282, fpl_ep 670, bottomup_lambda 282 (snapshot odds_2026-11-04T2224Z.json.gz, 282 of 282)`; `projection_log.csv` sha256 `fcae...` on both, 42,712 lines (2,103 appended; the 40,609 original rows unchanged apart from carriage returns); `diff -rq` of the two copies empty. The real worktree's log is untouched (sha256 `7451...` before and after, `git status` clean). The runner path is untouched by the diff: it adds `tools/cup_mc.py`, `tools/cup_backtest.py`, `tools/cups/names.csv`, `tools/cups/round_dates.csv`, `tests/test_S16_part3.py` and nothing else; `nightly.yml`, `fpl_nightly.py`, `fpl_edge.py` unchanged; the no-import tests (`tests/test_S3.py`, `tests/test_S4.py`, `test_fpl.py` line 5241, `tests/test_W2.py`) passed in every suite run above.

## 6. Mutations: PASS, with test gaps listed

**The implementer's 54** (`mut_s16.py`, each a byte-exact single replacement in a fresh copy, `tests.test_S16_part3` run): reproduced, **54 red, 0 green**.

**The dropped mutation** (`m[0] > origin` -> `>=`): the claim "equivalent" holds for the output. If the fallback Tuesday equals the origin date, the origin gameweek's deadline is on that Tuesday, so `window(Wednesday 12:00)` is the origin gameweek itself, and a replay placed there lands in `(club, origin_gw)`, which is never a target (`g > origin_gw`); the only side effect, `placed`, affects other replays into that same midweek, which land there too. Confirmed on the real data: forecasts identical on all ten origins (n = 400); no origin date is a candidate Tuesday (the one Tuesday origin, GW30 2024/25 on 1 Apr 2025, follows the international break and is not a candidate).

**My own 28** (`mut_verifier.py`, places the list skips): **14 red, 14 green**. The reds: replay order by fixture id (V08), `window` taking the earliest deadline (V13), Elo scale 300 (V14), home/away swapped in `load_fixtures` (V15, caught by the E0 score-for-score test), id block off by one (V16, caught by the real-file test), `simulate` unseeded (V17), a drawn round's clubs = home clubs only (V18), Elo giving the loser the delta (V19), base rate blank from 1 fixture (V20), a round on a non-league day read as the next gameweek (V22), Elo in file order (V24), record kind labels swapped (V25), reliability bins by outcome (V27), European knockout never reached (V28).

The 14 survivors, classified. Equivalent in output (no test can or need catch them): V01 (above); V02 origin as the UTC date, not the UK date (a deadline at 23:00-24:00 UTC in BST does not occur; the ten origin deadlines lie 10:00-18:30 UTC); V04/V05 the after/before weekend check without Monday/Friday (a gameweek with fixtures on a Monday or a Friday only does not occur); V21 the midweek's gameweek from Tuesday noon (a deadline between Tuesday and Wednesday noon means a league midweek, busy for all); V23 the blank round's date from the last leg (blank rounds are single-leg).

**Real gaps: the code is right, no test pins it** (each would pass all 56 tests):
1. **V10, the sample filter.** `g > origin_gw` -> `g >= origin_gw` adds the origin gameweek's 20 clubs as targets and would change the pooled BSS. No test checks the key set of `simulate`'s output. The most important gap, since it is the prereg's sample filter.
2. **V11/V12, a two-legged tie.** `t["dates"][-1] < origin` -> `[0]` in `simulate_cup` and in `cup_state` reads a semi-final's winner after its first leg: a point-in-time leak in principle. No backtest origin falls between the EFL Cup semi-final legs (7/8 Jan - 5/6 Feb 2025 against origins 4 Jan and 14 Feb; 13/14 Jan - 3/4 Feb 2026 against 3 Jan and 6 Feb), so the one run is safe, but the toy test should exist.
3. **V03, Thursday.** `busy` from `range(3)` -> `range(2)` frees a club with a Thursday league fixture. Thursday in-block league fixtures inside candidate midweeks exist (5 Dec 2024, 26 Dec 2024, 1 May 2025; 4 Dec 2025, 1 Jan 2026). Real forecasts are identical at n = 400 (no replay seeks those midweeks), but the rule is live and untested.
4. **V06/V07, the bootstrap.** The 90 % quantiles (`0.05`/`0.95` -> `0.025`/`0.975`) and the resample size (`k=len(values)` -> half) are untested; the test checks only reproducibility and low < high.
5. **V09, `forecast`'s season start.** `date(year, 7, 1)` -> `(year, 1, 1)` would count last season's second half: at GW10 the FA field would be 53 exempt clubs + 11 placeholders instead of 44 + 20, silently. The real-file test calls `clubs_by_tier` with its own dates and never reaches `forecast`'s.
6. **V26, `clubs_by_tier`'s upper bound** (`d < before` dropped): a point-in-time read in principle; equivalent on the real data (tiers do not change within a season).

Recommendation: add one toy test each for items 1-5 before `--run-once` (none needs the backtest; none touches a model definition).

## 7. Secrets: PASS

`git diff 53ba782 faf0d73` searched case-insensitively for `apiKey=`, `api_key`, `Authorization`, `Bearer`, `sk-`, 32-hex strings: nothing. The only URLs are Wikipedia permanent-revision links and the CSVs' own paths.

## The caller's items

### 1. Code against the prereg and the amendment, line by line

Every rule located; where the code decides something the text leaves open, it is listed.

| rule (prereg / amendment) | code | finding |
|---|---|---|
| Elo K 20, H 60, tier starts, non-league 1000, carry over seasons | `K`, `HOME`, `TIER_START`, `NON_LEAGUE`; `elo` with `setdefault(TIER_START[tier])` at first appearance, one dict across seasons | as pinned |
| "league results with a date before the origin" | `elo`: `if d >= before: continue`; `read_results` over 2023/24-2025/26 then filtered per origin | as pinned |
| Elo order within a date | `read_results` sorts by (date, tier, file row): E0 first, then the file's order | **silent choice**, deterministic; the text does not pin an order |
| tie: P(home) with H 60, 0 at neutral venues and in the two-legged EFL SF | drawn unplayed tie: `ht = 0 if neutral or legs == 2 else HOME`; undrawn round: `h = 0 if (comp, rnd) in NEUTRAL else HOME`, `NEUTRAL` = FA SF, FA F, EFL SF, EFL F | as pinned |
| undrawn round: uniform random pairing, first drawn at home | `rng.shuffle`, `zip(clubs[0::2], clubs[1::2])`, `a` at home | as pinned |
| a round counts as drawn only if `draw_date` before the origin and every tie of the round before has been played before the origin; else random among the clubs left | `cup_state`: `drawn = bool(here) and all(draw < origin) and prev_played`; `prev_played = drawn and all(dates[-1] < origin)` | as pinned; a round whose predecessor is unfinished is wholly random (the real data has such windows: EFL R4 drawn 2024-09-25 before the last R3 tie 2024-10-01; FA R4/R5/QF 2024/25; EFL SF, FA R4/R5 2025/26; none of the ten origins falls in one) |
| a tie is played when its last `tie_date` is before the origin; same-day not known | `simulate_cup`: `t["dates"][-1] < origin` reads the winner, else Elo | as pinned |
| FA Cup R3 before its draw: 44 exempt (tiers 1-2 from the league files) + 20 placeholders at 1250, never a PL club | `forecast`: field when R3's draw is not before the origin; `clubs_by_tier(results, 1 Jul, origin)`; `fa_field` reverse-maps football-data names to cup names, pads to 64 with `qualifier NN`; placeholders rated 1250 and absent from `season.clubs` | as pinned; reverse map safe (87 unique football-data names) |
| round dates: `round_dates.csv`, one row per leg | `read_round_dates` sorted by leg; blank rounds use leg 1; midweek rounds use every leg | as pinned |
| blank rounds: FA QF, FA SF, EFL F; count only on a UK day of gameweek k's in-block fixtures; k after the origin | `BLANK_ROUNDS`; `blank_gw(day)` = the gameweek with an in-block fixture on that UK day; `k > origin_gw` | as pinned. Real data: FA QF 29 Mar 2025 and 4 Apr 2026 fall on no league day -> no blank; FA SF -> GW34 both seasons; EFL F -> GW29 and GW31 |
| a day holding a deadline belongs to that deadline's gameweek | `blank_gw` returns `hit[0]` | **nit**: if a UK day held in-block fixtures of two gameweeks, the code would take the earlier, the text the later; cannot happen with in-block fixtures |
| every PL fixture of k involving a club in the round is postponed; both clubs blank | `postponed` over `season.original[k]` when `home in clubs or away in clubs`; `delta -1` for both | as pinned (inclusion-exclusion falls out of the joint simulation, as the text says) |
| midweek = Tue-Thu; gameweek = window of Wednesday 12:00 UTC; busy by an in-block league fixture Tue-Thu, a cup round dated that midweek while in it, a European match that midweek | `Season.midweeks`, `window(wed noon)`, `busy` over `tue+0..2` from `league_day` (in-block only); `midweek_rounds` keyed by Tuesday, membership via `sim[c][r]`; `euro[tue]` | as pinned |
| candidate midweek only with an in-block league fixture on Fri-Mon before and Fri-Mon after; season's midweeks from the week of the first to the week of the last in-block kickoff | `before = tue-1..4`, `after = tue+3..6`; loop from the Tuesday of the first league day's week to the last league day | as pinned; 25 candidate midweeks per season. A Monday first kickoff starts the loop one week early (harmless: no league before it) |
| "after its gameweek" = a midweek whose window is a later gameweek than k; "before it" = window earlier than k with its Tuesday after the origin's date; first free after, else last free before | `later[k]` (`m[1] > k`, in order), `earlier[k]` (`reversed`, `m[1] < k and m[0] > origin`); `next(... later) or next(... earlier)` | as pinned |
| replays placed by gameweek, then fixture id; a placed replay makes both clubs busy | `sorted(postponed.items())` on `(k, fid)`; `placed[tue]` | as pinned |
| count: original fixtures of k less postponed plus replays placed in k; 0 blank, >= 2 double; no free midweek -> no double, counted | `base`, `delta`; `blank += (b+d==0)-(b==0)`, `double += (b+d>=2)-(b>=2)`; `slot is None` leaves the blank and adds nothing | as pinned. **Latent**: a club with no fixture in a block would get P(blank) = 0 (the `b == 0` branch is dead: `base` holds only keys with >= 1 fixture; the output's defaultdict yields 0). Unreachable for 2024/25 and 2025/26 (10 fixtures per block, each club once; the real-file test asserts 10 per block). One line to fix before forward use; it cannot touch the backtest |
| European: league phase as scheduled; eliminated at each knockout stage with 0.5; dates from the European CSV | `european_busy`: stage 0 certain, stage s with 0.5^s; backtest passes `europe=()` | as pinned for the backtest (question 1's default: no European matches). **No reader for `europe_2026-27.csv` exists yet**; `simulate` expects `[{"date", "clubs", "knockout", "competition"}]`. Outstanding for forward use, outside this pass |
| 20,000 simulations per origin, seed 20261021 | `N`, `SEED`; `random.Random(seed)` per `simulate` call | as pinned |
| base rate: part 1 seasons before the test season, void round and events above 38 excluded; 2025/26 includes 2024/25 | `base_rates`: `BD.SEASONS` up to `< test_season`, `LAST_REGULAR_EVENT`, `VOID_ROUNDS`, zeros from `BD.counts` | as pinned |
| BSS pooled; per kind and per season; reliability 10 bins; bootstrap 90 % over (season, target gw) blocks, B 10,000, seed | `bss`, `report`, `reliability` (equal-width bins, 1.0 in the last), `bootstrap` (blocks `(r[0], r[2])`, quantiles at `int(0.05 B)` and `int(0.95 B)`) | as pinned; **silent choices**: equal-width bins; floor-index quantiles |
| records scored by the gameweek's `event` count | `records`: `actual == 0`, `actual >= 2` | as pinned (part 1's definition) |
| the one run refuses without its flag | `main`: `REFUSED ...`, return 2 before anything is created | as pinned |

Design note, pinned and not a code matter, stated without any outcome consulted: the rule gives P(blank) = 1 to every club of a known blank-round tie and to its league opponent; the model has no "kept in k by a within-week move" option, which the amendment's stated limit acknowledges exists. Boris may want this in mind when reading the result; it must not be changed after it.

### 2. Point-in-time

Covered in check 1. No path lets a row, result or fixture dated on or after an origin reach that origin's forecast except the final-schedule fields of `fixtures.csv` (`kickoff_time` and `event`), whose use is the pinned stated limit; the text should name `event` too (above). The truncation test is bit-exact at all ten origins.

### 3. The tables

`names.csv`: 89 rows; 87 football-data names, all present in the 2023/24-2025/26 league files and unique; 2 empty (Macclesfield, Weston-super-Mare: tier 6 in every cup row, and in neither season's `EC.csv`); 23 FPL names = the 17 clubs of both seasons + Ipswich, Leicester, Southampton + Burnley, Leeds, Sunderland, unique. Every row eyeballed: each maps to the same club (the abbreviations are football-data's: Man City, Man United, QPR, Dag and Red, Nott'm Forest, Sheffield Weds, Bristol Rvs, Peterboro; FPL's Spurs, Man Utd). Football-data's names are continuous across the three seasons: the only clubs that join or leave are the four National League promotions and relegations each year, so no Elo is silently reset by a rename. What the tests establish: the tier test pins each cup club's football-data name to a club of the stated tier in that season (it would catch a wrong club across tiers, not a swap within a tier; my eyeball covers that); the E0 test pins the 23 PL mappings exactly (380 fixtures per season, score for score); `fa_field` on the real files pins the 44 exempt mappings in both seasons.

`round_dates.csv`: 26 rows, 13 per season (EFL R2, R3, R4, QF, SF leg 1, SF leg 2, F; FA R3, R4, R5, QF, SF, F), each with a source. `test_the_round_dates_are_the_cup_csvs_earliest_tie_dates` establishes exactly the amendment's rule for every round present in the cup CSVs (per leg), and `test_every_blank_round_has_a_date` that the three blank rounds have one; neither would notice an extra row (harmless) nor checks the `source` text (hand-typed, by ruling the final verifier's row check).

### 4. Tests

Strong where they look (the 54 are all red; my 14 reds include the real-file E0 and block tests catching swaps the toys cannot); gaps as in check 6, the sample filter first.

### 5. Hermetic

`tests.test_S16_part3` in a fresh copy with `HOME` an empty folder, `GIT_CONFIG_GLOBAL=/dev/null`, `LC_ALL=C`, `ODDS_API_KEY`/`FPL_DATA_DIR` unset: with `FPL_HISTORICAL` under `TZ=Asia/Tokyo`, `Pacific/Kiritimati`, `America/Anchorage`, `Europe/London`: Ran 56, OK; without it under `Asia/Tokyo` and `America/Los_Angeles`: Ran 56, OK (skipped=3, "no local historical files"). After the runs the tree held nothing new but `__pycache__`; the refusal test's `--out` is in the temporary folder and is proven not created.

### 6. The runner

The diff touches no runner file (five paths, all under `tools/` and `tests/`). The nightly's discovery would collect `tests/test_S16_part3.py`; it imports `tools/cup_backtest`, `cup_mc`, `blank_double`, `calendar_2627` (standard library only, no network, nothing written), and the three real-file tests skip on the runner (`historical/` is gitignored). `tests/test_S3.py::test_the_nightly_imports_nothing_under_tools_or_analysis` and its siblings build the forbidden set from `tools/*.py` at run time, so the two new modules are covered; they passed in all four suite runs.

### 7. Standard library, the refusal, secrets

Imports: `csv, io, os, random, sys, collections, datetime, argparse` and the local `calendar_2627`, `blank_double`, `provenance`. `python -I tools/cup_backtest.py` in a fresh copy: prints `REFUSED: the real backtest gets one run (prereg/S16.md). Pass --run-once after Boris's rulings on the four questions.`, exit 2; the only new files are `tools/__pycache__/*.pyc`; no `tools/out`. `provenance.Run(tool, out_dir, argv=None)` accepts the `argv=None` the CLI passes. Secrets: check 7.

### 8. Suite counts

Check 2: 755 -> 811 bare and with the data, exit 0 each.

## Findings, most serious first

1. **Test gap, the sample filter** (V10): `g > origin_gw` -> `>=` survives all 56 tests and would change the pooled BSS. Failing case: `simulate(toy, ..., origin_gw=3)` returns keys with `gw == 3`. Add a test on the key set before the run.
2. **Test gap, two-legged ties** (V11/V12): `dates[-1]` -> `dates[0]` reads a semi-final winner after leg 1. Failing case: an EFL SF with legs on `SAT+2` and `SAT+9`, origin `SAT+5`, winner "B" with ratings favouring "A": the mutant takes "B". Not reachable at the ten origins; add the toy.
3. **Prereg text incomplete**: `event` is read as well as `kickoff_time`; GW15 2024/25's deadline is 13:30 UTC in the code against FPL's 11:00; no forecast effect in these seasons. One amendment line.
4. **Test gaps** V03 (Thursday busy; live in the data, no forecast effect at n = 400), V06/V07 (bootstrap quantiles and resample size), V09 (`forecast`'s 1 Jul season start: 53 + 11 instead of 44 + 20 under the mutant), V26 (`clubs_by_tier`'s origin bound).
5. **Latent**: a club absent from a block gets P(blank) = 0 (dead `b == 0` branch). Unreachable here; fix before forward use.
6. **Silent choices**, informational: Elo order within a date (tier, then file row); equal-width reliability bins; floor-index bootstrap quantiles; `blank_gw` takes the earlier gameweek of a shared day (unreachable).
7. **Outstanding for 2026/27**, outside this pass: no reader for `europe_2026-27.csv`.

No defect in the code against the prereg and its amendment was found.

## VERDICT: PASS

The prereg's design and both amendments were committed before the single code commit; the code implements every pinned constant and rule (Elo, the tie and draw rules, when a draw and a tie count as known, the FA Cup field, the blank rounds and their gameweeks, the candidate midweeks, replay placement and the counts, the base rate, the Brier skill score, the bootstrap blocks and the bar) as the text states, with the few open details decided deterministically and listed above; the point-in-time rule holds bit-exactly under truncation at all ten origins and the only later information read is the fixture list's final schedule, which the prereg declares (the declaration should also name `event`); the suite goes 755 -> 811 green bare and with the data, hermetically under five time zones with no global git config and `LC_ALL=C`, skipping cleanly without the historical files; the recording path is byte-identical before and after under a frozen clock and the runner imports nothing new; the real run refuses without its flag and writes nothing; the files hold no secret; the implementer's 54 mutations are all red and the dropped one is output-equivalent as claimed. The 14 of my 28 mutations that survive are either output-equivalent or correct lines without a test; the sample filter, the two-legged tie rule and the bootstrap interval should get their toy tests, and the stated limit its extra line, before `--run-once`. None of that changes a model definition, and the backtest has not been run.

---

# Follow-up: the delta `cbde15d..7d600de` (the verifier's gaps closed; still before the one real run)

- Verifier: `backtest-verifier`, model Fable 5.1 (`claude-fable-5-1`), `.claude/agents/backtest-verifier.md` re-read from disk first. Thu 5 Nov 2026, after the pushed `s16b-wip` head `7d600de`. The first verdict above stands as written.
- The hard limit was kept again: no `--run-once`, no score, nothing compared with an outcome. On real inputs I called only `cup_backtest.forecast` at n = 400 and compared forecasts with forecasts.

## Order of commits: PASS

`cbde15d` (03:58:15 +0100) adds the prereg section "After the verifier's pass on the code, before the follow-up" and the first report; the code commit `810aae7` is 03:58:32 +0100 and `7d600de` (one more test) 04:02:29 +0100. The note precedes the code.

## 1. The code change, and the forecasts: PASS

`git diff cbde15d 7d600de` touches `tools/cup_mc.py` (+2/-1) and `tests/test_S16_part3.py` (+68) only. The one code change is the note's: `simulate` now initialises the blank and double counters over every `(club, gameweek)` (`for key in ((c, g) for c in season.clubs for g in season.gws)`, `b = season.base[key]`) instead of over `season.base.items()`, so a club with no fixture in a block starts with P(blank) = 1. Nothing else in the module moved.

Forecasts: `verify_pit.py` with `faf0d73`'s `cup_mc` as the reference and `7d600de`'s as the candidate, the ten origins (GW10/15/20/25/30 of 2024/25 and 2025/26), n = 400, seed 20261021: all ten pairs identical as dicts of floats (exact equality). Expected, since every club has one fixture in every block of both seasons. The truncation test of the first pass also re-ran identical on all ten origins.

## 2. My earlier findings under my own mutations: PASS

`mut_verifier.py` (the same 28 single-line replacements) on a fresh `git archive` of `7d600de`: **22 red, 6 green** (14 red, 14 green on `faf0d73`).

| finding | mutation | on `faf0d73` | on `7d600de` | killed by |
|---|---|---|---|---|
| 1 sample filter | V10 `g > origin_gw` -> `>=` | green | **red** | `test_the_targets_are_every_club_and_only_gameweeks_after_the_origin` |
| 2 two-legged ties | V11 `dates[-1]` -> `[0]` in `simulate_cup` | green | **red** | `test_a_two_legged_tie_is_played_only_after_its_second_leg` |
| 2 two-legged ties | V12 the same in `cup_state` | green | **red** | the same test (added in `7d600de`) |
| 4 Thursday busy | V03 `range(3)` -> `range(2)` | green | **red** | `test_a_thursday_league_fixture_is_busy_too` |
| 4 bootstrap | V06 quantiles 0.025/0.975 | green | **red** | `test_the_interval_is_the_sorted_draws_at_the_two_floors` |
| 4 bootstrap | V07 resample half the blocks | green | **red** | the same |
| 4 season start | V09 `forecast` start 1 Jan | green | **red** | `test_a_club_from_last_season_is_not_in_the_field` |
| 4 origin bound | V26 `clubs_by_tier` without `d < before` | green | **red** | `test_the_field_reads_only_this_seasons_results_before_the_origin` |
| 5 published blank | the one code change reverted to `season.base.items()` in a fresh copy | (was the code) | **red** | `test_a_club_with_no_fixture_in_a_block_blanks` |

All eight "correct lines with no test" now go red, and the code change has a test that fails on the old loop. The six that remain green are exactly the ones I classified as output-equivalent: V01 (fallback Tuesday on the origin's date; any extra placement lands in the origin gameweek's own window, never a target; identical on the real data), V02 (origin as the UTC date; no deadline at 23:00-24:00 UTC in BST), V04/V05 (a gameweek with fixtures on a Monday only or a Friday only does not occur), V21 (Tuesday noon for the midweek's gameweek; a deadline between Tuesday and Wednesday noon means a league midweek, busy for all), V23 (the blank round's date from the last leg; blank rounds are single-leg). None is a line a toy can distinguish without inventing a calendar no season has; none needs a test.

## 3. The note's account of the `event` limit: ACCURATE

The note says the calendar also reads `event` to keep the fixtures left in their id block, that this encodes which fixtures later left it, that a later postponement therefore drops a fixture from its gameweek's days, its deadline and that midweek's busy clubs, and quotes my measurement (GW15 2024/25: Sat 7 Dec 13:30 UTC against FPL's 11:00; the same UK date; no forecast effect in these seasons). That matches the code: `Season.__init__` feeds `kick` (the deadline), `days` (`blank_gw`) and `league_day` (the midweek busy sets) only from fixtures with `event == block`. The one thing the sentence does not spell out is that `league_day` also decides which midweeks are candidates (the Friday-to-Monday check); a postponement could only matter there if a weekend lost every fixture, which is the void-round case and not in these seasons. The four pinned choices (Elo within a date by tier then row order; equal-width bins; floor-index quantiles; the earlier gameweek of a shared day) are what the code does. The claim "this cannot happen in 2024/25 or 2025/26" for the published blank holds: the real-file test asserts 10 fixtures in every block, and each club appears once in each.

## 4. The implementer's mutations: PASS

`mut_s16.py` now lists 66; on a fresh `git archive` of `7d600de`: **66 red, 0 green**.

## 5. Suite at `7d600de`: PASS

Clean `git archive` copy, discovery (`test_fpl.py` plus `tests/`), `ODDS_API_KEY` unset, `FPL_HISTORICAL` set: bare **Ran 819, OK (skipped=10)**; with `FPL_DATA_DIR=C:\GIT\FPL-data` **Ran 819, OK (skipped=3)**; exit 0 both. 811 -> 819: the eight new tests (`tests.test_S16_part3` alone: 56 -> 64). Hermetic: `tests.test_S16_part3` with `HOME` an empty folder, `GIT_CONFIG_GLOBAL=/dev/null`, `LC_ALL=C`: 64 OK under `TZ=America/Anchorage` and `Pacific/Kiritimati` with the historical files, 64 OK (skipped=3) under `Asia/Tokyo` without them; a before/after file listing shows nothing written outside `__pycache__`. Secrets: the delta holds none (the same search as check 7). The delta touches no runner file.

## 6. In the way of the one real run

Nothing in the code or its tables, as far as this pass can see, given the defaults the prereg states. What remains is Boris's four rulings, with one dependency to name: if the ruling on question 1 is to add the 2024/25 and 2025/26 European calendars (rather than the default of no European matches), the backtest needs CSVs that do not exist, a reader that does not exist (`simulate` takes `europe` as a list of dicts; no file reader is written), and a prereg amendment pinning both, before the run; likewise a non-default ruling on question 2 (Dixon-Coles instead of Elo) or 3 (another elimination rule) is new code and a new amendment first. Under the defaults, `python -I tools/cup_backtest.py --run-once` is ready: it reads only the committed tables and the local `historical/` files, writes `tools/out/s16_backtest/backtest.txt` and `run.txt` through `provenance.Run`, and refuses without the flag.

## VERDICT (follow-up): PASS

The prereg note was committed before the follow-up code; the only code change is the one it describes (a published blank now has P(blank) = 1), it leaves every real-input forecast bit-identical to `faf0d73` at all ten origins, and its own test fails on the old loop; the eight tests added close every gap I listed (all eight of my surviving "correct line, no test" mutations now go red, and the six that stay green are the output-equivalent ones); the note's account of the `event` limit and the pinned choices is accurate; the implementer's 66 mutations are all red; the suite is 819 green bare and with the data, hermetically, with no secret and no runner file touched. Given the prereg's defaults, only Boris's rulings on the four questions stand between this code and its one run; a non-default ruling on question 1, 2 or 3 would need code and an amendment first.
