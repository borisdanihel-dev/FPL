# verify_FM — status gate v2 (`xp_v2_g2`): the code and its retrospective check, `origin/fm-wip` `f6d1c34`

**VERDICT: WARN.** Every number in the launch reproduces exactly, the rule equals the pin
row by row, the check is point-in-time clean, and nothing was tuned. The result stands:
the bar is **not passed** (mean e -0.158, 90% [-0.310, -0.016]). Four things need Boris:
(1) the check scored six origins, not the seven answer 7 asked for (GW4 cannot be built
from its export); (2) two information prints the pin lists are missing from the tool;
(3) the check's own function has no test, so 14 of my 17 mutants of it stay green,
including a reversed e; (4) the test file holds 22 tests, not 23. None of these can turn
the result into a pass (see "GW4 cannot change the outcome").

Verifier: Claude Code, model Fable 5.2 (`claude-fable-5-2`); Fable was available, no
fallback. Effort: launched at high, not confirmable. Run: Thu 19 Nov 2026, about 21:18 to
21:50 UTC. `.claude/agents/backtest-verifier.md` was read from disk first; it matches my
loaded instructions. Its verdict line allows PASS or FAIL; the launch asked for PASS, WARN
or FAIL, and I use WARN as the launch and `verify_W3fix.md` do: no deciding check fails,
but decisions are open. No session transcript or chat log was read. I read the
implementer's scratch outputs (`fm_check1.log` to `fm_check3.log`, the two `run.txt`
files, `gate_v2_rows.csv`, `fm_smoke.py`, `fm_probe.py`, `fm_probe2.py`); these are tool
outputs and scripts.

State checked: `C:\GIT\FPL` master `101a485`; the untracked folder `worklog/gw_pass/gw11/`
was there before I started and I did not touch it; this file is my only change.
`C:\GIT\FPL-data` at `029bcfd`, `pull --ff-only` said "Already up to date"; nothing else
was run there. All work was done in
`C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vfy_fm`
(git-archive copies of `f6d1c34`, `30b6067` and the branch base `2af773c`; a git-archive
copy of data `029bcfd`; a scratch clone at `f6d1c34` for the provenance run). Nothing was
pushed, merged or deleted.

## Summary table

| Check | Result | Evidence in one line |
|---|---|---|
| 0 prereg before code | PASS | the pin `4274955` is an ancestor of all four code commits and 23 min 53 s earlier than the first; answers 6-7 (`448e652`) were committed 9 min 55 s before the first run on the data |
| 1a truncation | PASS | six origins rebuilt from folders holding only what existed before each deadline: v1 and v2 equal the item's for every player and week, max difference 0 |
| 1b timestamps | PASS | every export, odds snapshot, result and export row used for origin g is before g's deadline (table below) |
| 1c shift probe | not applicable | the metric is a paired absolute-error difference, not a correlation |
| 2 suites | PASS | base `2af773c` 855 OK (11 skipped); `f6d1c34` 877 OK bare (11 skipped) and 877 OK with the data copy (4 skipped) |
| 3 re-run | PASS | my run of the harness on a clone at `f6d1c34` gives both output files byte-identical to the implementer's |
| 4 metric, filter, bootstrap, bar | PASS, with notes 1 to 5 | all as pinned on the six origins scored; no metric promoted; the 16 Nov draft code gives the same 830 rows |
| 5 recording path | PASS | 2,340 GW11 rows re-recorded with the base code and the item's: identical to each other and to the data's in every column but `made_at`; no `xp_v2_g2` row |
| 6 mutation | PASS for the rule, gap for the check | 24 of my 42 mutants red: 21 of 25 on the rule, 3 of 17 on the check |
| 7 secrets | PASS | no `apiKey=`, Authorization value, URL or key pattern in the three new files |

## Claim 1 — the pin predates the code, and the code implements it. Confirmed.

