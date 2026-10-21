# Verifier: S2b (the final re-fetch until data_checked), pre-merge, after the dry run

Written 2026-10-20, about 11:40 UTC, by the backtest-verifier agent. Model:
Fable 5.1 (claude-fable-5-1); effort high, as `.claude/agents/backtest-verifier.md`
says (read from disk first; it matched the loaded instructions). This run
verifies the GitHub dry run and the delta since the code-level PASS
(`worklog/verify_S2b_pre.md`, on `19b303c`); the checks are in their
data-pipeline form (the prereg has no pass/fail metric): 1, 2, 5, 6, 7 plus the
item's acceptance tests; 3 and 4 are n/a where the prereg says n/a, except
check 4's "ruling present verbatim, committed before the code".

Nothing was written to `C:\GIT\FPL`, `C:\GIT\FPL-data`, `C:\GIT\FPL-b` or any
data branch; nothing dispatched; no FPL or Odds API call. The data-dryrun and
data commits were read with `git show` from `C:\GIT\FPL` into the session
scratchpad (`v2/`: the two databases, logs, exports and projection logs; `v2/a00`
and `v2/df8` are `git archive` exports of `a00ccc7` and `df867cb`; `v2/mut/*`
the mutation copies). `C:\GIT\FPL-data` was only read (hashes below).

## What was verified against

- The branch `s2b-wip` in the scratch worktree at `df867cb` (clean at launch);
  master `8d0a50b` = the merge base of `df867cb`. The dry-run commit
  `origin/data-dryrun 4b199eb` ("dry run 2026-10-20 s2b-wip a00ccc7", parent
  `e1154dd` = the 19 Oct 22:05 nightly on `data`). `C:\GIT\FPL-data` at
  `e1154dd`.
- `git diff --stat 8d0a50b df867cb`: `checks.py` (+56/-), `fpl_sync.py`
  (+77/-), `test_fpl.py` (19 lines), `tests/test_S2b.py` (+376, new),
  `tests/test_S3.py` (3 lines), `worklog/cc_2026-10-19_S2b.md`,
  `worklog/verify_S2b_pre.md`. The same seven files for `a00ccc7` against its
  master parent `a3d63b0`. No other runner file, no workflow file.

## Prereg and commit order: PASS

