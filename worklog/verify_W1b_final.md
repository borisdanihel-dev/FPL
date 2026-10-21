# W1b - final verifier report (the first real run on the merged master)

- **Verifier:** backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high.
  `.claude/agents/backtest-verifier.md` read from disk first; it matches the loaded
  instructions. Date: 2026-10-21 (about 14:30-14:50 UTC).
- **Item:** W1b, runner work, merged into master at f367cbd (tag `pre-W1b` = 87485f3; the
  merge brings w1b-wip dd10f24 - `git diff dd10f24 f367cbd` is empty, so the merged tree is
  the tested tree). This is the final verifier the ruling of Wednesday 21 Oct, point 1,
  orders on Boris's real run. Descriptive/pipeline item: no metric, no forecast model, no
  feature; agent-file checks 1 and 3 are n/a (no feature or metric was produced; the
  recording path is checked below under check 3).
- **Not done, by instruction:** nothing dispatched, nothing pushed, nothing committed, no FPL
  or Odds API call. GitHub's public Actions API was read without any token (two calls,
  then one listing; a fourth call hit the unauthenticated rate limit and was not retried).
  The data worktree got `git -C C:\GIT\FPL-data pull --ff-only` only ("Already up to date").
  Scratch under `scratchpad/v1b_final/` only; this file is the only write in the w1b
  worktree (`git status --short` there before: clean at dd10f24).
- `ODDS_API_KEY` is unset in the verifier's shell; no key-like string appears below.

## Prereg and rulings

`prereg/W1b.md`: first commit 7aa568f (2026-10-19 02:08:40 +0200), before the first code
commit a9248d1 (02:35:16 +0200). It holds, verbatim: RULING W1b (points 1-7), the morning
ruling of 19 Oct (point 4: manual dry runs gated too, the 21:30 window closes at 04:00, a
missing deadline row WARNs), RULINGS PART F item F-A (cap 12), the ruling of Tue 20 Oct
(point 1: merge Wednesday) and the Wednesday 21 Oct text (point 1: tonight's one runner
change, the real run, the final verifier, the revert-to-pre-W1b clause). PASS.

## The run (public API, no auth)

Run 39615734849, workflow `nightly` (`.github/workflows/nightly.yml`), `event =
workflow_dispatch`, `head_branch = master`, `head_sha = 1594e5d`, `run_attempt 1`,
`display_title = nightly` (the `run-name` expression gives "dry run <ref>" for a dry run and
"nightly" otherwise, so the name itself says this was not a dry run), started
2026-10-21T14:18:27Z. One job, `nightly`, `completed / success`, 14:18:31Z-14:21:04Z. Steps:

| # | step | conclusion | time (UTC) |
|---|---|---|---|
| 1 | Set up job | success | 14:18:32-33 |
| 2 | actions/checkout (master) | success | 14:18:33-34 |
| 3 | actions/checkout (data -> ./data) | success | 14:18:34-36 |
| 4 | actions/setup-python | success | 14:18:36 |
| 5 | Is this run due | success | 14:18:36-37 |
| 6 | Install requirements | success | 14:18:37-39 |
| 7 | Nightly run | success | 14:18:39-14:20:58 |
| 8 | Commit outputs to the data branch | success | 14:20:58-14:21:01 |
| 9 | Weekly backup | success | 14:21:01 |
| 10 | Failure issue | success | 14:21:01 |
| 18-21 | Post steps, Complete job | success | 14:21:01-02 |

Note: at my first read (about 14:30 UTC, minutes after the job ended) the run-level record
still said `status = in_progress, conclusion = null, updated_at 14:26:27Z` while its only
job was `completed / success`; the later re-poll hit the rate limit. The job record, the
step list and the data commit below are the evidence; the run-level flag was read while
GitHub was still finalising the run and is not load-bearing.

## Check 1 - the real run behaved as a real run: PASS

Evidence from `reports/status.txt` and `logs/run_2026-10-21.log` at data commit 7dbc319
(read with `git show`, parsed in scratch):