| Commit | Time (UTC) | What |
|---|---|---|
| `4274955` | Mon 16 Nov 17:44:51 | the design pinned in `prereg/FM.md` |
| `b04c3f8` | Mon 16 Nov 18:08:44 | `tools/gate_v2.py`, 12 tests |
| `30b6067` | Mon 16 Nov 18:11:49 | `tools/gate_v2_check.py` drafted, 15 tests |
| `85f3a69` | Mon 16 Nov 19:16:10 | the two parked questions on file |
| `448e652` | Thu 19 Nov 20:53:32 | answers 6 and 7 on file |
| (first run, `fm_check1.log`) | Thu 19 Nov 21:03:27 | a traceback at GW4, no number printed |
| `2efefd2` | Thu 19 Nov 21:04:30 | the missing-input handling |
| (second run, `fm_check2`) | Thu 19 Nov 21:04:31 to 21:04:43 | the first numbers, on `2efefd2`, 0 modified files |
| `f6d1c34` | Thu 19 Nov 21:20:14 | matrix tests, the count print |

`4274955` is an ancestor of `b04c3f8`. The item adds three files and changes no other
(`diff -rq` of the two archives: `tools/gate_v2.py`, `tools/gate_v2_check.py`,
`tests/test_FM.py`). `tools/xp_v2_live.py`, `fpl_xpv2.py` and the runner are untouched.

The rule against the pin. I wrote the rule again from `prereg/FM.md` alone (my own date
parser, my own suspension reader on the raw exports, my own window, then the frozen
`xp_v2_live.core`) and compared it with `gate_v2.matrix` for every player and all six
weeks at each origin, and at tonight's live origin:

| Origin | Player-weeks compared | Max difference | Modes, item = mine |
|---|---|---|---|
| GW5 | 1,836 | 0 | v1 2,766, out 760, normal 226, lifted 22, half 180 |
| GW6 | 1,795 | 0 | v1 2,730, out 762, normal 283, lifted 31, half 196 |
| GW7 | 1,879 | 0 | v1 2,808, out 746, normal 244, lifted 28, half 176 |
| GW8 | 1,895 | 0 | v1 2,790, out 766, normal 240, lifted 28, half 184 |
| GW9 | 1,975 | 0 | v1 2,826, out 764, normal 203, lifted 25, half 196 |
| GW10 | 1,975 | 0 | v1 2,844, out 774, normal 186, lifted 20, half 196 |
| GW11 (live) | 1,955 | 0 | |

A second route that does not use my window code: I edited a copy of each export (every
flagged player set to status `a` with no chance for "as normal"; status `a` with chance 50
for the fixed 50%; `xp_v2_live.forecast(lift=...)` for the lifted week) and read the
values off v1 and the frozen forecast. Over 3,372 flagged player-weeks at the six origins
the difference from the item's v2 is 0 (11 flagged players skipped: a suspended gameweek
in the window, which only the first route covers).

Row by row:

- `d`: lifted in week t (P(start) x c and P(sub) x c, equal to the S8c lift), then normal. Confirmed.
- `s` with "Suspended until <date>": 0 before the date, normal from the first fixture on or after it. Confirmed (Thiago tonight: 0, 0, 0, 4.71, 4.26, 5.26).
- `s` with no date: 0 in t, then normal. Confirmed by the unit test and my mutant R3; no such player is in the scored population (all 24 `s` rows there carry a date).
- `i` with "Expected back <date>": like `s`. Confirmed.
- `i` unknown: 0 in t and t+1, then P(start) x 0.5 and P(sub) x 0.5. Confirmed.
- `u`, `n`: 0. `a`: as v1. Confirmed.
- The date rule: the first year that puts the date on or after the export's generated date. Confirmed. One consequence, as pinned: a stale date reads as next year. Bergvall, "Expected back 31 Oct" in the 6 Nov export, is taken as 31 Oct 2027 and is 0 in all six weeks (one scored player-week, e = 0).
- The split double gameweek: covered by the toy test only (my mutant R18 goes red). The data has no double in GW5-10, so it is never exercised by the check.
- Point 5 as answer 6 reads it: the window is the last four gameweeks without a suspension, for starts and for the 45-minute gate. Suspended in e = status `s` in the newest export generated before e's deadline; my reader gives the same player-gameweeks at every origin (1, 5, 9, 12, 17, 21). GW1-3 have no export before their deadlines and are taken as unsuspended; the tool prints the count (34 of 34, 43 of 43, 39 of 39, 1 of 45, 1 of 42, 0 of 36).

