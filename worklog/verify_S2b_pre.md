# Verifier pre-check: S2b (the final re-fetch until data_checked)

Code-level verifier run before the item's GitHub dry run (Tuesday). Written
2026-10-19, about 00:30 UTC, by the backtest-verifier agent. Model: Fable 5.1
(claude-fable-5-1); effort: high, as `.claude/agents/backtest-verifier.md`
says (read from disk first; it matched the loaded instructions). The checks
are applied in their data-pipeline form (the prereg has no pass/fail metric):
1, 2, 5, 6, 7 plus the item's own acceptance tests; 3 and 4 are n/a where the
prereg says n/a, except check 4's "ruling present verbatim" part, decided below.

Nothing was pushed, fetched into or changed in `C:\GIT\FPL`, `C:\GIT\FPL-data`
or `C:\GIT\FPL-b`; no tag, hook or config was touched; no workflow was
dispatched; no Odds API or FPL API call was made by me (the implementer's
rehearsal databases were read as files). GitHub was read with `git ls-remote`
only. All scratch work is under the session scratchpad: a clone of
`C:\GIT\FPL` (`v/repo`) with worktrees at `ab047c3` (`v/base`), `19b303c`
(`v/item`), the data tip `9da6ff1` (`v/data9`, `v/gate9`), copies for the
mutations, and blobs read with `git cat-file`.

## What was verified against

- GitHub (`git ls-remote`): master `d813953`, s2b-wip `19b303c`, w1-wip
  `ab047c3`, data `9da6ff1`. `C:\GIT\FPL`'s local refs agree; `C:\GIT\FPL-data`
  is at `9da6ff1`, clean; `C:\GIT\FPL-b` at `e7e86e9` (only read).
- The item: `8b11ce6` (merge of master `f612a2c` into w1-wip `ab047c3`;
  `git diff ab047c3 8b11ce6` touches `prereg/S2b.md` and
  `worklog/SESSION_STATE_A.md` only) and `19b303c`, the one code commit:
  `checks.py` (+56/-), `fpl_sync.py` (+77/-), `test_fpl.py` (14 lines),
  `tests/test_S3.py` (3 lines), `tests/test_S2b.py` (+376, new); 5 files,
  nothing else.

## Prereg and commit order: PASS