- The commit: 7dbc319 "nightly 2026-10-21 [skip ci]", parent 3c1071f (last night's nightly),
  committer github-actions[bot], 2026-10-21T14:20:58Z, contained in `origin/data` only;
  `origin/data-dryrun` is unchanged at 516326d (the W1b dry run #40 of 20 Oct). 9 files:
  `exports/fpl_export_gw7_2026-10-21.json.gz` (new), `fpl.sql`, `fpl.sqlite`,
  `logs/run_2026-10-21.log` (new), `odds/odds_2026-10-21T1420Z.json.gz` (new),
  `projection_log.csv`, `reports/fpl_2026-10-21.txt` (new), `reports/status.txt`,
  `reports/watch_2026-10-21.txt` (new).
- `STATUS OK | generated 2026-10-21T14:20:58Z | next deadline GW8 2026-10-23 17:30 UTC /
  2026-10-23 19:30 Prague | checks 29/29 | repo 8 MB`; checks 1-30 OK except 27 SKIP
  (manual, as always).
- The test gate ran the merged suite: log line 1312 `Ran 739 tests in 127.310s`, line 1314
  `OK (skipped=12)`, line 1315 `TESTS OK`; check 28 `test gate: 739 tests green`. Last
  night's run (3c1071f, master cd9e8bc, pre-W1b) had `test gate: 708 tests green`: 708
  before W1b on the runner, 739 after (W1b's 31 tests in `tests/test_W1b.py`).
- The record path ran: `RECORD OK own 276`, `xg 256`, `minutes 256`, `bottomup 256`,
  `fpl_ep 668` (log lines 1336-1352 and the summary 1868-1872), each "recorded N forecasts
  for GW8 ... (2 days, 3:09:0x before deadline)"; check 29 the same five counts; check 18
  `new rows bottomup +256, fpl_ep +668, minutes +256, own +276, xg +256`.
- The odds call happened: `ODDS OK 20 events (20 with totals), 3127 prices,
  odds/odds_2026-10-21T1420Z.json.gz 11731 bytes; credits used 28, remaining 472, this
  request 4` (log line 1331; check 30). Last night: credits used 24, remaining 476 - this
  run spent its 4 credits, which a dry run cannot (the key is not passed on a push, and
  `FPL_ODDS_LIVE` is empty).
- Check 23 `secret in the files to commit: 7 file(s) to commit, none holds a key pattern or
  the key value` OK. (7, not 9: `changed_files` reads `git status` at check time, before
  `status.txt` is written and before the publish step dumps `fpl.sql`; last night's commit
  3c1071f also has 9 files against a "7 file(s)" check 23, so this is the standing
  behaviour, not W1b's. The publish step's own staged-file scan covers the commit.)
- The sync ran (17 FPL calls, all 200; `fpl_export_gw7.json` exported, archived as the dated
  gz); the watch file and the report were written; the backup step ran its skip branch
  (Wednesday, no `force_backup`); the failure issue step ran (success, i.e. the issue path of
  a green real run), both of which a dry run skips.

## Check 2 - the W1b gate did not touch the real run: PASS

- Step 5 "Is this run due" succeeded in 1 s (14:18:36-37) and every later step ran, so the
  gate wrote `run=true`.
- The log (1909 lines) has no `DRY RUN` line, no `SKIPPED`, no `data-dryrun` outside the test
  names in the suite block (lines 1-1315); the non-test part (lines 1316-1909) matches the
  shape of last night's real run (sync, odds, record x5, watch, report, stuck check,
  archive, checks).
- `fpl_publish.run_mode` at f367cbd (identical on origin/master): ref master and not a
  schedule -> `FPL_DRY_RUN` decides. Run on the clean checkout with the run's environment
  (`GITHUB_REF=refs/heads/master`, `GITHUB_EVENT_NAME=workflow_dispatch`,
  `FPL_DRY_RUN=false`): `('real', 'dry_run is not ticked')`. Controls: ticked ->
  `('dry', 'dry_run is ticked')`; a push to `dry/W2` -> `('dry', 'ref refs/heads/dry/W2 is
  not refs/heads/master')`; a schedule on master -> `('real', 'scheduled run')`.
- `fpl_nightly.due_main` at f367cbd calls `fpl_dryrun.gate` only when `due and
  run_mode(env)[0] == "dry"`. Run with the same environment, `FPL_SCHEDULE=""`, a scratch
  data folder holding the run's `status.txt` and `fpl.sqlite`, `fpl_dryrun.gate` replaced
  by a sentinel, now = 14:18:36Z: it printed `DUE          not the backup cron`, the
  sentinel was never called, `GITHUB_OUTPUT` got `run=true`, rc 0; `fpl_dryrun._GET` is
  `None` (no network path reachable). The workflow's `FPL_DRY_RUN` expression is `false` for
  a master dispatch with `dry_run` unticked, its concurrency expression `nightly-data`, and
  `ODDS_API_KEY` is passed for every non-push event (workflow text at f367cbd; the API does
  not expose the group, the credits spent above show the key was passed).

## Check 3 - the recording path: PASS

`projection_log.csv` at 3c1071f (470,767 bytes, 9,200 rows after the header) is a byte-prefix
of the file at 7dbc319 (558,366 bytes): 0 rows removed or changed. The 1,712 appended rows
(header `made_at,source,event,player_id,web_name,predicted`): all `event = 8`; by source
own 276, xg 256, minutes 256, bottomup 256, fpl_ep 668 - equal to the five RECORD OK lines,
check 29 and check 18; `made_at` is `2026-10-21T14:20:56+00:00` or `...14:20:57+00:00`
(today, during step 7), every one before the GW8 deadline `2026-10-23T17:30:00Z` read from
`events` in the committed `fpl.sqlite`; check 20 `0 of 10912 rows at or after their deadline`
(9,200 + 1,712 = 10,912). Check 19: 0 duplicate keys.

## Check 4 - nothing else on master changed the runner since the tested tree: PASS

`git diff dd10f24 origin/master -- '*.py' .github 'requirements*'` is empty. Master since
f367cbd: 1594e5d (`worklog/SESSION_STATE_A.md` only) and df287ca (`prereg/S16.md` only, +191);
origin/master = local HEAD = df287ca; the run's head 1594e5d is between them and has the
same runner files. `git diff dd10f24 f367cbd` is empty.

## Check 5 - clean-checkout suite of origin/master: PASS

`git archive origin/master` (df287ca) into `scratchpad/v1b_final/clean/`; `python -m unittest
discover -p "test*.py" -s . -t .` from inside, with `ODDS_API_KEY`, `FPL_DATA_DIR`,
`FPL_ODDS_LIVE`, `GITHUB_TOKEN` unset (`env -u`); Python 3.14, Windows:
`Ran 739 tests in 329.690s`, `OK (skipped=10)`, exit 0. The same 739 the runner's gate ran
on Linux (`OK (skipped=12)`: the two `fpl_run.bat` tests skip there too, plus two
platform skips). Before W1b on master: 708 (last night's gate at cd9e8bc); the earlier
verifier reports have the branch at 738 -> 739 (a81e2b1 -> 596de21). No later commit added
tests.

## Check 6 - secrets: PASS

- The run's check 23 OK (above); the publish step's staged scan precedes the commit.
- My own scan of all 9 committed files (the two `.gz` decompressed, `fpl.sqlite` as bytes,
  `fpl.sql` as text) for `apiKey=`, `api_key=`, `token=`, `Authorization`, `Bearer <x>` and
  any hex run of 32+ characters: no hit in 8 files. The odds file has 20 hex runs of exactly
  32 characters: they are the Odds API's event `"id"` values (context `[{"id":"d020...`),
  one per event (20 events); the decoded JSON holds no `apikey` and no `http` string at all.
  No `.git`-SHA-like 40-hex and no 64-hex anywhere in the 9 files.
- `logs/run_2026-10-21.log`: the ODDS line names the file, the count and the credits only.
- `ODDS_API_KEY` was unset in this shell (the value could not have been matched by me; the
  run's own check 23 and the publish scan match the value on the runner where it is set).

## Mutation spot-check (agent-file check 6): PASS

Fresh `git archive` of origin/master into `scratchpad/v1b_final/mut/`; one line of
`fpl_publish.run_mode` changed, `if ref and ref != MASTER:` -> `if ref and ref != MASTER and
False:` (every ref treated as master, so a push to `dry/<item>` could become real).
`python -m unittest tests.test_W1b`: `Ran 31 tests`, `FAILED (failures=8)`, e.g. the
end-to-end publish test asserting "the result goes to data-dryrun-S16 only, never to data"
got `PUSH OK      origin data` instead. Green copy: 31 OK (within the 739 above). The
earlier reports (`verify_W1b.md`, `verify_W1b_fix.md`) hold the per-rule mutation table
(M1-M13 plus mb, mc) on the same code.

## Observations (no finding)

1. The run-level `status = in_progress` read minutes after the job completed (above); the
   job, its steps and the data commit are what count. A later look at the Actions tab will
   show it completed.
2. The W1b gate's cap and quiet windows were, by design, never exercised by this run (a real
   run does not reach them). Their first live exercise will be the `dry/W2` push the
   Wednesday ruling's point 2 schedules; this report makes no claim about that path beyond
   the unit and end-to-end tests already verified.

## VERDICT: PASS

Boris's real dispatch 39615734849 on master 1594e5d (W1b merged at f367cbd, tree identical
to the tested dd10f24; no runner file changed since) ran as a real run: every step green,
the merged suite's 739 tests in the gate (708 the night before), 17 FPL calls, the Odds API
called (4 credits, 28 used / 472 left), five RECORD OK lines, checks 29/29 OK with check 23's
secret scan OK, and the result committed by github-actions[bot] to `data` as 7dbc319 (not
to `data-dryrun`, unchanged at 516326d). The W1b gate stayed out of it: "Is this run due"
passed in 1 s, the log has no DRY RUN or SKIPPED line, and `run_mode`/`due_main` at the
merged commit, run with the dispatch's environment, give `real` and `run=true` without
touching `fpl_dryrun.gate`. The projection log at 7dbc319 is last night's file byte-for-byte
plus exactly the 1,712 recorded GW8 rows (own 276, xg 256, minutes 256, bottomup 256,
fpl_ep 668), all made at 14:20:56-57Z today, 2 days 3 h before the GW8 deadline, 0 duplicates.
A clean git-archive checkout of origin/master is 739 OK bare; a one-line mutation of
`run_mode` turns 8 W1b tests red; none of the 9 committed files holds an `apiKey=`,
`Authorization`, `Bearer` or key-like string (the only 32-hex runs are the Odds API's 20
event ids). The prereg with every ruling verbatim predates all W1b code.