Note 4 below covers one wording difference on GW1-3.

## Claim 2 — v1 equals `builder.live_matrix`. Confirmed.

- Tonight's data (`029bcfd`, export `fpl_export_gw10_2026-11-19.json.gz`, snapshot `odds_2026-11-19T0249Z.json.gz`): `gate_v2.matrix(..., "v1")` equals `builder.live_matrix` as a dictionary, 292 players x 6 weeks = 1,752 values. The implementer's 296 was on data `93916ee`; tonight's export has 292.
- At each past origin I ran the real `builder.live_matrix` in the truncated folder with the clock set one minute before the deadline: equal to v1 as a dictionary at all six origins (1,668, 1,578, 1,674, 1,668, 1,758 and 1,800 values). For GW5-7 the export is plain `.json`, which `newest_export` does not read, so I gave it the same bytes gzipped.
- Week t of v1 equals the frozen `xp_v2_live.forecast` at all six origins, max difference 0.
- Status-`a` players under v2: at the six origins 0, 2, 4, 5, 8 and 8 of them differ from v1, and every one has a suspended gameweek in his plain window. Tonight 8 of 474 differ (Disasi, Sessegnon, Martinez, Danso, Janelt, Yarmoliuk, Bentancur, Crooks), all through point 5; 10 have a suspended gameweek in the window.

## Claim 3 — the check implements the pin, and nothing after a deadline is read. Confirmed for the six origins scored.

Timestamp audit (check 1b):

| Origin | Deadline (UTC) | Export, generated | Lead | Odds snapshot | Results in the fallback | Newest row in the export |
|---|---|---|---|---|---|---|
| GW5 | 18 Sep 17:30 | `fpl_export_gw4_2026-09-17.json`, 17 Sep 21:55 | 19.6 h | none (fallback) | 40, newest 14 Sep 19:00 | GW4 |
| GW6 | 10 Oct 10:00 | `fpl_export_gw5_2026-10-09.json`, 9 Oct 21:50 | 12.2 h | none (fallback) | 50, newest 20 Sep 15:30 | GW5 |
| GW7 | 17 Oct 10:00 | `fpl_export_gw6_2026-10-16.json`, 16 Oct 22:02 | 12.0 h | none (fallback) | 60, newest 12 Oct 19:00 | GW6 |
| GW8 | 23 Oct 17:30 | `fpl_export_gw7_2026-10-23.json.gz`, 23 Oct 14:22 | 3.1 h | `odds_2026-10-23T1422Z` | 70, newest 19 Oct 19:00 | GW7 |
| GW9 | 31 Oct 11:00 | `fpl_export_gw8_2026-10-30.json.gz`, 30 Oct 22:13 | 12.8 h | `odds_2026-10-30T2213Z` | 80, newest 25 Oct 16:30 | GW8 |
| GW10 | 6 Nov 18:30 | `fpl_export_gw9_2026-11-06.json.gz`, 6 Nov 01:48 | 16.7 h | `odds_2026-11-06T0148Z` | 90, newest 2 Nov 20:00 | GW9 |

I chose each export and snapshot with my own code; they are the tool's. Lambda sources:
GW5-7 all fallback; GW8 and GW9 week t 10 of 10 from odds, later weeks 11 from odds and 39
fallback; GW10 week t 10 from odds, later weeks 10 and 40.

