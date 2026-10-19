# Verifier pre-check: W1 (fpl_ep and the Odds API collector)

Pre-check required by the fast-lane merge rule (S2 amendment 2, point 6b)
before the merge planned for Monday 19 Oct. Written 2026-10-18, about
21:30 UTC, by the backtest-verifier agent. Model: Fable 5.1
(claude-fable-5-1); effort: high, as `.claude/agents/backtest-verifier.md`
says (read from disk first; it matched the loaded instructions). The agent
file's checks are applied in their data-pipeline form (no pass/fail metric in
the prereg): checks 1, 2, 5, 6, 7 plus the item's own acceptance tests;
checks 3 and 4 are reported as n/a where the prereg says n/a.

Nothing was pushed, fetched into or changed in `C:\GIT\FPL`, `C:\GIT\FPL-data`
or `C:\GIT\FPL-b`; no workflow was dispatched; the Odds API was not called;
the real key was never read (fake keys were built at run time). GitHub was
read with `git ls-remote` only.

## What was verified against

- Code: a scratch clone of `C:\GIT\FPL`, worktrees at `7efc2b2` (the master
  base of w1-wip; `git diff --stat 1af9644 7efc2b2` touches only CHANGELOG,
  prereg and worklog files, so it is the 1af9644 code) and `d928ebe` (w1-wip
  head: `fec087a`, `a5b63bd`, `d928ebe` on `7efc2b2`; merge-base confirmed).
