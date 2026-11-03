# Verifier report: W2 (wiring: chips, league, bottomup_lambda, sync columns)

Verifier: backtest-verifier agent, model Fable 5.1 (claude-fable-5-1), effort high,
instructions read from `.claude/agents/backtest-verifier.md` on disk (identical to
the loaded instructions). Date: 2026-10-19. Item type: descriptive / data-pipeline
(no pass/fail metric in the prereg): checks 1, 2, 5, 6, 7 and the item's own
acceptance tests; checks 3 and 4 are n/a beyond the prereg-order and ruling checks.

Tree verified: worktree branch `w2-wip`, HEAD 109e58a (off master 6a94467), clean
(`git status` empty). Nothing was edited in the worktree, in `C:\GIT\FPL` or in
`C:\GIT\FPL-data` (its `fpl.sqlite`, `projection_log.csv`, `fpl_export_gw7.json` and
`odds/` hashes identical before and after this run). All suites, mutations,
migrations and regenerations ran on scratch copies under the session scratchpad
(`v/base` = `git archive 6a94467`, `v/w2` = `git archive 109e58a`, `v/data` = a copy
of the data worktree). No git pull/fetch/commit/push/checkout was run anywhere.

## Prereg order (PASS)

`prereg/W2.md` was committed at 08d6a95 (13:23), amended at 6efb6a4 (14:19, RULING
W2 standings + lanes merge) and fc56fd5 (16:40, RULING 19 Oct afternoon); the first
W2 code commit is 4d48697 (18:10). `git merge-base --is-ancestor` confirms all three
precede 4d48697. The rulings (RULING W2 build, the W2 addition of 18 Oct, RULING
morning 19 Oct point 3, BUILD_PLAN Part E item 8, Step 9 item 4, the standings
amendment, RULING 19 Oct afternoon) are present verbatim in the prereg. Code
commits: 4d48697 (a), aa5352a (b), 451ade6 (c), 109e58a (a test). 14 files changed,
no change under `.github/`, `.gitleaksignore` or `requirements.txt`.

## Check 1: point-in-time (PASS)

The only new recorded feature is `bottomup_lambda` (source name new; the five
existing sources are untouched). It exists for one evaluated gameweek today, GW8
(the next deadline), so earliest = middle = latest.

a. Truncation test: rebuilt GW8 `bottomup_lambda` from only the pre-deadline
   inputs - the export `fpl_export_gw7_2026-10-19.json.gz` (generated
   2026-10-19T06:13:10Z, gameweek 7) and the odds snapshot
   `odds_2026-10-19T0613Z.json.gz` (taken 2026-10-19T06:13Z, 107.3 h before the
   GW8 deadline 2026-10-23T17:30Z) - through `tools/odds_lambda.py`
   (`sqlite_tables` -> results, `fit_fallback`, `newest_snapshot`, `snapshot_book`,
   `rebuild_2627`), and compared with the runner's `fpl_lambda.bottomup_lambda`:
   264 rows, identical after the record's `round(., 3)`, max abs diff 0.0; the
   unrounded `rebuild_2627` dicts are equal float for float (sources included),
   the fallback models equal. 264 of 264 players have odds-priced fixtures, so the
   fallback path was not exercised on real data; `tests/test_W2.py` exercises it
   on the toy (one fixture without odds).