Truncation (check 1a). For each origin I built a folder with only the exports generated
before the deadline, the snapshots taken before it, and a database copy with every result
from the deadline on removed, `player_gw` rows of gameweek g and later deleted, and the
events from g on unset. Folder sizes: 2, 18, 25, 33, 41, 47 exports; 0, 0, 0, 8, 16, 23
snapshots; 40 to 90 finished fixtures. v1 and v2 rebuilt there equal the full-data values
for every player and week at all six origins (max difference 0; 1,836 to 1,975 values for
v2). The launch asks for three gameweeks; I ran all six.

The rest of the pin:

- Weeks u = g..g+5 with u <= 10, all locked (`data_checked` 1 and 10 of 10 fixtures finished for GW1-10). Confirmed.
- Population: status `d`, `s`, `i` in the origin's export with `mins_last4` >= 45. Confirmed (next section).
- Realised: `player_gw.total_points` summed over the week. Confirmed.
- e = |v1 - r| - |v2 - r|, pooled mean, origins resampled, B 10,000, seed 20261018, 90% percentile interval with `fpl_bt.bootstrap_mean`'s index rule, bar = lower bound above 0. Confirmed by my own bootstrap.

## Claim 4 — the result. Reproduced exactly.

My run: `python -I tools/gate_v2_check.py` on a clone at `f6d1c34` (0 modified files),
data copy of `029bcfd` (its `exports/`, `odds/`, `fpl.sqlite` and `projection_log.csv`
have the same SHA-256 as the implementer's `fm_data`). `gate_v2_check.txt` (sha256
`2a15...`) and `gate_v2_rows.csv` (sha256 `d138...`) are byte-identical to the
implementer's `fm_check3`. My `run.txt`:
`C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vfy_fm\out\check\run.txt`.

Independent count, from the raw exports and the database with none of the item's code:

| Origin | Flagged | Weeks | Player-weeks | Sum e | Mean e |
|---|---|---|---|---|---|
| GW5 | 34 | GW5-10 | 204 | -32.920452 | -0.161375 |
| GW6 | 43 | GW6-10 | 215 | +17.646053 | +0.082075 |
| GW7 | 39 | GW7-10 | 156 | -42.484951 | -0.272339 |
| GW8 | 45 | GW8-10 | 135 | -68.634622 | -0.508405 |
| GW9 | 42 | GW9-10 | 84 | -10.576592 | -0.125912 |
| GW10 | 36 | GW10 | 36 | +5.518086 | +0.153280 |
| all | | | 830 | | -0.158376 |

- The 830 keys (origin, week, player) equal the implementer's set; status equal in all.
- Playing clubs taken from the database's fixtures, not the export: the same 830. The export's fixture list equals the database's in every scored week. No double, no blank.
- The flagged count is the same when minutes are summed from `player_gw` over the last four gameweeks instead of read from `mins_last4` (34, 43, 39, 45, 42, 36). `mins_last4` differs from that sum for 2 players in each of the three September-October exports; none changes the population.
- Realised points: equal to my sum from the database in all 830; total 1,070. No player-week lacks a row; none has two rows. A second source, the newest export's `player_gw_recent`, agrees in all 830 (439 player-weeks have no row there and 0 points in the database).
- Pooled mean -0.158376480. My bootstrap: 90% [-0.310141737, -0.016281611]. The bar is not passed. 3.05% of the resample means are above 0.
- By status: `d` -0.314471 (n 378), `i` -0.092789 (n 370), `s` +0.265237 (n 82). As claimed.
- GW4: `fpl_export_gw3_2026-09-11.json` (generated 11 Sep 21:55, 14.6 h before the GW4 deadline) has 929 rows without `player_id`; `fpl_edge.canonical_from_export` raises. Confirmed.

By status and mode (information):