- Data: `e8629f0` ("nightly 2026-10-18", `C:\GIT\FPL-data` HEAD at launch and
  GitHub `refs/heads/data` at 21:29 UTC - tonight's 21:40 nightly had not
  committed yet) and the dry run `bf91cf5` ("dry run 2026-10-18 w1-wip
  d928ebe", one commit on `e8629f0`), fetched into the scratch clone from
  `C:\GIT\FPL`'s `refs/remotes/origin/data-dryrun`; GitHub
  `refs/heads/data-dryrun` is `bf91cf5` at 21:29 UTC. Blobs read with
  `git cat-file`.
- GitHub refs at 21:29 UTC: master `19690cc`, w1-wip `d928ebe`, data
  `e8629f0`, data-dryrun `bf91cf5`.

## Prereg and commit order: PASS

`prereg/W1.md` exists on master (`19690cc`) with the template rows and, verbatim,
RULING FAST-TRACK item 3, BUILD_PLAN.md Step 4 item 2, Step 5 item 1's
collector parts, RULING S1 amendment 1 item 1, "Decisions" (RULING W1
decisions, points 1-5) and "Odds storage" (RULING W1 odds storage, points 1-4).
Commit times (all 2026-10-18, +02:00):

| prereg commit | time | first code it precedes | time |
|---|---|---|---|
| `7efc2b2` prereg | 21:09:20 | `fec087a` W1 WIP | 21:34:52 |
| `91b10c7` decisions | 22:14:26 | `a5b63bd` decisions applied | 22:27:46 |
| `249be76` odds storage | 22:41:54 | `d928ebe` odds storage | 22:50:53 |

Note (information): w1-wip's own copy of `prereg/W1.md` is the `7efc2b2`
version without the two later rulings; they are on master, 25 lines ahead.
The merge brings the two together.

## Check 1 - point-in-time: PASS

fpl_ep is the item's only forecast; the odds snapshot is an input store.
Only one gameweek has been recorded (the first night), so the three-gameweek
truncation collapses to one.

- 1a Truncation (decides): the 668 `fpl_ep` rows of `bf91cf5`'s
  `projection_log.csv` (event 8, `made_at` 2026-10-18T21:06:04+00:00) were
  rebuilt from the dated export `exports/fpl_export_gw7_2026-10-18.json.gz`
  (`generated` 2026-10-18T21:06:02+00:00) as `(id, web_name,
  round(float(ep_next), 3))` for every player with a non-null `ep_next`:
  identical sets of `(player_id, web_name, predicted)` for all 668 rows
  (exact string equality, so within 1e-9). PASS.
- 1b Timestamps (decides): export generated 21:06:02 <= record 21:06:04 <=
  GW8 deadline 2026-10-23 17:30 UTC (`events.deadline_time` in
  `bf91cf5`'s `fpl.sqlite`; the log's "4 days, 20:23:55 before deadline"
  agrees). The odds file is named for its fetch minute
  (`odds_2026-10-18T2106Z`, run started 21:05:30 UTC); every event in it
  commences between 2026-10-19T19:00Z and 2026-11-02T20:00Z, after the
  fetch. PASS.
- 1c Shift probe: n/a, no correlation metric in the item.

The deadline guard is shared: `record_status` returns "deadline passed -
nothing to record" before the per-source branch, and
`test_fpl_ep_is_refused_at_the_deadline_like_every_source` covers it.

## Check 2 - clean-checkout test runs: PASS

All in scratch worktrees, with `ODDS_API_KEY`, `GH_TOKEN` and `GITHUB_TOKEN`
removed from the environment, `GITHUB_REF=refs/heads/w1-wip`,
`FPL_DRY_RUN=true`, `FPL_DATA_DIR` = a scratch worktree of `bf91cf5` after
`fpl_nightly.py --restore`.

| run | master base `7efc2b2` | w1-wip `d928ebe` |
|---|---|---|
| `python test_fpl.py` (does not discover `tests/`) | 386 OK, skipped=8 | 386 OK, skipped=8 |
| the nightly's command: `-m unittest discover -p "test*.py"` | **459 OK**, skipped=2 (no tz database) | **495 OK**, skipped=2 |
| same, with stand-in zones: `PYTHONTZPATH` = scratch copies of Git's `mingw64/share/zoneinfo/Europe/{London,Prague}` | - | **495 OK**, 0 skipped |
| hermetic: `env -i` with PATH/SYSTEMROOT/TEMP only, empty HOME, USERPROFILE and XDG_CONFIG_HOME, `GIT_CONFIG_NOSYSTEM=1`, empty `GIT_CONFIG_GLOBAL`, no identity | - | **495 OK**, skipped=2 |
| the dry run `bf91cf5`, ubuntu-24.04, from its log | 459 (S3 dispatch block) | **495 OK**, skipped=11 |

459 -> 495 as claimed, every run exit 0, no FAIL or ERROR line.
`tests.test_S3.Hermetic.FILES` is built from `os.listdir("tests")`, so
`tests/test_W1.py` is in the hermetic scan (code read, and the class passed).

## Check 3 - re-run of the pre-registered evaluation: n/a

The prereg has no metric. What the dry run reports was reproduced instead:
the five RECORD OK counts (own 285, xg 264, minutes 264, bottomup 264,
fpl_ep 668) by running `--record` myself on the same export (rows equal, see
check 5), and the odds line's figures from the stored file (21 events, 21 with
totals, 2736 prices of which 219 are `h2h_lay`, 10,472 bytes).

## Check 4 - metric, filter, bootstrap, threshold: n/a (rulings present)

All "n/a" in the prereg, as a data-collection item; nothing was promoted or
re-tuned after results. The three rulings the task names are in
`prereg/W1.md` verbatim (see above).

## Check 5 - recording path: PASS