b. Timestamp audit: snapshot 2026-10-19T06:13Z < deadline; export generated
   06:13:10Z < deadline; `results_before` uses the export's `fixtures_played`
   (finished = 1, `team_h_score IS NOT NULL`, event <= 7): 60 results, max kickoff
   2026-10-12T19:00Z, all before the deadline and before the export was
   generated; the export's `player_gw_recent` max event is 7 (no GW8 player data
   exists). `newest_snapshot` takes only files with `taken < deadline`; the
   snapshot's time comes from its file name (the payload is a bare list, no fetch
   field), which W1's `fpl_odds.py` mints at fetch time. The sync's results in
   `fpl.sqlite` (the tool's input) equal the export's `fixtures_played` (60 = 60,
   as sets).
c. Shift probe: n/a, no correlation metric in this item.

The CHIPS and LEAGUE sections are report text, recorded nowhere; they read the
data folder read-only (tree hash of `v/data` unchanged after both the tools and
the runner ran).

## Check 2: clean-checkout suites (PASS)

`python -m unittest discover -p "test*.py" -s . -t .`, `FPL_DATA_DIR` unset:
- master 6a94467 (`v/base`): Ran 614 tests in 392 s, OK (skipped=10)
- W2 109e58a (`v/w2`): Ran 625 tests in 398 s, OK (skipped=10)
- W2 with `FPL_DATA_DIR` = the scratch copy of the data folder: Ran 625, OK
  (skipped=3)
+11 tests = `tests/test_W2.py` (11). The implementer reported 9 skipped bare; this
PC shows 10 on both master and W2 (the same set skips before and after, so W2 adds
no skip). The stand-in-zones variant was not run (no zone files here), as the
implementer also reported.

## Check 5: recording path (PASS)

Frozen clock (`datetime.datetime` replaced by a subclass whose `now()` returns
2026-10-19T21:50:00Z, which `record_status`'s local `from datetime import
datetime` picks up), the same copy of the real `projection_log.csv`,
`fpl_export_gw7.json` and `odds/`, horizon 6, each source in turn:
- master's `fpl_edge`: RECORD OK own 285, xg 264, minutes 264, bottomup 264,
  fpl_ep 668
- W2's `fpl_edge`: the same five lines and RECORD OK bottomup_lambda 264
  (snapshot odds_2026-10-19T0613Z.json.gz, 264 of 264 players with odds-priced
  fixtures)
The rows of each of the five sources are identical between the two logs, and the
W2 log with its 264 `bottomup_lambda` lines removed is byte-identical to master's
log (383,848 bytes). No sqlite file was created by the record (the record never
opens the database). Real log today holds 0 `bottomup_lambda` rows (the item is
not merged).

## Check 6: mutations (PASS, 5 of 5 red)

Each in its own copy of the W2 tree, `tests.test_W2` run (11 tests):
1. `fpl_sync.export`: drop `AND COALESCE(s.label_error, 0) = 0` ->
   `test_the_export_skips_a_flagged_row` FAIL
2. `fpl_lambda.results_before`: `if k < deadline` -> `if True` ->
   `test_the_numbers_are_the_tools` FAIL (the post-deadline result is read)
3. `checks.c31`: `return WARN, _short(bad)` -> `FAIL` ->
   `test_check_31_warns_and_never_fails` FAIL
4. `fpl_edge.record_status`: `if skipped:` -> `if not skipped:` ->
   `test_the_record_and_the_skip` FAIL
5. `fpl_sync.migrate`: `if "standings.label_error" in added:` -> `if False:` ->
   `test_migration_flags_the_mislabelled_rows_and_keeps_every_row` FAIL
Each mutant failed exactly one test, the intended one; the other 10 stayed green.

## Check 7: secrets (PASS)

The 14 files W2 adds or changes were scanned for `apiKey=`, an Authorization
header value, the Odds API host with a key, GitHub tokens and 32+ hex strings.
No key, no URL with a key, no header value. The only 32+ hex hits are pre-existing
test fixtures outside W2's hunks (test_fpl.py line 4500 `ea7a...`, tests/test_S3.py
lines 962-963 `3d3c...`, `5fda...`). The odds snapshot used contains no `apiKey`
or `Authorization` string. `checks.py`'s `Authorization` header construction
(line 736) predates W2 and is not in its diff.

## Acceptance tests of the prereg

1. Report sections (PASS). On the real data copy: `tools/chips.py live()` 37 lines
   == `fpl_chips.live` 37 lines; `tools/league.py report()` 69 lines ==
   `fpl_league.report` 69 lines (same `today`); `fpl_sections.sections()` returns
   exactly those lists; a rerun is identical (seeded). The CLI appended 114 lines
   (two 4-line ruled headers + 37 + 69) to a copy of the night's report, prefix
   kept, LF only, the pound sign as UTF-8. With an empty data folder both sections
   print one `<SECTION> SKIPPED: <why>` line and the CLI exits 0 (test). Check 31
   "report sections": OK on `CHIPS OK n lines` + `LEAGUE OK n lines`, WARN on a
   SKIPPED line, on a missing line and on `SECTIONS FAILED`; `SEVERITY[31] = WARN`;
   the nightly never adds "sections" to `failed` (test with a stub exiting 3). The
   nightly echoes child stdout verbatim into the run log, so the status lines land
   at column 0 as `c31`'s regex expects (the real run log shows `RECORD OK ...`
   lines the same way). Verbatim copy: every top-level definition of `fpl_chips.py`
   (24), `fpl_league.py` (28), `fpl_bt.py` (39), `fpl_pit.py` (5) has a
   same-named definition in `tools/chips.py`, `tools/league.py`,
   `tools/backtest.py`, `tools/hist_pit.py` with an identical source segment
   (`ast.get_source_segment`); 0 differ, 0 extra; the module aliases are kept
   (`fpl_bt as BT`, `fpl_pit as PIT`, `fpl_edge as E`, `fpl_hist as H`).
2. bottomup_lambda (PASS). `fpl_lambda.py`: 30 definitions identical to
   `tools/odds_lambda.py`, 2 additions (`results_before`, `bottomup_lambda`), no
   `sqlite3` import, no tools import. Numbers identical (check 1a). No snapshot
   before the deadline -> `RECORD_SKIP`, `RECORD SKIP bottomup_lambda no odds
   snapshot before the GW9 deadline ...` (test; also a snapshot dated after the
   deadline is never used). `c29`: SKIP of `fpl_ep` or `bottomup_lambda` is a
   WARN ("the other 5 recorded"), SKIP of a frozen source or a missing source
   FAIL. `SOURCES` in `fpl_nightly.py` and `checks.py` are the six and equal
   (test_W1). Check 18 counts new rows per source without naming them. The
   `NightlyRunner` real-world test (the fpl_run.bat steps) expects the five
   recorded and a `RECORD SKIP bottomup_lambda` in a world without `odds/`. The
   five sources keep byte-identical rows under a frozen clock (check 5).
3. fetched_at_utc (PASS). The migration adds `transfers.fetched_at_utc`,
   `chips.fetched_at_utc`, `player_history.fetched_at_utc`,
   `standings.fetched_at_utc` (and `players.code`, `standings.label_error`); on
   the real copy every stored row keeps NULL (0 of 67 transfers, 0 of 12 chips, 0
   of 1927 player_history, 0 of 42 standings non-null); every write path sets it
   (named-column INSERT OR REPLACE, test with a fake API). `picks` is S2b's, not
   in this tree.
4. Standings, as amended (PASS). On a scratch copy of the real `fpl.sqlite`
   (unmigrated, 42 standings rows, events 2-7 x 7 entries): `migrate` flagged
   exactly 7 rows, all event 2, entries 18931, 881799, 2322726, 3073318, 4866471,
   5826302, 8690100 (totals 217/243/229/204/208/216/176 against the GW2 chain's
   172/190/173/145/160/150/108), one line printed per row; the five original
   columns of all 42 rows unchanged; every table's row count unchanged; every
   other row `label_error = 0`; no event-2 row off the chain unflagged. A second
   `migrate` prints nothing and re-flags nothing (a row reset to 0 stays 0). The
   export skips `label_error = 1`: `export(db, 7)` under master's code on the
   unmigrated copy and under W2's code on the migrated copy are identical aside
   from `generated` (7 standings rows each); `export(db, 2)` gives 7 rows under
   master and 0 under W2 (GW2 league rank "not recorded", per the ruling). The
   only direct readers of the `standings` table are the two queries in
   `fpl_sync.py`; the report sections and `fpl_edge` read the export's
   already-filtered `standings`.
5. players.code (PASS). Column added by migration and in the fresh SCHEMA; filled
   from the bootstrap element (test: id 1 code 111, id 2 None). The export is
   unchanged (acceptance 4's comparison).
6. Tests (PASS). 11 tests in `tests/test_W2.py`, hermetic (in-memory or
   temporary folders, a fake API, tools imported only by tests); suite green bare
   and with the data folder; mutations above; the frozen-clock regeneration above.
7. The runner never imports tools/ (PASS). `tests/test_S3.py
   FastTrack.test_the_nightly_imports_nothing_under_tools_or_analysis` parses every
   root `.py` (the six new modules included) and passed; a grep of the runner
   files finds no `backtest`, `chips`, `league`, `hist_pit`, `odds_lambda` or
   `tools` import. Every import in the new modules is standard library or an
   existing runner module.

## Information only (no bearing on the verdict)

- The flagging rule is "event 2 and total != the GW2 entry_gw total". On the real
  copy, standings rows of events 3, 4, 6 and 7 also differ from their entry_gw
  totals by 2-11 points (e.g. entry 5826302 event 7: 487 vs 485), so the rule
  would misfire if ever widened beyond event 2; as written it selects exactly the
  seven. The flagged totals do not equal the entries' GW3 chain totals either
  (217 vs 208 etc.), consistent with the standings snapshot and the entry_gw
  chain being fetched at different times. Not a W2 matter; worth a look in the
  S9 follow-up.
- `fpl_sections.MISSING` includes `KeyError` and `OSError`, so a programming error
  surfacing as a KeyError inside a section is reported as `SKIPPED` (a WARN) rather
  than `SECTIONS FAILED` - the same WARN either way, as ruled.
- With `FPL_DATA_DIR` set the suite skips 3 tests here (no zone data); bare it
  skips 10 on both master and W2.

VERDICT: PASS

Reason: the prereg and all its rulings were committed before the first W2 code
commit; every one of the 126 definitions copied into the six new runner modules
is segment-identical to its `tools/` source, and on the real data the runner
reproduces the tools exactly (bottomup_lambda 264 rows, max diff 0.0; CHIPS 37
and LEAGUE 69 lines identical) from inputs all dated before the GW8 deadline; the
migration on a copy of the real database flags exactly the seven event-2 rows
named in the ruling, keeps all 42 rows byte for byte, is idempotent and leaves
the GW7 export identical; the five existing sources' projection-log rows are
byte-identical under master's and W2's `fpl_edge` with a frozen clock; the suite
goes 614 -> 625 OK bare and 625 OK with the data folder; five mutations each
turned exactly the intended test red; no secret appears in any file the item
touches; the nightly imports nothing under `tools/`.