| Status, mode | n | Mean v2 | Mean realised | Mean e |
|---|---|---|---|---|
| `d`, lifted | 110 | 1.84 | 1.30 | -0.327 |
| `d`, normal | 268 | 2.84 | 1.99 | -0.310 |
| `i`, half | 93 | 1.20 | 1.18 | -0.227 |
| `i`, normal (dated) | 108 | 1.97 | 1.39 | -0.123 |
| `i`, out | 169 | 0 | 0.10 | 0 |
| `s`, normal | 48 | 3.18 | 2.46 | +0.453 |
| `s`, out | 34 | 0 | 0 | 0 |

### GW4 cannot change the outcome

I did not build GW4 by any other route, so that the decision on it is made without its
number. A bound that needs no GW4 number: with seven origins resampled, 34.0% of resamples
hold no GW4 at all ((6/7)^7). Of those, 97.9% have a pooled mean at or below 0 (exact, all
6^7 draws). So at least 33.3% of seven-origin resamples are at or below 0 whatever GW4
holds, and the 5th percentile cannot be above 0. The bar cannot be passed on GW4-10.

With GW4 kept as a seventh, empty unit the interval is [-0.312, -0.015]. Other seeds give
[-0.312, -0.016], [-0.310, -0.016], [-0.308, -0.016].

## Claim 5 — tests and mutants. Partly confirmed.

- `tests/test_FM.py` holds **22** tests, not 23 (12 at `b04c3f8`, 15 at `30b6067`, 22 at `f6d1c34`). All 22 pass. The suite count agrees: 855 + 22 = 877.
- The implementer's 11 mutants are not listed in any file I could find, so "11 of 11" is not confirmed or refuted.
- My mutants, one line each in a scratch copy, `tests/test_FM.py` run each time: **24 of 42 red**.

The rule (`tools/gate_v2.py`): 21 of 25 red. Red: `d` lifted in the wrong weeks; a fixture
on the date still out; `s` without a date out twice; `i` unknown out once, or three times;
today not counting; never the following year; the chance ignored; injured read as
suspended; unknown gameweeks not reported; the plain window; a three-week window; lifted
at 100; a status-`a` chance dropped; the split double on both fixtures; normal weeks at
half; `u`/`n` taken as `a`; an export after the deadline; the fallback on later results; a
suspension read from a later export; lifted P(start) without the chance. Survivors:

1. `matrix()` passes no suspensions to the window. The toy tests call it with `{}`, so point 5 inside the matrix is tested only through `window()`.
2. The 45-minute gate is not read over the point-5 window (`q["mins_last4"] = mins` removed).
3. P(sub) keeps the flag's chance in normal and 50% weeks (`chance_u[pid] = scale` removed). The toy player has P(sub) 0.
4. `origin()` takes an odds snapshot from after the deadline.

All four behaviours are right in the code: my own rule and the edited-export route match
on the real data, and the timestamp audit covers the snapshot.

The check (`tools/gate_v2_check.py`): 3 of 17 red (the bar at >= 0, the bar on the upper
bound, the point estimate as a mean of origin means). `check()`, `locked_weeks()` and
`main()` are never called by a test. Survivors:

1. e reversed. `test_the_sign_of_e` computes `abs(v1 - r) - abs(v2 - r)` inside the test and never calls the module.
2. Injured players left out of the population.
3. The 45-minute filter dropped.
4. Weeks that are not locked down scored.
5. Realised points taken from the following gameweek.
6. The resample statistic changed to a mean of origin means.
7. The seed not fixed (the toy has three origins, so every run gives the same percentiles).
8. A 50% interval.
9. v2 never read.
10. A blank club's week scored.
11. A missing origin kept as an empty unit.
12. Origins GW5-10 only.
13. The horizon through GW11.
14. Point 5's suspensions not passed to v2.

The pin's test list says "the check's metric sign, its bootstrap unit and its bar on toy
numbers ... Each test red on a planted bug". The bar is covered. The sign and the
resample statistic are not. The check's numbers are still right: my independent count
reproduces all of them.

