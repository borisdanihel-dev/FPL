# Verifier report: W1b (automatic dry runs), code-level run before the last manual dry run

- **Verifier:** backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high, as
  `.claude/agents/backtest-verifier.md` on disk says (the file on disk matched the loaded
  instructions; no Opus fallback was needed).
- **Date:** 19 Oct 2026 (UTC).
- **Item:** W1b, runner work, branch `w1b-wip` at `a9248d1` (code) on `4cb69c5` (docs merge)
  on `w1-wip` `ab047c3`. Prereg `prereg/W1b.md` at master `7aa568f`.
- **Where I ran:** scratch clones only, under the session scratchpad
  (`...\scratchpad\v\{before,after,base,redbefore,mut,dataA,dataB}`). No push, no fetch, no ref
  change, no workflow dispatch, no GitHub or Odds API call. `C:\GIT\FPL`, `C:\GIT\FPL-data`
  (at `9da6ff1`, read only, copied without `.git`) and `C:\GIT\FPL-b` were not touched;
  `git status` of the data worktree stayed empty throughout. GitHub was read once with
  `git ls-remote` (refs only: no `dry/*` branch exists; `w1b-wip` = `a9248d1`,
  `w1-wip` = `ab047c3`, `master` = `7aa568f`, `data` = `9da6ff1`, `data-dryrun` = `f7c5706`).

## Order and ruling