- Same export (`bf91cf5`'s restored `fpl_export_gw7.json`), two scratch
  folders, `fpl_edge.py --record --source <s> --status st.txt` for own, xg,
  minutes, bottomup with the `7efc2b2` code and with the `d928ebe` code (plus
  fpl_ep with the latter): the 1077 rows of the four frozen sources are
  identical between the two codes in every field except `made_at`
  (the clock); status lines identical (`RECORD OK own 285 / xg 264 /
  minutes 264 / bottomup 264`).
- My `d928ebe` rows for all five sources equal `bf91cf5`'s GW8 rows of
  2026-10-18T21 for each source (285/264/264/264/668), field by field except
  `made_at`.
- Export: `fpl_sync.export(db, 7)` from both codes on a copy of `bf91cf5`'s
  `fpl.sqlite`, same second: the top-level keys are equal, and the only
  differing field anywhere is `all_players[].ep_next`.

## Check 6 - mutation spot-check: PASS (18 of 18 red)

Each in a fresh scratch copy of `d928ebe`, the named test module or class run
with the dry-run environment and no keys:

| # | mutation | red test(s) |
|---|---|---|
| M1 | fpl_edge: all-null ep_next returns FAIL instead of SKIP (the strict version) | `FplEp.test_a_missing_ep_next_is_a_skip_never_a_lost_night` (both subtests), `test_the_cli_writes_record_skip_and_exits_zero` |
| M2 | fpl_odds: `"xb"` -> `"wb"` | `OddsCollector.test_an_existing_file_is_never_rewritten` |
| M3 | fpl_gate: a rewritten odds file passes | `OddsAppendOnly.test_a_rewritten_odds_file_fails_the_gate` |
| M4 | checks: `CREDITS_WARN` 60 -> 0 | `OddsCheck.test_credits_below_60_are_a_warn` |
| M5 | fpl_sync: missing ep_next stored as 0.0 | `FplEp.test_the_sync_stores_ep_next_as_a_number_and_a_missing_one_as_null` |
| M6 | fpl_nightly: the suite sees the key (`drop=()`) | `NightlyOrder.test_the_odds_step_has_the_key_and_the_suite_does_not` |
| M7 | fpl_odds: a dry run calls the API without odds_live | `OddsCollector.test_a_dry_run_calls_the_api_only_with_odds_live` (3 subtests) |
| M8 | fpl_odds: the HTTP failure line carries the URL | `OddsCollector.test_a_failure_never_shows_the_url_or_the_key` |
| M9 | fpl_odds: odds also written to `fpl.sqlite` (`odds_snapshots`) | `OddsCollector.test_no_odds_go_to_sqlite`, `test_fpl.DataGate.test_grow_only_holds_exactly_the_tables_the_sync_never_deletes_from` |
| M10 | fpl_nightly: an odds crash appended to `failed` (night red) | `OddsNeverCostsTheNight.test_a_crashing_collector_and_the_night_still_commits` |
| M11 | nightly.yml: `ODDS_API_KEY` in a third step (Weekly backup) | `test_fpl.NightlyWorkflow.test_schedule_runner_and_steps` |
| M12 | checks: `BIG_FILE_MB` 50 -> 500 | `BigFiles` (2 tests) |
| M13 | checks c29: a skipped fpl_ep is a FAIL | `OddsCheck.test_a_skipped_fpl_ep_is_a_warn_and_a_skipped_frozen_source_a_fail` |
| M14 | checks: `SEVERITY[30]` WARN -> FAIL | `OddsCheck.test_ok_skipped_failed_missing` |
| M15 | fpl_odds: gzip without `mtime=0` | `OddsCollector.test_the_answer_is_written_byte_for_byte_as_deterministic_gzip` |
| M16 | fpl_edge: fpl_ep records only half the players | `FplEp.test_fpl_ep_records_ep_next_for_the_next_gameweek`, `test_some_null_players_are_counted_and_the_rest_recorded` |
| M17 | fpl_sync: export query drops `pl.ep_next` | `FplEp.test_the_export_carries_ep_next` |
| M18 | fpl_nightly: the odds step removed | `NightlyOrder` and `OddsNeverCostsTheNight` |

## Check 7 - secrets: PASS

- The ten files the item adds or changes at `d928ebe`, searched for
  `apiKey=`/`api_key=` followed by a value, `Authorization`, `Bearer `, and
  32+ hex characters: no API key, no URL with `apiKey=`, no header value.
  The hits are explained: `tests/test_W1.py` builds fake keys at run time
  (`"k" + secrets.token_hex(16)`); `checks.py:701` adds the GitHub token
  header from a variable (pre-existing code, no value); `fpl_gate.py:23-25`
  names the pattern in a docstring (present at `7efc2b2`); the action SHAs in
  the workflow and the git SHA in `test_fpl.py:4498` are not keys.
- `fpl_odds.py` builds the URL with `urlencode({"apiKey": key, ...})` and
  never prints, logs or writes it; failure lines carry the kind and HTTP
  status only (tests, and M8 red).
- The dry run's new or changed text files (run log, status, report, watch
  file): no key pattern, no `ODDS_API_KEY` value-like string, no 32-hex
  string. The run log shows the test suite's output and `ODDS OK ...` only.