`prereg/S2b.md` was committed in `f612a2c` (2026-10-19 01:10:03 +02:00), an
ancestor of the one code commit `19b303c` (01:38:16 +02:00). Since then the
file only gained lines (`0674e0f` the morning ruling, `fc56fd5` the afternoon
ruling; `git diff f612a2c 8d0a50b -- prereg/S2b.md` removes 0 lines). The
S2b ruling (points 1-4, "RULING S2b ... END RULING") is in the file verbatim,
with the six acceptance tests, the morning ruling (point 5: "S2b decisions
1-3 accepted; check 22 is the guard on point 1") and the afternoon ruling
(point 5: the dry run moved to Tuesday after 00:00 UTC; the dry run ran
10:56-10:59 UTC on 20 Oct).

## S2b's code unchanged since 19b303c / 316652a: PASS

- `git diff ab047c3 316652a` and `git diff 8d0a50b df867cb`, each restricted
  to `checks.py fpl_sync.py test_fpl.py tests/test_S3.py`: 280 lines each; the
  added and removed lines (headers stripped) are identical (`diff` empty).
- `git diff 316652a df867cb -- tests/test_S2b.py`: empty.
- `git diff a00ccc7 df867cb` on `fpl_sync.py checks.py test_fpl.py tests/test_S2b.py
  tests/test_S3.py fpl_nightly.py fpl_edge.py .github`: empty. The dry run at
  `a00ccc7` therefore ran exactly the S2b code that `df867cb` carries.
- The landing (`a3d63b0` -> `8d0a50b`): `BUILD_PLAN.md`, `CHANGELOG.md`,
  `CLAUDE.md`, `tests/test_S11..S14.py`, `tests/test_S6b..S6d.py`,
  `tests/test_S8.py`, `tests/test_bundle.py`, `tests/test_provenance.py`,
  `tests/test_S5.py` (11 lines), `tests/test_S9.py` (2 lines), and files under
  `tools/`, `analysis/`, `prereg/`, `worklog/`. `git diff --name-only a3d63b0
  8d0a50b` on `fpl_sync.py checks.py fpl_nightly.py fpl_edge.py fpl_gate.py
  fpl_publish.py fpl_prepush.py fpl_xpv2.py fpl_odds.py .github/
  requirements*.txt`: nothing. The landing touches no runner file; its
  interaction with S2b is tested by the `df867cb` suite runs below (green,
  708 of 708, bare and with the real data).

## The dry run against the prereg and the report: PASS

Read from `origin/data-dryrun 4b199eb` (`reports/status_dryrun.txt`,
`logs/run_2026-10-20.log`, `fpl.sqlite`, `fpl.sql`, `projection_log.csv`,
`exports/fpl_export_gw7_2026-10-20.json.gz`) against `e1154dd`'s.

**Calls (acceptance test 3, ruling point 1).** The run log's `SYNC STATS`
lists 73 calls, all HTTP 200: `bootstrap-static/`, `fixtures/`,
`event/1/live/` .. `event/7/live/` (7), `leagues-classic/455565/standings/`,
and for each of the 7 entries `history/`, `transfers/` and
`event/1/picks/` .. `event/7/picks/` (7 x 9 = 63). The 19 Oct 22:05 nightly's
`SYNC STATS` lists 25 (one live, one picks per entry: GW7 only). Extra:
6 live + 42 picks = 48, as the report expected ("48 extra calls"). The sync's
progress lines read `+ events.data_checked_seen_utc`, `+ picks.fetched_at_utc`
(the two migrations), then `live stats GW1 ...` to `GW7 ...` and the seven
entries. Check 1 "10 core calls, all HTTP 200" counts the core endpoints.

**First sight (acceptance test 1).** `events` on the dry-run database has 9
columns (`data_checked_seen_utc` added; 8 before). GW1-6:
`finished 1, data_checked 1, data_checked_seen_utc '2026-10-20T10:58:26+00:00'`,
one distinct value, equal to the bootstrap fetch time the log prints
(`PRICE DATE FLAG: fetched 2026-10-20T10:58:26+00:00`). GW7
(`finished 0, data_checked 0`), GW8, GW9: NULL. The text dump `fpl.sql`
carries the same (`CREATE TABLE events (... data_checked, data_checked_seen_utc
TEXT)`, the six rows with the time, GW7-8 NULL).

**Fetch times and finality (acceptance test 2).** On the dry-run database,
every row of GW1-7 has a non-NULL `fetched_at_utc`: `player_gw` GW1 610 rows at
10:58:27 ... GW7 668 at 10:58:30; `entry_gw` 7 rows per GW at 10:58:32-10:59:06;
`picks` 105 rows per GW (8 columns now, `fetched_at_utc` added, written with
the entry_gw row's time); `automatic_subs` 1/2/1/3/3/4/4 rows GW1-7. Before
(`e1154dd`): GW1-6 `player_gw` (3883 rows) and `entry_gw` (42) all NULL, `picks`
without the column, `automatic_subs` empty; GW7 fetched 22:05:05-22:05:17. So
every GW1-6 row was provisional by the ruling's definition and was re-fetched,
and every re-fetched row is now dated after the first sight (earliest
10:58:27 > 10:58:26; no same-second collision).

The item's own `is_final` (imported from `df867cb`, run on a read-only copy of
the dry-run database, no API): GW1-6 `player_gw` True, `entry_gw` 7/7 True,
`picks` 7/7 True; GW7 all False (seen NULL); GW8 all False. The run after this
one would therefore re-fetch none of GW1-6 and only GW7 (data_checked 0), the
"once, then never" of acceptance test 3. The pre-verifier's rehearsal showed
the same shape (73 then 25 calls).

**Stored v final (ruling point 3, acceptance test 6), 19 Oct 22:05 -> dry run:**

| GW | entry_gw points changed | moves |
|---|---|---|
| 1, 2, 5 | 0 of 7 | - |
| 3 | 7 of 7 | +6, +6, +9, +16, +18, +19, +21 |
| 4 | 6 of 7 | +2, +2, +6, +8, +11, +11 |
| 6 | 5 of 7 | +1, +2, +2, +2, +6 |
| 7 (in progress, not S2b's) | 6 of 7 | +2, +2, +2, +9, +11, +13 |

GW3, GW4 and GW6 are the rehearsal's numbers to the point. GW7 moved because
its Monday match finished between the two fetches (fixtures GW7: 0 of 10
`finished` at 22:05, 10 of 10 at 10:58; `data_checked` still 0), which is the
nightly's normal re-fetch of the open gameweek, not S2b's. The other entry_gw
columns that moved in GW1-6: `points` 18, `total_points` 18, `overall_rank` 28,
`points_on_bench` 13 (the provisional rows). `player_gw` GW1-7: 0 rows missing,
0 new, `total_points` unchanged in every gameweek. The changed cells are
`ruleset` NULL -> '2026-27' on every re-fetched GW1-6 row (S2's "scored rows
carry ruleset", written by any fetch since S2) and, in GW4 and GW6 only, `bps`
10 + 4 = 14, `expected_goals` 8 + 8 = 16, `expected_assists` 5 + 4 = 9,
`defensive_contribution` 5 + 3 = 8, `minutes` 2 + 0 = 2: exactly the report's
field counts (bps 14, xG 16, xA 9, defcon 8, minutes 2). GW7: 10 rows (in
progress). `automatic_subs`: 0 -> 14 rows for GW1-6 (1, 2, 1, 3, 3, 4), 4 for
GW7.

**Check 22 (ruling point 2, acceptance test 4).** The status file:
`22 OK manager score reconciliation: 42 entry-gameweeks in GW1-GW6, every one
equal; GW7 not locked down: silent mid-gameweek (ruling S3, point 6)`. My run
of `checks.c22` from `df867cb` with my own `Ctx` (the dry-run database, the
dry-run export, now = the status file's 10:59:08Z) returns that string to the
character. An independent walk over `checks.entry_points` for the 7 entries x
GW1-6: 42 graded, 0 mismatches, 0 None. The same on the 19 Oct database and
export: `SKIP no entry with its substitutions stored in GW1-GW6; GW7 not
locked down ...`, 42 None (no substitutions stored), which is the before state
the report describes. GW7 (information, not graded): computed = FPL for all 7
on the dry-run database; on the 19 Oct database 5 of 7 differ, the provisional
rows of the open gameweek.

**The rest of the dry run.** `Ran 635 tests ... OK (skipped=12)`, `TESTS OK`;
`RESTORED` 5 exports; `ODDS SKIPPED (dry run): odds_live not ticked` (the one
WARN, expected: check 30); `RECORD OK own 277 / xg 257 / minutes 257 /
bottomup 257 / fpl_ep 668`, each "3 days, 6:30:5x before deadline" (GW8
deadline 23 Oct 17:30 UTC); `ARCHIVE OK`; `STATUS WARN ... checks 28/29`,
27 SKIP (manual workflow glance), 23 OK "6 file(s) to commit, none holds a
key pattern or the key value". The commit `4b199eb` exists on `data-dryrun`,
so `fpl_publish.py`'s gate accepted the database with the two new columns.
Nothing in the dry run contradicts the code-level verification; every number
the pre-verifier's rehearsal predicted (73 calls, GW1-6 seen once, the entry_gw
moves, total_points unchanged, 14 automatic_subs rows, check 22 OK 42) is what
the GitHub run produced.

## Check 1 - point-in-time: PASS (data-pipeline form)

The item produces no forecast, feature or metric; it re-fetches actuals of
locked-down gameweeks (every row fetched 20 Oct, after every GW1-7 deadline by
construction) and adds two columns. No forecast reads `data_checked_seen_utc`
or `picks.fetched_at_utc`. The truncation test and shift probe have no
forecast to act on; the recording path is check 5.

## Check 2 - clean-checkout test runs: PASS

`python -m unittest discover -p "test*.py" -s . -t .` on `git archive` exports,
Python 3.14.7, `ODDS_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN` removed:

| run | `a00ccc7` (the dry-run commit) | `df867cb` (HEAD) |
|---|---|---|
| bare (no `FPL_DATA_DIR`) | **635 OK**, skipped=10, exit 0 (300 s) | **708 OK**, skipped=10, exit 0 (323 s) |
| `FPL_DATA_DIR=C:\GIT\FPL-data` (read-only) | **635 OK**, skipped=3, exit 0 (291 s) | **708 OK**, skipped=3, exit 0 (310 s) |

No FAIL or ERROR line in any of the four. 635 is the dry run's own count
(`skipped=12` there: Linux, no stand-in zones); 708 - 635 = 73 = the landing's
new tests (test_S11-S14, S6b-S6d, S8, bundle, provenance), all green on top of
S2b. `C:\GIT\FPL-data` after the two data runs: sha256 of `fpl.sqlite`,
`projection_log.csv` and `fpl_export_gw7.json` unchanged, `git status
--porcelain` unchanged (`e1154dd`). The pre-verifier's stand-in-zone and
hermetic runs stand for the identical code.

## Check 3 - pre-registered evaluation: n/a (descriptive; reproduced above)

The prereg's metric, bootstrap and threshold are n/a. The descriptive
measurement (stored v final per gameweek, the call count, check 22) was
recomputed by me from the two committed databases and matches the report's
rehearsal and the status file.

## Check 4 - metric, filter, bootstrap, threshold: n/a; ruling present: PASS

All n/a in the prereg; nothing promoted or re-tuned; the ruling is verbatim
and predates the code (above).

## Check 5 - recording path: PASS

`projection_log.csv` on `4b199eb` against `e1154dd`'s: the 19 Oct file
(383,168 bytes, 7,489 lines) is a byte-prefix of the dry run's (470,968 bytes,
9,205 lines); `git diff` removes 0 lines; the 1,716 new rows are all GW8,
`made_at` 2026-10-20T10:59:06/07+00:00: own 277, xg 257, minutes 257,
bottomup 257, fpl_ep 668 = check 18's growth line and the RECORD lines. No
row of any model moved; the only difference is the night's new rows. (The
row counts differ from 19 Oct's 281/261/261/261/668 by the night's
availability changes, not by code: the record code is untouched by S2b and by
the landing.) The pre-verifier's frozen-clock regeneration (byte-identical,
clock aside) stands for the code at `19b303c` = the code here.