- Prereg `7aa568f` committed 2026-10-19 00:08:40 UTC; docs merge `4cb69c5` 00:10:10 UTC;
  code `a9248d1` 00:35:16 UTC. `git diff 7aa568f a9248d1 -- prereg/W1b.md` is empty (the
  prereg on the branch is byte-identical to master's). `git diff ab047c3 4cb69c5 --stat`
  touches only `prereg/*.md` and `worklog/SESSION_STATE_A.md`. **Order: PASS.**
- `prereg/W1b.md` holds a block headed `RULING W1b (automatic dry runs; answers the four
  parked questions):` ... `END RULING`, plus the three earlier clauses it answers. I cannot
  compare it with the chat (I never read transcripts); the ruling text is present and the
  acceptance tests 1-9 are stated. **Check 4 (ruling present, no metric to promote): PASS.**

## Checks

### 1. Point-in-time leak check: n/a
W1b produces no forecast, feature or metric. The gate reads only `events.deadline_time`
and the data checkout's last commit time, for a skip decision. Nothing to truncate.

### 2. Clean-checkout test run: PASS
`python -m unittest discover -p "test*.py"`, env without `FPL_DATA_DIR`, `GITHUB_ACTIONS`,
`GH_TOKEN`, `ODDS_API_KEY`:
- before (`4cb69c5`): **Ran 499, OK (skipped=9)**;
- after (`a9248d1`): **Ran 527, OK (skipped=9)**;
- after, runner-like push env (`GITHUB_EVENT_NAME=push GITHUB_REF=refs/heads/dry/W1b
  GITHUB_REF_NAME=dry/W1b GITHUB_ACTIONS=true`): **Ran 527, OK (skipped=9)**;
- `tests/test_W1b.py` alone: **28 tests, OK**; also OK under `TZ=EST5EDT`, `TZ=NZST-12NZDT`,
  `TZ=UTC0`, each with `HOME`/`USERPROFILE` on a temp folder, `GIT_CONFIG_GLOBAL=/dev/null`,
  `GIT_CONFIG_NOSYSTEM=1`, `LANG=C`; `tests.test_W1b tests.test_S3 test_fpl.NightlyWorkflow
  test_fpl.Publish` hermetically: 123 tests, OK (skipped=1).
- The implementer's "499 -> 526" is the count before the 28th test (the deadlines guard);
  527 is the count at `a9248d1`.

**Red before:** `4cb69c5` plus only `fpl_dryrun.py` and `tests/test_W1b.py`: **14 of 28 red**
(5 errors: the `ResultBranch` and two `Cap` tests that need `fpl_publish.result_branch`;
9 failures: the four `Trigger` workflow tests, the four `DueGate` tests, `PushRunPublishes`).
That is the implementer's 13 of 27 plus the later deadlines-guard test. Without
`fpl_dryrun.py` the module does not import at all.

### 3. Re-run of the pre-registered evaluation: n/a (no metric); the acceptance tests are
verified below, point by point.

### 5. Recording path: PASS
Frozen clock (`datetime.now` pinned to 2026-10-19 12:00:00 UTC by patching
`datetime.datetime`; `fpl_edge.py` reaches the clock only through `datetime.now(timezone.utc)`,
five sites, no `date.today()`/`time.time()`), after `fpl_nightly.py --restore` in each data
copy (both restored `fpl_export_gw7_2026-10-18.json.gz`, identical), `--record` for the five
nightly sources `own, xg, minutes, bottomup, fpl_ep`:
- `ab047c3` code in `dataA` and `a9248d1` code in `dataB`: `RECORD OK own 285`, `xg 264`,
  `minutes 264`, `bottomup 264`, `RECORD SKIP fpl_ep the export has no ep_next for any
  player` on both;
- `projection_log.csv`: **byte-identical** (6,833 rows, sha256 `fb07c20c404abe0f...` both);
  status files identical.
- Also structurally: `git diff ab047c3 a9248d1 -- fpl_edge.py fpl_sync.py checks.py
  fpl_odds.py fpl_gate.py fpl_alert.py fpl_prepush.py` is empty. The item touches no model
  or recording code.
- Note, unrelated to W1b: the real log on disk in the worktree is CRLF (checkout), the
  rewritten scratch log is LF; the real rows are all present in the scratch log, which adds
  exactly the 1,077 frozen 19 Oct rows. The real log was not written.

### 6. Mutation spot-check: PASS (29 of 29 red)
My own battery (`scratchpad\v\mutate_verify.py`, not the implementer's), each applied alone
to a scratch copy of `a9248d1`, running `tests.test_W1b test_fpl.NightlyWorkflow
tests.test_S3.FailureIssue`:

| mutation | red by |
|---|---|
| V1 yml push filter `dry/*` | Trigger.test_the_push_trigger_is_dry_only |
| V2 nightly step key `${{ secrets.ODDS_API_KEY }}` | Trigger.test_the_key_is_not_passed_to_a_push_run (+ test_fpl) |
| V29 commit step key `${{ secrets.ODDS_API_KEY }}` | same |
| V3 `actions: read` removed | Trigger.test_the_one_job_reads_actions... (+ test_S3) |
| V4 run-name without the push clause | Trigger.test_every_dry_run_is_named... |
| V5 due step without `GH_TOKEN` | Trigger.test_the_one_job_reads_actions... |
| V6 group always `nightly-data` | Trigger.test_a_push_waits_in_the_dry_group... |
| V7 `CAP = 7` | Cap (4 tests) |
| V8 `NIGHT_END` 03:18 | Windows.test_the_night |
| V9 `NIGHT_START` 21:31 | Windows.test_the_night |
| V10 `DEADLINE_GAP` 2 h | Windows.test_a_deadline |
| V11 a skipped "Nightly run" counts | Cap.test_counting |
| V12 this run counted | Cap.test_counting |
| V13 other days counted | Cap.test_counting |
| V14 untitled runs counted | Cap.test_counting |
| V15 page overflow ignored | Cap.test_when_it_cannot_count_it_skips |
| V16 windows disabled in `decide()` | Cap.test_a_quiet_window_skips_before_any_api_call (+ DueGate) |
| V17 cap `>` instead of `>=` | Cap (3 tests) |
| V18 no token still counts | Cap.test_no_token_means_no_count... |
| V19 no deadlines still runs | DueGate.test_without_the_deadlines_it_skips |
| V20 unknown tip not quiet | Windows.test_the_night |
| V21 `result_branch` always `data-dryrun` | 4 tests |
| V22 `push_dry` refusal removed | ResultBranch.test_push_dry_refuses... |
| V23 `dry_target` accepts `data-dryrun-` | ResultBranch.test_only_data_dryrun... |
| V24 `main()` ignores the target | PushRunPublishes.test_a_push_run_goes_to_its_own_branch |
| V25 due gate never called | DueGate (4 tests) |
| V26 due gate also for real runs | DueGate.test_real_runs_never_reach_the_gate |
| V27 `TITLE` without the trailing space | Trigger.test_every_dry_run_is_named... |
| V28 list query without `created` | Cap.test_counting |

### 7. Secrets: PASS
Over the nine files the item adds or changes: no key value, no `apiKey=` URL, no
`Authorization` header value. Hits are only: `fpl_dryrun.py:116` the template
`"Authorization": f"Bearer {token}"` (no value); `nightly.yml:24` the pre-existing comment
describing the scan; `BUILD_PLAN.md:200,274` the verifier and scan specifications;
`test_fpl.py:4501` a git SHA fixture; `tests/test_W1b.py` uses `GH_TOKEN="t-not-a-real-token"`.
A direct probe of `_getter`: the token goes only into the `Authorization: Bearer ...`
header (with `Accept`, `User-Agent`, `X-GitHub-Api-Version`, timeout 30); HTTP 403 ->
`CannotCount("HTTP 403")`, `URLError` -> `CannotCount("URLError")`, bad JSON ->
`CannotCount("JSONDecodeError")`; `decide()` on a 403 prints
`DRY RUN SKIPPED: cannot count today's dry runs (HTTP 403)` and the token is not in it.

## The acceptance tests of `prereg/W1b.md`, point by point

1. **Trigger.** `on:` holds `push: branches: ["dry/**"]` and nothing else under `push` (no
   `tags`, `paths`, `branches-ignore`); `schedule` (`40 21 * * *`, `17 3 * * *`) and
   `workflow_dispatch` (inputs `dry_run` true, `odds_live` false, `force_backup` false,
   all boolean) are unchanged. A push's `github.ref` is `refs/heads/dry/...`, never master,
   so `fpl_publish.run_mode` gives `dry` ("ref ... is not refs/heads/master"). PASS.
2. **Dry-run path.** `FPL_DRY_RUN` expression unchanged, true for any non-master ref. The
   backup step and the failure issue keep `env.FPL_DRY_RUN != 'true'`. Concurrency expression
   unchanged (`'nightly-dryrun'` for a non-master ref, `cancel-in-progress: false`). Both
   `ODDS_API_KEY` lines are `${{ github.event_name != 'push' && secrets.ODDS_API_KEY || '' }}`
   (`false && x` -> `false`, `false || ''` -> `''`), exactly two `secrets.` references in the
   non-comment text (test pins both). `FPL_ODDS_LIVE: ${{ inputs.odds_live }}` is empty on a
   push. Probe of `fpl_odds.main()` with `GITHUB_ACTIONS=true`, push env, empty key and
   `urlopen` replaced by an assertion: prints `ODDS SKIPPED (dry run): odds_live not ticked
   - no Odds API call`, exits 0, opens nothing (the dry-run check precedes the key check).
   "The key is not passed" is met at the only level that exists: no step env of a push run
   carries the value. The commit step's value check with an empty key: `fpl_gate.secret_hit`
   then tests only the patterns (`apikey=`, `api_key=`); the value check is moot since no
   process of that run ever had the value, and the files from `data` were scanned by the
   real runs that committed them. Immaterial. PASS.
3. **Results.** `result_branch`: `data-dryrun-S16` for push + `refs/heads/dry/S16`,
   `data-dryrun-S16-2` for `dry/S16-2`, `data-dryrun` for a dispatch on any ref, for
   `refs/heads/dry/` (empty item) and for a push to a non-dry ref. `dry_target` accepts only
   `data-dryrun` and `data-dryrun-<non-empty>`; `push_dry` refuses everything else before any
   git call (test records zero `_git` calls); `main()` passes the target through. The
   bare-remote test shows the result on `data-dryrun-S16`, `data` head unchanged, `data-dryrun`
   absent, commit message `dry run <date> dry/S16 0123456 [skip ci]`. `fpl_prepush.py` is
   unchanged between `ab047c3` and `a9248d1`; `check()` guards only `refs/heads/master` with a
   non-zero SHA, so `dry/*` pushes and `data-dryrun-*`/`dry/*` deletions pass (test). A
   force-push to `data-dryrun-<item>` cannot re-trigger the workflow (`data-dryrun-*` does
   not match `dry/**`). PASS.
4. **Cap.** `actions: read` on the one job, `permissions: {}` at workflow level; the due
   step gets `GH_TOKEN: ${{ github.token }}`. `count_dry_runs`: one list call
   `/repos/<repo>/actions/workflows/nightly.yml/runs?created=%3E%3D<today>&per_page=100`
   (the workflow file name is a valid `workflow_id`; `created` takes the `>=YYYY-MM-DD` range
   syntax, UTC), `CannotCount` when `total_count` exceeds the page; skips this run by
   `GITHUB_RUN_ID`, other days by `created_at[:10]`, and runs whose `display_title` does not
   start with `dry run ` (`display_title` is the evaluated `run-name` when one is set); one
   `/actions/runs/<id>/jobs` call per remaining run; a run counts when its step named
   `Nightly run` has `status == "in_progress"` or `status == "completed"` with a conclusion
   other than `skipped`/null. Those are the real field names of the two endpoints. My probe of
   `counted()` with the shapes GitHub returns: cancelled before start (`steps: []`) -> not
   counted; job cancelled at "Install requirements" (Nightly run `skipped`) -> not counted;
   cancelled during Nightly run (`cancelled`) -> counted; `queued`/`pending` step -> not
   counted (it is this run, or a later poll will count it); gate said `run=false` (step
   `skipped`) -> not counted, so a skipped run does not consume the cap. The test pins the
   boundary: 5 counted -> `DRY RUN 6 of 6 today; the result goes to data-dryrun-S16` and
   runs; 6 -> `DRY RUN SKIPPED: 6 of 6 today`, `run=false`; manual dispatch counted and
   capped alike. Cannot count (HTTP error, network error, >1 page, no token, no
   repository) -> skip with the reason. Manual dry runs made before W1b lands are titled
   `nightly` and are not counted, as the prereg states. PASS.
5. **Quiet windows.** `quiet()`: `|now - deadline| < 1 h` for every deadline (16:30:00
   before a 17:30 deadline is allowed, 16:30:01 is not; 18:29 skipped, 18:30 allowed);
   the night window from 21:30:00 UTC (21:29:59 allowed) until the data tip is at or after
   that 21:30 (a 21:58 commit closes it from 21:58; a 03:25 backup commit closes it), at the
   latest 03:17:00 (03:16:59 still quiet, 03:17:00 allowed); unknown tip = quiet. Windows are
   checked before any API call (test records zero calls). `gate()` skips when `fpl.sqlite` is
   absent or the `events` table unreadable. PASS.
6. **Manual dispatch.** Inputs unchanged; `result_branch` gives `data-dryrun` for every
   dispatch; `odds_live` is read only from `inputs.odds_live`, empty on a push. A real run
   (schedule, or master with `dry_run` unticked) never reaches the gate: `due_main` calls
   `fpl_dryrun.gate` only when `run_mode(env)[0] == "dry"` (test `real_runs_never_reach_the_gate`
   with a 21:45 scheduled run and a 17:10-near-deadline real dispatch; mutation V26 red). PASS.
7. **Tests.** All of the listed kinds exist in `tests/test_W1b.py` (28): trigger filter,
   windows, cap and result-branch naming as pure functions; the workflow text parse (push
   `dry/**` only, group `nightly-dryrun`, run-name, key lines, permissions, due-step token);
   the hook; `--due` end to end with a fake Actions API, a real git checkout and a real
   `fpl.sqlite`, no network. Red before (14 of 28), mutations red (29 of 29 mine), suite green
   bare, under a push env, under stand-in zones and hermetically, regeneration byte-identical.
   The older tests changed are exactly the three claimed: `test_fpl.NightlyWorkflow`'s trigger
   list (`push, schedule, workflow_dispatch`, comment lines skipped) and its key line, and
   `test_S3.FailureIssue`'s permissions test (`contents: write, issues: write, actions: read`).
   The S3 test that the nightly imports nothing under `tools/` or `analysis/` walks every
   top-level `.py` by AST, so it covers `fpl_dryrun.py` (stdlib + `fpl_publish` only). PASS.
8. **Docs.** `CLAUDE.md` and `BUILD_PLAN.md` Part E record: push to `dry/<item>`, result on
   `data-dryrun-<item>`, a second run as `dry/<item>-2`, delete both after landing with
   `git push origin --delete dry/<item> data-dryrun-<item>`, the four skip reasons, manual
   dispatch unchanged. Matches the ruling and the code. PASS.
9. **Readings**, judged:
   - **(a) The cap and the windows apply to every dry run, push or manual.** Consistent with
     ruling point 4 ("push-triggered and manual dry runs together count ... The 7th ends
     green") and with the standing rule "No manual nightly dispatch within 1 hour either side
     of an FPL deadline". The one phrase that could be read against it is point 6's "stays
     exactly as now"; the inputs and the result branch are indeed unchanged, only the gate
     is new. I judge (a) the reading the ruling supports; it is listed for the chat as the
     prereg requires.
   - **(b) The 21:30 window also closes at 03:17 UTC.** The ruling says "until that night's
     nightly has committed"; read literally, a night without a commit (a gate FAIL, a red
     sync) would keep every dry run skipped all the next day, the dry run of the fix above
     all, until the next night's commit. (b) avoids that and is a defensible extension. One
     consequence for the chat: 03:17 is the backup run's start, so after a failed night a dry
     run pushed between 03:17 and the backup's commit (about 03:35) runs alongside the backup
     run. Harmless to `data` (the dry run writes `data-dryrun-*` only; different concurrency
     groups), two parallel jobs at most; if the chat wants the backup run covered too, the
     close would move to about 04:00. Not a defect under the ruling as written.

## Other judgements the launch asked for

- **Concurrency.** GitHub allows one running and one pending run per concurrency group; a
  newer pending run cancels the older pending one, whatever `cancel-in-progress` says (that
  flag concerns the running one, which is never cut here). So a third dry run queued behind a
  running one cancels the pending second. This is inherent GitHub behaviour, and the ruling
  itself mandates the one group `nightly-dryrun`. The cancelled run never started "Nightly
  run", so it does not count against the cap; its lane sees "cancelled" on the Actions tab
  and no `data-dryrun-<item>` update, and pushes `dry/<item>-2`. To report, not a defect.
- **Minor, no action required:** (i) an `events` table that exists but has no deadline rows
  gives `{}`, and the gate proceeds without the deadline check (only a missing file or an
  unreadable table skips); the `data` branch always holds the season's 38 events, so this is
  theoretical. (ii) The run-name uses the `inputs` context, which GitHub makes available to
  `run-name`; on `schedule` and `push` it is empty and the expression falls to `'nightly'` /
  the push clause respectively. (iii) `data_tip` works on the shallow `data` checkout
  (`git log -1` on a depth-1 clone).

## Write guard
I wrote only this file. `git -C C:\GIT\FPL status --short` before and during the run showed
only the main session's four untracked `worklog/verify_*.md` files; the data worktree's
status stayed empty; `C:\GIT\FPL-b` was not opened.

## VERDICT: PASS

The prereg with the ruling precedes the code (7aa568f 00:08:40 UTC before a9248d1 00:35:16
UTC) and is byte-identical on the branch; the suite goes 499 -> 527 green on clean checkouts,
also under a push-like runner environment, stand-in zones and a hermetic environment; 14 of
28 new tests are red with only the module dropped in, and 29 of my own mutations across the
workflow, the gate, the publisher and the due wiring each turn a test red; the frozen-clock
regeneration is byte-identical between ab047c3 and a9248d1 (and the recording code is
untouched); no changed file holds a key, an `apiKey=` URL or an `Authorization` value, and the
token reaches only the request header; the trigger, dry path, key, result-branch, cap,
window, dispatch, hook, test and docs acceptance points each check out against the workflow
text, the code and the real GitHub API field semantics. Readings (a) and (b) are judged
consistent with the ruling, with the 03:17 close and the concurrency pending-cancel behaviour
reported as decisions for the chat rather than defects.