- Inside the stored odds body: 21 32-hex strings, which are exactly the 21
  event `id`s; no `apikey` in any case.
- The scans read inside `.gz`: a fake key planted inside a gzip in `odds/`
  and staged -> `fpl_gate.py --secrets` says `SECRET FAIL ... commit nothing`
  (exit 1) with the key in `ODDS_API_KEY`; `checks.c23` on
  `changed_files()` -> FAIL naming the file; the pattern `ApiKey=` inside a
  gzip with no key in the environment -> `SECRET FAIL`. The real dry-run
  files with a fake key in the environment -> `SECRETS OK` and c23 OK
  (9 files, the odds file among them).
- Workflow: `ODDS_API_KEY: ${{ secrets.ODDS_API_KEY }}` appears exactly twice,
  in "Nightly run" and "Commit outputs to the data branch"; `FPL_ODDS_LIVE:
  ${{ inputs.odds_live }}` in the nightly step; the test suite is run by
  `fpl_nightly.py` with `ODDS_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN` dropped
  (M6 red).

## The implementer's claims, tested

1. fpl_ep - holds. `players.ep_next REAL` is in SCHEMA and MIGRATIONS
   (`+ players.ep_next` in the dry-run log); `ep_next()` gives None for None
   or "" (M5 red); the export carries it (M17 red); `--record --source fpl_ep`
   records `round(float(ep_next), 3)` for every player with one, next
   gameweek, same deadline guard; absent or all-null -> `RECORD SKIP fpl_ep
   the export has no ep_next for any player`, exit 0 (CLI test), c29 WARN
   (M13 red); some null -> `RECORD OK fpl_ep n (k without ep_next)`; the four
   stay strict (`test_the_frozen_four_stay_strict`) and record identically
   with or without ep_next (test, and check 5 on real data); `ep_next` is not
   in `REQUIRED_ELEMENT`. In the dry run all 668 bootstrap elements had an
   ep_next (0 null, 313 equal to 0 as the API gave them, 1 negative recorded
   as given per odds storage point 3), and 668 = the SYNC STATS element
   count, so "every player FPL scores" holds.
2. Collector - holds. One request: `soccer_epl`, `regions=uk,eu`,
   `markets=h2h,totals`, `oddsFormat=decimal`. The stored file's gzip header
   is `1f 8b 08 00 00000000 02 ff`: flags 0 (no name), mtime 0, OS 255; it
   decompresses to a 225,471-byte JSON list of 21 events; opened `"xb"` (M2
   red). No odds table: 14 tables at the gate, `fpl.sqlite` 1,896,448 bytes in
   both `e8629f0` and `bf91cf5`; `fpl_odds.py` imports no sqlite3 (M9 red).
   `read_snapshot()` returns the fetch minute 2026-10-18 21:06 UTC and the
   events; `rows()` gives 2517 rows without lay prices, 2736 with. The ODDS OK
   line matches the file (21 events, 21 with totals, 2736 prices, 10,472
   bytes; credits used 8, remaining 492, this request 4). Dry-run guard: a dry
   run calls the API only with `FPL_ODDS_LIVE=true` (M7 red); the dry run of
   `bf91cf5` had it ticked. A non-zero exit or crash of `fpl_odds.py` is one
   `ODDS FAILED` line, not in `failed`, so the night stays green, commits, and
   opens no issue (test, M10 and M18 red). Check 30 WARNs below 60 credits
   (M4 red).
   Determinism, judged: `gz()` is deterministic per zlib build - the same
   body gives the same bytes within one build (the test asserts `raw ==
   O.gz(BODY)`; M15 red). Re-gzipping the stored body on this machine
   (CPython 3.14, Windows, `zlib 1.3.1.zlib-ng`) gives 10,477 bytes, not the
   runner's 10,472, confirming the measured caveat. Nothing depends on
   cross-platform byte identity: the gate compares the working file with the
   committed blob byte for byte without re-compressing (a file rewritten
   with another compressor -> `GATE FAIL ... was rewritten`; deleted -> `GATE
   FAIL ... was deleted`; restored -> `GATE OK`), and every reader
   decompresses. The ruling's "deterministic" is met in the sense it serves
   (an append-only, reproducible archive on the one build that writes it).