## Claim 6 — the suite. Confirmed.

| Tree | Mode | Result |
|---|---|---|
| `2af773c` (the branch base) | bare | 855 OK, 11 skipped |
| `f6d1c34` | bare | 877 OK, 11 skipped |
| `f6d1c34` | `FPL_DATA_DIR` = my restored copy of `029bcfd` | 877 OK, 4 skipped |

## Claim 7 — no tuning. Confirmed.

- `tools/gate_v2.py` has two commits. `f6d1c34` only moves the window's list into `window_weeks()`.
- `tools/gate_v2_check.py` has three. `2efefd2` adds the try/except, the "NOT SCORED" lines and the filter to scored origins; it was committed one second before the first run that printed numbers started, and that run was on it with 0 modified files. `f6d1c34` changes the last column of the origin table.
- `gate_v2_rows.csv` has the same SHA-256 in `fm_check2` (on `2efefd2`) and `fm_check3` (on `f6d1c34`).
- I ran `check()` from the 16 Nov draft (`30b6067`, written before any number) on origins GW5-10: the same 830 rows to the last digit and the same interval.
- `fm_smoke.py` (16 Nov) compares v1 with the live matrix and prints three players; it reads no realised points. `fm_probe.py` and `fm_probe2.py` (19 Nov) read the toy only.

## Check 5 — recording path. PASS.

On two copies of data `029bcfd`, after `fpl_nightly.py --restore`, I ran `fpl_edge.py
--record` for the seven sources with the base code and with the item's. Each replaced
today's 2,340 GW11 rows (own 292, xg 271, minutes 271, bottomup 271, fpl_ep 672,
bottomup_lambda 271, xp_v2 292). Both logs equal each other and the data's own log in
every column but `made_at`, in order, all 71,936 lines (header included); the other 69,596
lines are byte-identical to the data's. No `xp_v2_g2` row exists. Only `tests/test_FM.py` and the two new tools
mention `gate_v2`.

## Check 7 — secrets. PASS.

The three new files hold no `apiKey=`, no Authorization value, no URL, no 32-character hex
string and no token pattern. The only long strings are four test names.

## Notes

1. **Six origins, not seven.** Answer 7 says "Score all seven origins, GW4-10". The tool reports GW4 as a missing input and scores six; the bootstrap resamples six. The header still reads "GW4-10". In the 11 Sep export every one of the 929 rows matches exactly one player by (web_name, team, position), so GW4 could be built by a lookup, but that is a substitution the frozen reader refuses and no ruling covers. It would add 17 flagged players and 102 player-weeks (GW4-9).
2. **Two pinned prints are missing.** The pin lists, as information, "the players whose v2 differs only through point 5 ... their own n and mean e" and "F-M's record: our flagged players' realised points against v1 and v2, week by week". The tool prints neither. My figures, information only:
   - Point 5 alone: 12 status-`a` players, 76 player-weeks over origins GW6-10, mean v1 1.90, mean v2 3.01, mean realised 2.34, mean e -0.227 (origin-unit 90% [-0.447, -0.047]).
   - Our flagged players: 17 player-weeks (Shaw GW5-10 from the GW5 origin; Branthwaite GW7-10 and GW9-10; Calafiori GW9-10; Thomas GW9-10 and GW10), mean e -0.193. Calafiori scored 6 and 6 against v2 2.73 and 5.01; Thomas 0, 0, 0 against 2.45, 4.46, 1.67; Shaw 2, 3, 0, 0, 0, 0 against 2.13 and then about 2.9 a week.