`prereg/S2b.md` was committed in `f612a2c` at 2026-10-18 23:10:03 UTC
(01:10:03 +02:00); the code commit `19b303c` is at 23:38:16 UTC. `f612a2c` is
an ancestor of `19b303c` and the file is byte-identical on both. The ruling
block ("RULING S2b (runner fix, priority over the night-work queue) ... END
RULING", points 1-4) is in the file verbatim as quoted in the task, plus the
six acceptance tests.

## Check 1 - point-in-time: PASS (in its data-pipeline form)

The item produces no forecast, feature or evaluation metric: it changes which
stored rows of past gameweeks are fetched again and adds one column to
`events` and one to `picks`. The rows it re-fetches are actuals, fetched after
their gameweek's deadline by construction; no forecast reads them. Evidence
that the recorded forecasts do not move: check 5 (byte-identical regeneration,
the clock aside) and the calibration (the only metric that reads these rows)
reproduced identically on the before and after exports of the rehearsal
(`--section calibration` with the `19b303c` code on `cal_before` and
`cal_after`: `diff` empty; my before output equals the implementer's
`cal_before.txt`). The truncation test and the shift probe have no forecast to
act on.

## Check 2 - clean-checkout test runs: PASS (499 -> 520)

`python -m unittest discover -p "test*.py" -s . -t .`, `ODDS_API_KEY`,
`GH_TOKEN`, `GITHUB_TOKEN` removed, Python 3.14.7, SQLite 3.50.4:

| run | `ab047c3` | `19b303c` |
|---|---|---|
| bare (no `FPL_DATA_DIR`) | **499 OK**, skipped=9 | **520 OK**, skipped=9 |
| runner-like: `GITHUB_ACTIONS=true GITHUB_REF=refs/heads/s2b-wip FPL_DRY_RUN=true FPL_DATA_DIR` = scratch worktree of `9da6ff1` after `fpl_nightly.py --restore` (RESTORE OK, 5 exports) | - | **520 OK**, skipped=2 |
| stand-in zones: `PYTHONTZPATH` = the scratch `tz/Europe/{London,Prague}` copies | - | **520 OK**, skipped=7 |
| hermetic: `env -i` with PATH/SYSTEMROOT/TEMP/TMP, empty HOME, USERPROFILE, XDG_CONFIG_HOME, `GIT_CONFIG_NOSYSTEM=1`, empty `GIT_CONFIG_GLOBAL` | - | **520 OK**, skipped=9 |

Every run exit 0, no FAIL or ERROR line. The skip counts vary only with the
environment (zone database, real data present).

Red before the fix: `19b303c`'s `tests/test_S2b.py` copied onto an archive of
`ab047c3` and run alone: `Ran 21 tests ... FAILED (failures=6, errors=11)`,
17 of 21 red. The four green on the old code are the ones the old code also
satisfies (`test_the_nightly_rewrite_keeps_every_other_column_current`,
`test_final_gameweeks_are_not_fetched_again`, `test_the_old_guards_stay`,
`test_the_calls_are_counted`). The implementer's "16 of 20" plus the later
21st (`test_an_entry_never_stored_is_fetched`, an ERROR on the old schema)
is exactly this set.

## Check 3 - pre-registered evaluation: n/a (rehearsal reproduced)

No metric. The rehearsal's numbers were reproduced instead (below, "claim 8").

## Check 4 - metric, filter, bootstrap, threshold: n/a; ruling present: PASS

All n/a in the prereg; nothing promoted or re-tuned. The ruling is in
`prereg/S2b.md` verbatim and was committed before the code.

## Check 5 - recording path: PASS (byte-identical)

Two scratch folders with `9da6ff1`'s restored `fpl_export_gw7.json`,
`projection_log.csv` and `fpl.sqlite`; `fpl_edge.py --record --source <s>
--status` for own, xg, minutes, bottomup, fpl_ep, then `--watch watchlist.txt
--out` and `--diff --out`, with the `ab047c3` code and with the `19b303c` code:

- status lines identical: `RECORD OK own 285 / xg 264 / minutes 264 /
  bottomup 264`, `RECORD SKIP fpl_ep the export has no ep_next for any player`
  (the 18 Oct export was written by the pre-W1 master code, so it has no
  `ep_next`; the same on both sides);
- the two `projection_log.csv` (6833 rows each, same fields): 1077 rows differ
  in `made_at` only (the clock; the GW8 same-UTC-day rows of the four frozen
  sources), 0 rows differ in any other field;
- the watch file (6,273 bytes) and the report (30,069 bytes) byte-identical.
- Export: copies of `9da6ff1`'s `fpl.sqlite`, `migrate()` then
  `export(db, 7)` with each code in its own folder: the two JSON files are
  equal in every key except `generated`. The item's migrate prints exactly two
  lines beyond the base's: `+ events.data_checked_seen_utc`,
  `+ picks.fetched_at_utc`; after it `events` has 9 columns (38 rows, all
  `data_checked_seen_utc` NULL) and `picks` 8 (735 rows, all `fetched_at_utc`
  NULL).

## Check 6 - mutation spot-check: PASS (17 of 17 red)

My own batch (`v/verify_mutate_s2b.py`), each in a fresh copy of `19b303c`,
running `tests.test_S2b`, `test_fpl.DataGate` and
`test_fpl.SyncExportsSettledFlags` (52 tests) with no keys:

| # | mutation | red test(s) |
|---|---|---|
| V1 | events upsert without `COALESCE` (first sight moves) | `SeenTime.test_set_at_first_sight_and_never_changed` |
| V2 | `t > seen` -> `t >= seen` | `test_the_same_second_is_not_later` |
| V3 | never-seen data_checked counts as final | both `test_a_finished_gameweek_never_seen_data_checked_is_fetched_again` |
| V4 | no rows counts as final (`bool(times) and` dropped) | `test_an_entry_never_stored_is_fetched` |
| V5 | entries: picks finality not checked | `test_a_null_fetch_time_on_either_table_is_never_final` |
| V6 | picks stored with a NULL fetch time | `test_provisional_entry_rows_are_fetched_again_and_replaced`, `FirstRun.test_once_then_never` |
| V7 | player_gw: the old `finished` test back | 6 (`PlayerGwFinality` x5, `test_once_then_never`) |
| V8 | NULL fetch time not guarded | 3 |
| V9 | c22: only the latest locked gameweek | 3 (`EveryLockedGameweek`) |
| V10 | c22: mismatches truncated with `_short` | `test_every_mismatch_is_listed` |
| V11 | c22: mid-gameweek note dropped | `test_the_gameweek_in_progress_stays_silent` |
| V12 | migration without `data_checked_seen_utc` | `test_the_column_is_added_and_stored_rows_keep_null`, `test_fpl...test_migration_adds_data_checked_to_an_old_database` |
| V13 | migration without `picks.fetched_at_utc` | `test_the_column_is_added_and_stored_rows_keep_null` |
| V14 | a `DELETE FROM automatic_subs` in the sync | `DataGate.test_grow_only_holds_exactly_the_tables_the_sync_never_deletes_from` |
| V15 | a plain `INSERT INTO picks` (no OR REPLACE) | the grow-only proof, plus 5 `test_S2b` errors |
| V16 | events back to `INSERT OR REPLACE` (no upsert) | `test_set_at_first_sight_and_never_changed`, the grow-only proof, 3 more |
| V17 | entry finality ignored (always re-fetch) | 6 (`EntryFinality`, `test_once_then_never`) |

## Check 7 - secrets: PASS

The five files at `19b303c`, searched for `apiKey=`/`api_key=`, `Authorization`,
`Bearer `, 32+ hex characters and an `ODDS_API_KEY=` literal: the only hits
are pre-existing and hold no value (`checks.py:733`, the GitHub token header
from a variable; `test_fpl.py:5288` building a fake key at run time;
`test_fpl.py:4498` a git SHA `ea7a...`; `tests/test_S3.py:961-962` the action
SHAs `3d3c...`, `5fda...`). The added lines of the diff hold no key-like
string. The rehearsal's run logs hold the SYNC STATS line and the sync's
progress lines only.

## The implementer's claims, tested

1. Order - holds (above).
2. Point 1, first sight - holds. `SCHEMA` has the 9th `events` column and
   `MIGRATIONS["events"]` adds it (V12 red); the bootstrap writes `events`
   with `INSERT ... ON CONFLICT (id) DO UPDATE SET` naming every other column
   from `excluded` and `data_checked_seen_utc = COALESCE(events..., excluded...)`
   with the value `now` (the bootstrap fetch time) when `data_checked` is
   true, else NULL (V1, V16 red). The tests show a later sync, a re-run and a
   sync reading 0 again leave it, while `finished` and `data_checked` stay
   current. On the rehearsal: GW1-6 `seen 2026-10-18T23:38:37+00:00` after
   run 1 and unchanged after run 2; GW7, GW8 NULL.
3. Point 1, finality - holds. `is_final` returns True only when the event's
   seen time parses, the table has rows for the gameweek (and entry), and
   every row's `fetched_at_utc` parses and is strictly later (V2, V3, V4, V8
   red). `sync_player_gw` skips only on `done > 300 and is_final(...) and not
   refetch` (V7 red; the `finished` read is gone). `sync_entries` skips only
   when both `entry_gw` and `picks` are final for that entry (V5, V17 red);
   `picks` gets `fetched_at_utc` by SCHEMA and ALTER TABLE, written with the
   entry_gw fetch time (V6, V13 red). `main()` calls `sync_bootstrap` first,
   then fixtures, player_gw, league, entries, export, so every row fetch of
   one run is later than that run's first sight.
   Judged, "a re-fetch" as built: the ruling says "otherwise the sync
   re-fetches it" and names the two endpoints; the code fetches exactly
   those and replaces the gameweek's rows by primary key, which is what the
   grow-only rule (the gate's `GROW_ONLY`, the test, and S2) allows. It meets
   the ruling. The one residual: an `automatic_subs` row stored from a
   provisional answer that FPL later withdrew would stay (nothing deletes);
   it would show as a check-22 mismatch WARN rather than silently. Today no
   such row exists (0 rows before the first run; 14 after, all from final
   answers), so it is an observation, not a defect.
   Judged, the same-second edge and `done > 300`: "later than" in the ruling
   is read strictly, which is the literal reading; its cost is one more
   re-fetch of a gameweek whose first live fetch landed in the bootstrap's
   second, which the pause after every call and the bootstrap's own DB
   writes make unlikely (rehearsal: seen :37, first live row :39). The
   `> 300` guard is one the prereg's point 2 says stays. Both acceptable.
4. Point 2, check 22 - holds. It reconciles every started gameweek that
   `fpl_edge.gameweek_settled` accepts, in order; every mismatch is listed as
   `GW<g> <entry>: FPL <x>, computed <y>` with no `_short` cut (V9, V10 red);
   the latest started gameweek, when not locked down, is named in the tail
   (V11 red). On the rehearsal databases with the `19b303c` code and my own
   `Ctx`: before (`9da6ff1`) `SKIP no entry with its substitutions stored in
   GW1-GW6; GW7 not locked down: silent mid-gameweek (ruling S3, point 6)`;
   after run 1 and run 2 `OK 42 entry-gameweeks in GW1-GW6, every one equal;
   GW7 not locked down ...`. My independent walk over `entry_points` gives
   the same: 42 graded, 0 mismatches, 0 None after; 42 None before.
   Judged, "WARNs per mismatch": a check returns one (level, detail); one
   WARN whose detail lists every mismatch, each with gameweek, entry, FPL
   and computed, is the form the framework allows and the form the prereg's
   acceptance test 4 (committed before the code) states. Met.
5. The grow-only proof - sound. The widened test still forbids DELETE, DROP,
   TRUNCATE and VACUUM; every `INSERT OR <mode>` must be REPLACE; the only
   plain `INSERT INTO` admitted must be the one whose text continues with
   `VALUES (...) ON CONFLICT (id) DO UPDATE SET`, and that list must be
   exactly `["events"]`. An upsert's DO UPDATE changes the colliding row in
   place and removes none, and its SET list (read) does not touch `id`.
   A DELETE (V14), a plain INSERT into another table (V15) and an OR IGNORE
   (by the mode set) are all still caught.
6. Tests - hold: 21 tests, 17 red on the old code, 499 -> 520 green bare,
   runner-like, with stand-in zones and hermetically; the two existing tests
   changed are the events-migration column count (8 -> 9) and the S3
   Reconciliation picks insert naming its 7 columns; 17 of my own mutations
   red.
7. Recording path - holds (check 5).
8. Rehearsal - every file reproduces:
   - `s2b_before.sqlite` sha256 `a4ac...` = `git cat-file blob
     origin/data:fpl.sqlite` at `9da6ff1`; `cal_before/fpl_export_gw7.json` =
     the gunzipped `exports/fpl_export_gw7_2026-10-18.json.gz` of that commit;
     both `projection_log.csv` copies = the commit's.
   - Run 1 log: 73 calls (bootstrap, fixtures, 7 live, league, 7 x (history,
     transfers, 7 picks)) = 7 live and 49 picks; run 2: 25 calls, GW7 only
     (its `data_checked` is 0, so it is fetched every night); the real 18 Oct
     nightly's SYNC STATS also lists 25.
   - `s2b_measure.py` re-run by me on before/after1: output byte-identical to
     `s2b_measure_preview.txt` (GW3 7 of 7 +6..+21, GW4 6 of 7 +2..+11, GW6
     5 of 7 +1..+6; player_gw total_points unchanged GW1-6; automatic_subs
     0 -> 14 rows GW1-6). Before/after2 differs only in GW7's fetch times.
     The ruling's "GW3-4 short 12-29 for every manager" is the GW3+GW4 sum
     per manager (12, 14, 18, 20, 21, 21, 29) and "GW6 1-6 for five rivals"
     matches (Boris's entry unchanged in GW6).
   - After run 2 against after run 1: `player_gw`, `entry_gw`, `picks`,
     `automatic_subs` rows for GW1-6 identical; only GW7 re-fetched; the
     `events` seen times identical.
   - `s2b_player_gw_diffs.txt`: 34 values in GW4 and GW6 (bps, xG, xA,
     defensive_contribution, 2 minutes), consistent with the measure's
     field counts.
   - Check 22: OK 42 after, SKIP before (above).
   - Calibration identical (check 1).
   - Inventory: on `9da6ff1` every GW1-6 `player_gw` (3883) and `entry_gw`
     (42) row has NULL `fetched_at_utc`, GW7's have 21:57-21:58; `picks` has
     no fetch column; `automatic_subs` is empty. First committed database
     with `data_checked = 1`: GW1-5 `09f6af6` (2026-10-05T19:41:24+02:00),
     GW6 `2c1573a` (2026-10-13T22:01:54Z), GW7-8 never - read from every
     committed `fpl.sqlite` on any ref (20 blobs; the implementer's 19 did
     not count the dry-run commit), with no API call.
   - Beyond the claims: `fpl_gate.py` with the `19b303c` code on the run-2
     database staged in a worktree at `9da6ff1`: `GATE OK integrity ok, 14
     tables, price_history 25882 rows, frozen forecasts unchanged; fpl.sql
     written` (exit 0), so the first real run's commit passes the gate.

## Observations (information, no verdict weight)

- The rehearsal exports differ in much more than the item (ep_next,
  transfers, prices, 1 h 41 min later); the item-attributable part is
  `player_gw_recent` xG/xA/bps/defcon for GW4 and GW6 and the new
  `automatic_subs`. After the first real run the xg and bottomup sources will
  read the corrected GW4/GW6 xG when they record GW8 and later; the models
  are unchanged, their inputs are now FPL's final ones. The frozen-clock
  regeneration on one export is byte-identical, which is what check 5 asks.
- The implementer's rehearsal called the live FPL API twice (23:38 and 23:39
  UTC, 98 calls) on scratch copies; the standing rule keeps the sync on the
  runner, and nothing in `C:\GIT\FPL-data` changed (`9da6ff1`, clean).
- A `picks` or `entry_gw` row an entry never had (an entry that joined late)
  is fetched every night, as it was before the item.

## Write guard

`git status` in `C:\GIT\FPL` shows `?? worklog/verify_W1_pre.md`,
`?? worklog/verify_W1_recheck.md` (there at launch) and this file, untracked;
HEAD `d813953` = master, s2b-wip `19b303c`, w1-wip `ab047c3` as at launch.
`C:\GIT\FPL-data` (`9da6ff1`, clean) and `C:\GIT\FPL-b` were only read.

VERDICT: PASS

Reason: the ruling is in `prereg/S2b.md` verbatim and was committed (f612a2c,
23:10:03Z) before the one code commit (19b303c, 23:38:16Z); the first sight
is written once by an upsert and never moved, finality is the strict
"fetched later than the first sight, never NULL" the ruling asks, applied to
player_gw, entry_gw and picks with the old `--refetch` and 300-row guards
kept, and check 22 reconciles every locked-down gameweek, lists every
mismatch and stays silent mid-gameweek; the suite goes 499 -> 520 green bare,
runner-like, with stand-in zones and hermetically, 17 of the 21 new tests are
red on the old code, and all 17 of my mutations go red including three
against the widened grow-only proof, which stays sound; the recording path
regenerates byte-identically (clock aside) with an export equal except
`generated`; the rehearsal reproduces from the data tip's blobs (73 then 25
calls, the measured point moves, 42 entry-gameweeks equal, calibration
identical, GATE OK on the result); no changed file holds a key.