3. Key - holds (check 7).
4. Gate - holds: `check_odds()` lists `HEAD:odds/` and requires each file
   present and byte-identical; a new file passes (the dry-run content against
   `e8629f0` -> `GATE OK`). Check 24 names files over 50 MB (M12 red); the
   scan walks the data folder minus `.git`.
5. Tests - holds (check 2). Mutations: my own 18 above.
6. Recording path - holds (check 5), with `7efc2b2` standing in for
   `1af9644` (same code).
7. Dry run `bf91cf5` - every line holds in the committed log and status:
   `Ran 495 tests ... OK (skipped=11)`, `+ players.ep_next`, the ODDS OK line
   above, five RECORD OK, `STATUS OK ... checks 28/28`, `30 OK odds snapshot`,
   `23 OK ... 7 file(s) to commit`. The gate re-run by me on `bf91cf5`'s
   content staged in a worktree at `e8629f0`: `GATE OK integrity ok, 14
   tables, price_history 25882 rows, frozen forecasts unchanged`, and the
   `fpl.sql` it wrote is byte-identical to `bf91cf5`'s.

## Observations (information, no verdict weight)

- A local `python fpl_odds.py` with `ODDS_API_KEY` in the environment and no
  `GITHUB_REF` is a real run for `fpl_publish.run_mode` and would call the
  API (4 credits). The standing rule already keeps the pipeline on the runner.
- If the credits headers were absent, the ODDS OK line would read
  `remaining None` and check 30 would be OK without a credits figure.
- The stored answer lists a few bookmakers outside uk/eu keys (for example
  `betonlineag`, `mybookieag`); the request carries `regions=uk,eu` as
  pre-registered, so that is the API's grouping, not the collector's.
- The prereg's "about 60" credits a night is recorded as a miscount in the
  decisions ruling; the measured use is 4 a request.

## Write guard

`git status` in `C:\GIT\FPL` shows only this file, untracked;
`C:\GIT\FPL-data` and `C:\GIT\FPL-b` were only read. All scratch work is
under the session scratchpad.

VERDICT: PASS

Reason: the prereg and both rulings were committed before the code they
govern and are verbatim on master; the only forecast the item adds (fpl_ep)
rebuilds exactly from the dated export of the same night and is recorded
before the GW8 deadline; the four frozen sources record byte-identically
(except the clock) between the master code and W1 on the same export and
match the dry run's rows, and the export differs only by `ep_next`; the suite
goes 459 -> 495 green bare, with stand-in zones and hermetically, and all 18
mutations go red; no file the item adds or changes holds a key, a URL with
`apiKey=` or an authorization value, the scans read inside gzip, and the key
reaches exactly the two workflow steps; the dry run's claims reproduce from
its committed blobs, including `GATE OK` with an identical `fpl.sql`. The
gzip caveat (zlib-ng here gives different bytes from the runner's) is real but
nothing in the gate or the readers depends on cross-build byte identity.