## Check 6 - mutation spot-check: PASS (2 of 2 red)

Fresh copies of `df867cb`, `python -m unittest tests.test_S2b` (21 tests):
- `is_final`: `t > seen` -> `t >= seen` (the same second counted as later):
  `FAIL: test_the_same_second_is_not_later`, 1 failure.
- `c22`: `locked = locked[-1:]` after line 455 (the latest locked gameweek
  only): 3 failures (`EveryLockedGameweek`: `test_all_equal_is_ok_and_names_the_gameweeks`,
  `test_an_earlier_gameweek_is_reconciled_too`, `test_every_mismatch_is_listed`).
The pre-verifier's 17 mutations on the identical code also stand.

## Check 7 - secrets: PASS

The seven changed files (`git diff 8d0a50b df867cb --name-only`), searched for
`apiKey=`, `api_key=`, `Authorization`, `Bearer `, 32+ hex characters: only the
pre-existing value-free hits (`checks.py:733` a header from a variable;
`test_fpl.py:4498` a git SHA `ea7a...`; `tests/test_S3.py:961-962` the action
SHAs `3d3c...`, `5fda...`) and the pre-verifier report's own description of
this search. The added lines hold none. The dry run's `status_dryrun.txt`,
`run_2026-10-20.log`, `fpl_2026-10-20.txt`, `watch_2026-10-20.txt`: no hit.
`ODDS_API_KEY` is not set in this shell; the dry run made no Odds call.

