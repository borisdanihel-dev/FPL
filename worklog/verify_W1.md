# Verifier (final): W1, fpl_ep and the Odds API collector, after the merge and the real dispatch

Final verifier required by RULING morning 19 Oct, point 1 ("... merge W1 now,
ask Boris for the real dispatch; final verifier after it"). Written 2026-10-19,
about 06:50 UTC, by the backtest-verifier agent. Model: Fable 5.1
(claude-fable-5-1); effort: high, as `.claude/agents/backtest-verifier.md`
says (read from disk first; it matched the loaded instructions). Checks applied
in their data-pipeline form (the prereg has no pass/fail metric): 1, 2, 5, 6, 7
plus the item's own acceptance tests; 3 and 4 are n/a as in the pre-check,
except check 4's "ruling present verbatim" part, decided below. The earlier
verdicts (`verify_W1_pre.md` PASS on d928ebe, `verify_W1_recheck.md` PASS on
d928ebe..ab047c3) were read for context only; nothing below relies on them.

Nothing was pushed, fetched into or changed in `C:\GIT\FPL`, `C:\GIT\FPL-data`
or `C:\GIT\FPL-b`; no tag, hook or config was touched; no workflow was
dispatched; neither the Odds API nor the FPL API was called; the real key was
never read (`ODDS_API_KEY` is not set in this shell; the one fake key was built
at run time: `k454...`). GitHub was read with `git ls-remote` and two
unauthenticated reads of the public Actions API (the run and its jobs). All
scratch work is under the session scratchpad: a clone of `C:\GIT\FPL` with
`refs/remotes/origin/data` (bd724ca) and `origin/data-dryrun` (24881f1) copied
from `C:\GIT\FPL` by `git fetch <local path>` into the clone, worktrees at
`5b38b41` (pre-W1), `3779acf` (the dispatched commit), `086a237` (master),
`0665283` (s16-wip) and data `9da6ff1`, and the three data trees extracted
blob by blob with `git cat-file --batch` (no line-ending conversion).

## What was verified against

- GitHub (`git ls-remote`, 06:25 UTC): master `086a237`, data `bd724ca`,
  data-dryrun `24881f1`, w1-wip `ab047c3`, s16-wip `0665283`, tag `pre-W1`
  `a7f91b2` -> `5b38b41`. `C:\GIT\FPL`'s local refs agree. `C:\GIT\FPL-data`
  is at `9da6ff1`, clean, only read.
- Actions run 39208578261: `workflow_dispatch` by borisdanihel-dev on
  `master`, head_sha `3779acf...`, created 06:12:27Z, completed 06:13:19Z,
  conclusion success, runner ubuntu-24.04; steps "Is this run due",
  "Install requirements", "Nightly run" (06:12:37-06:13:13), "Commit outputs
  to the data branch" (06:13:13-06:13:15), "Weekly backup" and "Failure
  issue" all success. The API does not expose the dispatch inputs; that the
  run was real (dry_run unticked) follows from its commit landing on `data`
  (`bd724ca`, "nightly 2026-10-19 [skip ci]", 06:13:13Z, parent `9da6ff1`)
  and its status file being `reports/status.txt`, not `status_dryrun.txt`.

## Prereg and commit order: PASS

`prereg/W1.md` on master holds, verbatim: RULING FAST-TRACK item 3, BUILD_PLAN
Step 4 item 2, Step 5 item 1's collector parts, RULING S1 amendment 1 item 1,
"Decisions" (RULING W1 decisions 1-5), "Odds storage" (1-4), "Pre-check
decisions" (1-3) and "Morning ruling, 19 Oct" (RULING morning 19 Oct, points
1-7, the "Order today" line, END RULING). The point 1 text matches the task's
quotation word for word. Commit order (+02:00 clock): prereg `7efc2b2`
2026-10-18 21:09:20 precedes the first W1 code commit `fec087a` 21:34:52;
`91b10c7` 22:14:26 precedes `a5b63bd`; `249be76` 22:41:54 precedes `d928ebe`;
`23c1e1e` 23:39:45 precedes `ab047c3`; the morning ruling `3779acf`
2026-10-19 08:02:46 (06:02:46Z) was committed after the merge, as the ruling
itself provides, and before the dispatch (06:12:27Z) that tests it.