3. **`check()` is untested** (claim 5). `prereg/FJ.md` took an end-to-end test of `checkpoint.py`'s `main()` for the same gap.
4. **GW1-3 wording.** The pin says that where a gameweek in the window has no archived export "the plain window is used". The code takes GW1-3 as unsuspended but still skips a known suspended gameweek in the same window. Under the other reading (the plain window whenever the window reaches GW1-3) six flagged player-weeks change: mean -0.152, 90% [-0.301, -0.009]. Not passed either way.
5. **The branch's own prereg is behind.** `fm-wip` starts at `2af773c`; its `prereg/FM.md` lacks the parked questions and the Thu 19 Nov answers (42 lines) that master has. It is 5 commits behind master and 4 ahead; it needs a rebase before any merge.
6. **A wide catch.** `check()` catches every `ValueError` in an origin's build and reports it as a missing input. It is printed, never silent, but a bug that raises `ValueError` would read the same way.
7. **Provenance.** The cited run's `run.txt` is in the session scratch folder (`...\scratchpad\fm_check3`), not `tools/out/gate_v2_check/` as the pin names. It is correct (commit `f6d1c34`, 0 modified files, hashes equal to mine), but a scratch folder can be cleared.
8. **What the metric compares, for the GW15 revisit (not a pinned metric, and not a reason to change the verdict).** v1 is 0 in all 830 player-weeks, because the population is the players v1 gates out. So e compares v2 with the constant 0. 462 of the 830 scored 0, so 0 is the median, and absolute error favours the median. Mean realised is 1.29; mean v2 is 1.74, so v2 over-forecasts this group by 0.45. On squared error the same rows favour v2: mean difference +1.93, 90% [+0.75, +3.12]. Changing the metric now would be a promotion after the results were seen; any change belongs in a new prereg tested on gameweeks not yet played.
9. The parked-questions heading says "Mon 16 Nov 19:20 UTC"; its commit `85f3a69` is 19:16:10 UTC.

## Decisions for the chat

1. **GW4.** Answer 7 asked for seven origins; six were scored. Accept the six-origin run as the test's result (the bar cannot be passed with GW4 in, whatever it holds), or rule a way to build GW4 (the name, club and position lookup is unambiguous in that export) and rerun?
2. **The result.** The bar is not passed. By the Mon 16 Nov and Thu 19 Nov rulings `xp_v2_g2` is then not recorded on Mon 23 Nov. Its numbers as information in the GW11 bundle were ruled separately (Thu 12 Nov night, Mon 16 Nov) and are not affected by this verdict. Confirm.
3. **The missing prints and tests.** Before the GW15 re-run, add the two pinned information prints and an end-to-end test of `check()` on a toy that catches a reversed e, a wrong population, an unlocked week, the wrong week's points and a changed resample statistic?
4. **GW1-3 wording.** Keep the code's reading (GW1-3 unsuspended, known suspensions still skipped), or the pin's literal "plain window"? Six player-weeks; the same verdict.
5. **The GW15 revisit.** Keep the absolute-error bar as it is, or pre-register a different test for gameweeks from GW11 on (note 8)? The `d` rows do worst (-0.314); the `s` rows are positive (+0.265, n 82).
6. **The count.** The commit message and the launch say 23 tests; the file holds 22. The report should say 22.
7. **Housekeeping.** Rebase `fm-wip` onto master before any merge, and keep the cited `run.txt` somewhere durable.

VERDICT: WARN. The code implements the pinned rule exactly: my own rewrite of it from the
prereg matches for every player and week at six past origins and tonight's, and v1 equals
`builder.live_matrix` at all seven. The check is point-in-time clean under truncation and
a timestamp audit, was not tuned (the 16 Nov draft gives the same rows), and its result
reproduces byte for byte and by an independent count: 830 flagged player-weeks, mean e
-0.158, 90% [-0.310, -0.016], bar not passed. It is a WARN and not a PASS because the run
covers six of the seven origins answer 7 asked for, two pinned information prints are
absent, the check's own function has no test (14 of 17 mutants of it survive, a reversed e
among them), and the test count is 22, not 23. None of these can make the bar pass, so
under the rulings on file `xp_v2_g2` is not recorded on Mon 23 Nov unless Boris rules
otherwise.