## Runner path

S2b changes the sync (`fpl_sync.py`) and the checks (`checks.py`) and nothing
else the nightly runs or imports (the file lists above). `fpl_nightly.py`,
`fpl_edge.py`, `fpl_gate.py`, `fpl_publish.py`, `fpl_odds.py`, `fpl_xpv2.py`
and `.github/` are identical on `8d0a50b`, `a00ccc7` and `df867cb`. The
record path cannot move: it reads the export, which the pre-verifier showed
equal except `generated`, and the dry run's log is the 19 Oct log plus the
night's rows.

## Observations (information, no verdict weight)

- The dry run's database lives on `data-dryrun`; `data` (`e1154dd`) still has
  NULL fetch times for GW1-6, so tonight's real dispatch is "the first real
  run" of the ruling and will re-fetch GW1-6 once (73 calls) and set the
  first sight to its own bootstrap time, as the dry run did.
- GW7 was not locked down at 10:58 UTC (data_checked 0 with all 10 fixtures
  finished); if FPL ticks it before tonight's run, GW7 gains a first sight
  tonight and its rows (fetched after that bootstrap) are final at once, while
  check 22 starts grading it.
- `ruleset` NULL -> '2026-27' on every re-fetched GW1-6 row is S2's column
  being written by the first fetch since S2; the frozen `p1_eval.py` and the
  calibration read points and minutes, which did not change.