## The merge, tested (claim 1): holds

- `pre-W1` is an annotated tag (`a7f91b2`, "master before the W1 merge
  (RULING morning 19 Oct, point 1)") on `5b38b41`, on GitHub too.
- `20309df` has parents `5b38b41` and `ab047c3`; its merge base with w1-wip
  is `19690cc`. The files w1-wip changed since `19690cc` are exactly the
  eleven named (nightly.yml, checks.py, fpl_edge.py, fpl_gate.py,
  fpl_nightly.py, fpl_odds.py, fpl_sync.py, test_fpl.py, tests/test_S3.py,
  tests/test_W1.py, prereg/W1.md); `git diff --name-only 5b38b41 20309df` is
  that same list, and `git diff ab047c3 20309df -- <those files>` is empty:
  every one is blob-identical to `ab047c3`.
- `3779acf` changes only `prereg/W1.md` (+15 lines, the morning ruling).
- S16's landing (`f2820e3`, `086a237`) changes CHANGELOG.md,
  tests/test_S16.py, tools/calendar_2627.py and two worklog files;
  `git diff 3779acf 086a237 -- <the eleven W1 files>` is empty.
- The commits before the merge on master are as listed (`0674e0f`,
  `e938788`, `5b38b41`).

## Check 1 - point-in-time: PASS

fpl_ep is the item's only forecast; the odds file is an input store. One
gameweek (GW8) has been recorded on `data`, so the three-gameweek truncation
collapses to one.

- 1a Truncation (decides): `bd724ca`'s `projection_log.csv` holds 668 `fpl_ep`
  rows (event 8, made_at 2026-10-19T06:13:11+00:00; `9da6ff1` held none).
  Rebuilt from the dated export of the same commit,
  `exports/fpl_export_gw7_2026-10-19.json.gz` (`generated`
  2026-10-19T06:13:10+00:00, 668 players, 668 with an `ep_next`) as
  `(id, web_name, round(float(ep_next), 3))`: the same key set, max
  |difference| 0.0, and the `predicted` strings equal as sets. PASS.
- 1b Timestamps (decides): run started 06:12:37Z, bootstrap fetched
  06:12:56Z, export generated 06:13:10Z <= every added row's made_at
  06:13:11Z <= GW8 deadline 2026-10-23T17:30:00Z (`events.deadline_time` in
  `bd724ca`'s `fpl.sqlite`; the log says "4 days, 11:16:48 before
  deadline"). All 1745 added rows are event 8 and made 2026-10-19T06. The
  odds file is named for its fetch minute (06:13Z, between the sync at
  06:12:56 and the record at 06:13:11); every event in it commences between
  2026-10-19T19:00Z and 2026-11-02T20:00Z, after the fetch. PASS.
- 1c Shift probe: n/a, no correlation metric in the item.

## Check 2 - clean-checkout test runs: PASS

Scratch worktrees, `ODDS_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN` removed,
`FPL_DATA_DIR` = a scratch copy of `bd724ca` after `fpl_nightly.py --restore`
(RESTORE OK, 5 exports). Python 3.14.7, Windows.
`python -m unittest discover -v -p "test*.py" -s . -t .`:

| checkout | result |
|---|---|
| `5b38b41` pre-W1 (before) | **459 OK**, skipped=2, exit 0 |
| `3779acf` the dispatched master (after) | **499 OK**, skipped=2, exit 0 (40 in tests.test_W1, 73 in tests.test_S3) |
| `086a237` master now, with S16 | **511 OK**, skipped=2, exit 0 |
| the dispatch itself, ubuntu-24.04, from `logs/run_2026-10-19.log` | `Ran 499 tests ... OK (skipped=11)`, `TESTS OK` |
| the S16 landing dry run `24881f1` (context) | `Ran 511 tests ... OK (skipped=11)` |

459 -> 499 as claimed; no FAIL or ERROR line in any run.

## Check 3 - re-run of the pre-registered evaluation: n/a

No metric in the prereg. Reproduced instead: the five RECORD OK counts
(own 285, xg 264, minutes 264, bottomup 264, fpl_ep 668) by running `--record`
myself on the same export (check 5), and the odds line's figures from the
stored file (below).

## Check 4 - metric, filter, bootstrap, threshold: n/a; rulings present: PASS

All n/a in the prereg (a data-collection item); nothing was promoted or
re-tuned after results. All five rulings the task names are in `prereg/W1.md`
verbatim.

## Check 5 - recording path: PASS (byte-identical, clock aside)

Two scratch copies of the restored `bd724ca` data, `fpl_edge.py --record
--source <s> --status reports/record_status.tmp` for own, xg, minutes,
bottomup with the `5b38b41` code and for all five sources with the `3779acf`
code (the nightly's exact invocation), then `--watch watchlist.txt --out` and
`--diff --out` with each:

- status lines identical for the four frozen sources (`RECORD OK own 285 /
  xg 264 / minutes 264 / bottomup 264`), plus `RECORD OK fpl_ep 668`;
- the two resulting `projection_log.csv` (7501 rows each) and `bd724ca`'s are
  identical as ordered lists once made_at of today's rows is masked (the
  same-UTC-day replacement rewrote them at 06:36 instead of 06:13); the four
  frozen sources' rows are identical between the two codes; every row older
  than today is identical unmasked in all three;
- the watch file (6,273 bytes) and the report (30,070 bytes) are byte-identical
  between the two codes; against the committed files, the watch file differs
  only in its header's "forecasts recorded" minute, and the report only by the
  two status lines checks.py prepends after the build.

## The dispatch, tested (claim 2): holds

- Log block (`logs/run_2026-10-19.log`, 1515 lines, started 06:12:37 UTC):
  `Ran 499 tests`, `TESTS OK`, `+ players.ep_next` (the first migration on
  `data`: `players.ep_next` is absent in `9da6ff1`, present in `bd724ca` with
  668 of 668 filled, 313 zero, 1 negative, min -0.3, max 10.5), `ODDS OK
  21 events (21 with totals), 2776 prices,
  odds/odds_2026-10-19T0613Z.json.gz 10383 bytes; credits used 12, remaining
  488, this request 4`, five `RECORD OK` (fpl_ep 668), `ARCHIVE OK`,
  `STATUS OK ... checks 28/28`, `CHECKS OK -> reports/status.txt`. SYNC STATS:
  `elements 668`, 25 calls, `ep_next` among the element keys; 668 = the
  fpl_ep count, so "every player FPL scores" holds. `run_2026-10-18.log` is
  byte-identical between the two commits.
- `reports/status.txt`: `STATUS OK | generated 2026-10-19T06:13:12Z | checks
  28/28`; `30 OK odds snapshot: ...` (the line above); `29 OK record: own 285,
  xg 264, minutes 264, bottomup 264, fpl_ep 668`; `18 OK projection-log
  growth: new rows bottomup +264, fpl_ep +668, minutes +264, own +285, xg
  +264`; `22 SKIP manager score reconciliation: GW7 not locked down` (events
  7 has data_checked 0, 0 of 10 GW7 fixtures finished); `16 OK 25882 -> 26550
  rows (+668)`; `19 OK 0 duplicate keys`; `20 OK 0 of 7501 rows at or after
  their deadline`; `23 OK 7 file(s) to commit`.
- Projection log: `9da6ff1`'s 294,539 bytes are an exact byte prefix of
  `bd724ca`'s 383,848; 5756 -> 7501 rows, the 1745 added are own 285, xg 264,
  minutes 264, bottomup 264, fpl_ep 668, all event 8, all made
  2026-10-19T06; 0 duplicate `(source, event, player_id, day)` keys.
- `fpl.sqlite`: 1,896,448 -> 1,945,600 bytes, integrity ok, 14 tables in both
  (no odds table); price_history 25882 -> 26550 (+668), the new rows on
  london_date 2026-10-19 (the log's PRICE DATE FLAG names it).
- The gate re-run by me with the `3779acf` code on `bd724ca`'s content
  (every blob) copied over a worktree at `9da6ff1`: `GATE OK integrity ok, 14
  tables, price_history 26550 rows, frozen forecasts unchanged; fpl.sql
  written`, and that `fpl.sql` (2,611,794 bytes) is byte-identical to
  `bd724ca`'s. The same 9 paths git lists as changed are the commit's. Then,
  with the odds file committed as HEAD: one byte appended -> `GATE FAIL
  odds/odds_2026-10-19T0613Z.json.gz was rewritten`; deleted -> `GATE FAIL
  ... was deleted`.
- The odds file: gzip header `1f 8b 08 00 00000000 02 ff` (flags 0: no name;
  mtime 0; OS 255), 10,383 bytes, decompressing to a 228,702-byte JSON list of
  21 events, 21 with a totals market, 2776 outcome prices (222 of them
  `h2h_lay`), 42 bookmakers, markets h2h / h2h_lay / totals, 21 unique
  32-hex event ids, no `apikey`/`api_key` in the body. Re-gzipping the body
  here (zlib-ng) gives 10,394 bytes, the known cross-build caveat; nothing in
  the gate or the readers depends on it (the gate compares bytes without
  recompressing, shown above).
- The ARCHIVE line and the dated export: `exports/fpl_export_gw7_2026-10-19.json.gz`
  (127,499 bytes) is new in `bd724ca`; the 17 and 18 Oct ones are untouched.

## Check 6 - mutation spot-check: PASS (3 of 3 red)

Each in a fresh scratch copy of `3779acf`, `python -m unittest tests.test_W1`
(40 tests) with no key:

| # | mutation | red test(s) |
|---|---|---|
| F1 | fpl_edge: fpl_ep records `round(float(ep_next) * 2, 3)` | `FplEp.test_fpl_ep_records_ep_next_for_the_next_gameweek` |
| F2 | fpl_gate `check_odds`: the byte comparison disabled (`if False:`) | `OddsAppendOnly.test_a_rewritten_odds_file_fails_the_gate` |
| F3 | fpl_odds: the `GITHUB_ACTIONS != "true"` guard removed | `OddsCollector.test_the_api_is_called_only_in_github_actions` (7 subtests), `test_the_command_line_reads_github_actions_from_its_environment` |

The pre-check's 18 and the re-check's 8 mutations are on record in the earlier
reports; F1-F3 are mine.

## Check 7 - secrets: PASS

- The eleven files the item adds or changes, at `3779acf`, searched for
  `apiKey=`/`api_key=` followed by a value, `Authorization:`, `Bearer ` and
  32+ hex characters: the only hits are `checks.py:709` (the GitHub token
  header built from a variable, pre-existing, no value), `fpl_gate.py:25`
  (the pattern named in a docstring), the action SHAs pinned in nightly.yml
  and `tests/test_S3.py:960-961`, the git SHA in `test_fpl.py:4498`, and
  `tests/test_W1.py` building fake keys at run time (`fake_key()`,
  `secrets.token_hex`). No key, no URL with `apiKey=`, no header value.
- nightly.yml at `3779acf`: `secrets.ODDS_API_KEY` exactly twice ("Nightly
  run", "Commit outputs to the data branch"); `FPL_ODDS_LIVE: ${{
  inputs.odds_live }}` on the nightly step; the test step inside
  `fpl_nightly.py` drops `ODDS_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN`.
- The dispatch's new or changed text files (run log, status, report, watch
  file, projection log, fpl.sql): 0 lines matching `apikey=`, `api_key=`,
  `authorization` or `bearer `; no 32+ hex string in the log, status, report
  or watch file; no key pattern inside the gzipped export or the odds body.
- `fpl_gate.py --secrets` on `bd724ca`'s 9 staged paths with a fake key in
  the environment: `SECRETS OK` (exit 0); a gzip holding the fake key planted
  in `odds/` and staged: `SECRET FAIL odds/... - commit nothing` (exit 1),
  naming the file only.

## Context (claim 3): the S16 landing dry run

`24881f1` ("dry run 2026-10-19 s16-wip 0665283 [skip ci]", 06:17:45Z, parent
`bd724ca`): `Ran 511 tests ... OK (skipped=11)`, `TESTS OK`, `ODDS SKIPPED
(dry run): odds_live not ticked - no Odds API call`, five RECORD OK (fpl_ep
668), `STATUS WARN ... checks 27/28` with the only WARN `30 WARN odds
snapshot: ODDS SKIPPED (dry run)...`, 22 and 27 SKIP, `28 OK test gate: 511
tests green`. It holds the one odds file of `bd724ca` unchanged (same blob
`8dcce6e`). S16 has its own verifier; no verdict weight here.

## Observations (information, no verdict weight)

- The dry run re-synced 4 minutes after the real run and rewrote the same-day
  dated export `exports/fpl_export_gw7_2026-10-19.json.gz` (same size,
  different bytes) and the day's forecast rows on `data-dryrun` only. That is
  the pre-existing per-day archive rule, not W1's; `data` is untouched by it.
- `c30` reads the last ODDS line of the day's run log; tonight's 21:40
  nightly will append a second block to `run_2026-10-19.log` and write a
  second odds file (`odds_2026-10-19T21..Z`), which the append-only gate
  allows (a new name).
- `count(distinct london_date)` in price_history is 1 at `9da6ff1` and 2 at
  `bd724ca`: the column is filled only for the newest rows (older rows null),
  pre-existing.

## Write guard

`git status` in `C:\GIT\FPL` shows the two untracked files that were there at
launch (`worklog/verify_S2b_pre.md`, `worklog/verify_W1b_pre.md`) and this
file; `refs/heads/master`, `origin/data`, `origin/data-dryrun` and `pre-W1`
are unchanged. `C:\GIT\FPL-data` (`9da6ff1`, clean) and `C:\GIT\FPL-b` were
not touched. All scratch work is under the session scratchpad.

VERDICT: PASS

Reason: the merge is what was claimed - an annotated `pre-W1` on `5b38b41`,
`20309df` carrying the eleven w1-wip files blob-identical to `ab047c3`,
`3779acf` adding only the morning ruling to `prereg/W1.md` (verbatim, with the
four earlier rulings), and S16's landing touching no W1 file; the real
dispatch (run 39208578261, workflow_dispatch on `3779acf`, success) committed
`bd724ca` on `9da6ff1` whose log, status, projection log, database and odds
file match every claim and reproduce from the blobs (GATE OK with a
byte-identical `fpl.sql`, SECRETS OK, the rewrite and delete of the odds file
both refused); the only forecast the item adds, fpl_ep, rebuilds exactly (max
difference 0.0) from the dated export of the same commit and every added row
was made at 06:13:11Z, before the GW8 deadline; the four frozen sources, the
watch file and the report regenerate byte-identically (clock aside) with the
pre-W1 and the merged code on the same export and equal the committed rows;
the suite is green at 459 (pre-W1), 499 (dispatched) and 511 (master with
S16) locally and 499 on the runner; three mutations go red; and no file the
item adds or changes, nor any output of the dispatch, holds a key, a URL with
`apiKey=` or an authorization value.