- The merge window: GW8's deadline is 23 Oct 17:30 UTC, so the 30-hour runner
  freeze starts 22 Oct 11:30 UTC; a merge before 21:00 UTC today is outside it.

## Write guard

In the s2b worktree `git status` showed nothing at launch; after this run it
shows only `?? worklog/verify_S2b.md`. `C:\GIT\FPL` still shows
`?? worklog/verify_S2b_pre.md`, `?? worklog/verify_W1b_pre.md` (there at
launch). `C:\GIT\FPL-data` (`e1154dd`, hashes and status unchanged) and the
data branches were only read.

VERDICT: PASS

Reason: S2b's code on `df867cb` is line-for-line the code the pre-verifier
passed on `19b303c`/`316652a` (280 identical diff lines; `tests/test_S2b.py`
unchanged; the merges brought only tests, tools and docs, none on the runner
path), and the GitHub dry run at `a00ccc7` did what the ruling and the prereg's
acceptance tests say: 73 calls = the usual 25 plus 6 live and 42 picks for
GW1-6, the first sight written once as the bootstrap time 10:58:26 for GW1-6
and NULL for GW7+, every re-fetched row dated after it so `is_final` is True
for all of GW1-6 and False for GW7 (once, then never), `picks.fetched_at_utc`
written, entry_gw points moved exactly as the rehearsal measured (GW3 +6..+21
all seven, GW4 +2..+11 six, GW6 +1..+6 five) with player_gw total_points
unchanged, 14 automatic_subs rows gained, and check 22 "42 entry-gameweeks in
GW1-GW6, every one equal" reproduced by my own Ctx and an independent walk;
the suite is green on clean copies of both commits bare and with the real data
(635/635 and 708/708, the real data folder untouched by hash), the projection
log is the 19 Oct log plus the night's 1,716 new GW8 rows with 0 rows removed
or changed, two mutations go red, and no changed file or dry-run output holds
a key.
