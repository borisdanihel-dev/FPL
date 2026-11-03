# W1b - verifier report (pre-merge delta, w1b-wip 09fcff4 against origin/master e19657e)

- **Verifier:** backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high, as
  `.claude/agents/backtest-verifier.md` on disk says (read first; it matches the loaded
  instructions). Date: 2026-10-20 (UTC afternoon).
- **Item:** W1b, runner work: automatic dry runs by push to `dry/<item>`; the dry-run gate
  (`fpl_dryrun.py`) with the quiet windows and a daily cap. Descriptive/pipeline item: no
  metric, no forecast, no feature. Checks 1 and 3 of the agent file are n/a; the item's own
  acceptance tests (prereg items 1-9) are verified instead.
- **Scope of this run:** the delta since the code-level PASS at a9248d1
  (`worklog/verify_W1b_pre.md`, read only): 1118948, 7ceab6f, cd6d039, 09fcff4; and what a
  merge of 09fcff4 into origin/master (e19657e) would bring.
- **Not done, by instruction:** no workflow dispatched, nothing pushed, no FPL or Odds API
  call. The data worktree was only `git -C C:\GIT\FPL-data pull --ff-only` (already up to
  date, tip 63e6a44 nightly 2026-10-20); its `git status --short` is empty before and after
  every step here. Scratch under `scratchpad/v1b/` only; this file is the only write in any
  worktree. Nothing committed.

## Prereg and rulings (agent file: prereg before code; the ruling verbatim)

- `prereg/W1b.md` first committed at 7aa568f (2026-10-19 02:08:40 +0200); the first code
  commit is a9248d1 (02:35:16 +0200). PASS.
- RULING W1b (points 1-7, END RULING) is in the prereg under "## Ruling". The morning
  ruling of 19 Oct (points 1-7) was appended at 0674e0f (08:01:43 +0200), before 1118948
  (08:39:43 +0200) applied its point 4. RULINGS PART F item F-A was appended at 677f34e
  (2026-10-19 17:26:34 +0200), before 09fcff4 (2026-10-20 18:45:16 +0200) changed the cap.
  `prereg/W1b.md` is byte-identical on origin/master and 09fcff4. PASS.

## Check 1 - what the merge brings to master

- `git merge-base origin/master 09fcff4` = e19657e = origin/master, so
  `git diff origin/master...09fcff4` and `git diff origin/master 09fcff4` are the same diff:
  11 files, 1143 insertions, 21 deletions:
  `.github/workflows/nightly.yml` (17), `BUILD_PLAN.md` (+27), `CLAUDE.md` (+19),
  `fpl_dryrun.py` (new, 202), `fpl_nightly.py` (12), `fpl_publish.py` (44), `test_fpl.py` (13),
  `tests/test_S3.py` (6), `tests/test_W1b.py` (new, 433), `worklog/cc_2026-10-19_W1b.md` (new),
  `worklog/verify_W1b_pre.md` (new).
- Every one of the 11 is W1b's own (`fpl_nightly.py` is the `--due` wiring of the gate;
  `fpl_prepush.py` is unchanged on both sides - its guard is master-only, so `dry/*` pushes
  and `data-dryrun-*` deletions already pass, which `tests/test_W1b.py Hook` pins). Because
  the merge base is master's tip, no file outside the diff can differ: no stale copy of a
  master file is reintroduced. PASS.
- cd6d039 (merge of e19657e into w1b-wip) touched BUILD_PLAN.md, CLAUDE.md, test_fpl.py and
  tests/test_S3.py from both parents. `git diff e19657e cd6d039` on those four is exactly
  W1b's delta (+27, +18, 13, 6). BUILD_PLAN.md at 09fcff4 holds both the W1b "Dry runs by
  push" procedure (line 121, Part E) and "## Part F - queued rulings" (line 149) with all 12
  F-x items master has (12 on both). CLAUDE.md's diff against master is additions only (0
  removed lines). PASS.

## Check 2 - the delta since a9248d1 on W1b's own files

- **1118948 against the morning ruling, point 4** ("The 21:30 window closes at 04:00 UTC,
  which covers the backup run. ... a missing deadline row makes the gate WARN instead of
  skipping silently"): `NIGHT_END = time(3, 17)` -> `time(4, 0)`; `gate()` now reads
  `events` itself read-only (`read_deadlines`), prints `DRY RUN WARN: no deadline for GWn -
  the 1-hour rule is not checked for it` (or `no deadline rows in events`) and goes on with
  the deadlines it has; no `fpl.sqlite`, or an unreadable `events` table, still skips.
  `due_main` passes `say` through so the WARN reaches the log. Tests: `Windows.test_the_night`
  (03:17 and 03:59 quiet, 04:00 not), `DueGate.test_a_missing_deadline_row_warns_and_the_run_goes_on`,
  `..._no_deadline_rows_at_all_warns_...`. PASS.
- **09fcff4 against F-A** ("12 per UTC day, manual and push-triggered together ... Quiet
  windows unchanged ... W1b's cap constant becomes 12"): the only non-comment change on
  `fpl_dryrun.py` between cd6d039 and 09fcff4 is `CAP = 6` -> `CAP = 12`; `NIGHT_START`,
  `NIGHT_END`, `DEADLINE_GAP` and `quiet()` are untouched. Manual and push together: the
  count reads every run whose `run-name` starts with `dry run ` (push and dispatch alike), and
  my probe below shows a manual dispatch is gated at 12. Tests at 7, 12 and 13 of 12
  (`Cap.test_the_twelfth_runs_and_the_thirteenth_skips_green`,
  `Cap.test_a_manual_dry_run_counts_and_is_capped_too`, `DueGate.test_a_push_at_the_cap_skips_green`).
  PASS.
- **Docs say 12:** CLAUDE.md ("once 12 dry runs, pushed and manual together ... (RULINGS
  PART F, F-A)") and BUILD_PLAN.md Part E item 4 ("`12 of 12 today`; F-A, was 6"). PASS.
- **Defect D1 (comments only, no behaviour):** two comments W1b added still say 6:
  `.github/workflows/nightly.yml` line 14 ("when 6 dry runs, pushed and manual together,
  already ran that UTC day") and `fpl_nightly.py` line 351, the `due_main` docstring ("the
  cap of 6 a day (RULING W1b)"). A third, `nightly.yml` line 9 ("At most 6 dry runs a day
  (point 9)"), pre-dates W1b (it is in a9248d1^; S2 amendment 2, point 9) and is now also
  out of date under F-A. The constant, the log line and the tests say 12.
- The 1-hour window is either side of a deadline (`abs(now - dl) < DEADLINE_GAP`), as RULING
  W1b point 5 ("within 1 hour of a deadline"), the prereg's acceptance item 5 and the standing
  CLAUDE.md rule say; F-A's "one hour before a deadline" is under "Quiet windows unchanged",
  and nothing changed. Noted, not a defect.

## Check 3 - clean-checkout suites (git archive, keys removed)

`git archive` of each commit into `scratchpad/v1b/<commit>/`; `python -m unittest discover
-v -p "test*.py"` from inside; `ODDS_API_KEY`, `FPL_DATA_DIR` and `FPL_ODDS_LIVE` unset
(`env -u`); Python 3.14.7, Windows.

| checkout | result |
|---|---|
| origin/master e19657e, bare | Ran 708, OK (skipped=10) |
| cd6d039 (before the cap), bare | Ran 738, OK (skipped=10) |
| 09fcff4 (after), bare | Ran 738, OK (skipped=10) |
| 09fcff4, `FPL_DATA_DIR=C:\GIT\FPL-data` (runner-like, read-only) | Ran 738, OK (skipped=3) |

- The 30 added tests are all `tests.test_W1b` (30 of 30 ok in every run). Bare skips: the
  7 "no real export / fpl.sqlite / projection_log.csv" skips, 1 "no 2025/26 copy",
  2 "no time-zone database here (Windows without tzdata)". With the data: only the latter 3.
- `tests.test_S3.Hermetic.test_the_git_using_tests_pass_with_an_empty_home`: ok (bare and
  with data).
- The data worktree: `git status --short` empty before and after the runner-like run.
PASS.

## Check 4 - the recording path

- `git diff origin/master 09fcff4 -- fpl_edge.py fpl_sync.py checks.py fpl_gate.py fpl_alert.py
  fpl_odds.py fpl_ship.py p1_eval.py fpl_hist.py overrides.csv watchlist.txt requirements.txt
  tools` is empty.
- My own regeneration: two scratch folders with copies of the data worktree's
  `fpl_export_gw7.json`, `projection_log.csv`, `fpl.sqlite` and `watchlist.txt`; the
  nightly's five sources (`fpl_nightly.SOURCES`: own, xg, minutes, bottomup, fpl_ep) recorded
  with `fpl_edge.py --record --source <src> --status reports/record_status.tmp` on the
  origin/master archive and on the 09fcff4 archive, the clock frozen at
  2026-10-20T20:00:00Z (the `datetime` class patched in the `datetime` module, so the
  function-local imports see it too; every new row is stamped
  `2026-10-20T20:00:00+00:00`). Both: RECORD OK own 277, xg 257, minutes 257, bottomup 257,
  fpl_ep 668, "2 days, 21:30:00 before deadline".
  `projection_log.csv`: sha256 2236b276... on both, 470968 bytes, 9205 lines - byte-identical;
  `record_status.tmp` byte-identical. (A first attempt that froze only `fpl_edge.datetime`
  left the real clock in, and the only differences were the `made_at` second of the 1716 new
  rows; superseded by the proper freeze above.) PASS.

## Check 5 - mutations (mine, 17; fresh copy of the 09fcff4 archive each; `tests.test_W1b`,
`test_fpl.NightlyWorkflow`, `tests.test_S3.FailureIssue` = 48 tests)

| # | mutation | result |
|---|---|---|
| M1 | `CAP = 13` | red, 4 failures (the 12th/13th tests, manual cap, due-gate cap, below-cap line) |
| M2 | `CAP = 6` (the old cap) | red, 4 failures |
| M3 | `n >= CAP` -> `n > CAP` | red, 3 failures |
| M4 | `NIGHT_END` back to 03:17 | red (`Windows.test_the_night`) |
| M5 | `NIGHT_START` 21:40 | red (`Windows.test_the_night`) |
| M6 | `DEADLINE_GAP` 2 hours | red (`Windows.test_a_deadline`) |
| M7 | deadline window one-sided (before only) | red (`Windows.test_a_deadline`) |
| M8 | unknown data tip does not quiet the night | red (`Windows.test_the_night`) |
| M9 | skipped runs counted | red (`Cap.test_counting`) |
| M10 | this run counted too | red (`Cap.test_counting`) |
| M11 | cannot-count lets the run go | red, 2 failures |
| M12 | the gate on every run (real runs too) | red (`DueGate.test_real_runs_never_reach_the_gate`) |
| M13 | `due_main` gates push runs only (a manual dry run bypasses the gate) | **survived, 48 ok** |
| M14 | the key passed on a push (both lines) | red, 2 failures (test_W1b + test_fpl) |
| M15 | push trigger widened (`lane-b` added) | red (`Trigger.test_the_push_trigger_is_dry_only`) |
| M16 | a push's result on `data-dryrun` | red, 4 failures |
| M17 | `push_dry` accepts `data` | red (`ResultBranch.test_push_dry_refuses_...`) |

16 of 17 red. **Defect D2 (test gap, not a code defect):** no test drives a manual dispatch
dry run (ref master, `dry_run` ticked, event `workflow_dispatch`) through `due_main`; the
manual-cap test calls `decide()` directly. The behaviour itself is right - my direct probe of
`N.due_main` on 09fcff4 with a fake Actions API and a scratch data checkout (tip 18 Oct
21:58, GW8 deadline 23 Oct 17:30):

| environment | result |
|---|---|
| manual dry run, 3 today, 14:00 | run=true, `DRY RUN      4 of 12 today; the result goes to data-dryrun` |
| manual dry run, 12 today | run=false, `DRY RUN SKIPPED: 12 of 12 today` |
| manual dry run, 21:45 (night, tip 18 Oct) | run=false, the nightly's window |
| manual dry run, 03:59 / 04:00 | run=false / run=true (1 of 12) |
| manual dry run, 16:31 on 23 Oct | run=false, `within 1 hour of the GW8 deadline` |
| dispatch on a branch, `dry_run` unticked, 12 today | run=false, 12 of 12 (a non-master ref is always dry) |
| REAL dispatch master unticked, 12 today, 17:00 on 23 Oct | run=true, `DUE          not the backup cron`, no gate line |
| REAL schedule 21:45, 12 today | run=true, no gate line |
| REAL backup cron 03:17, no status.txt, 12 today | run=true, no gate line |

PASS, with D2 listed.

## Check 6 - secrets

- `ODDS_API_KEY` env is unset in this session. Over the whole merge diff, the only hits for
  key patterns, `apiKey=`, `api_key`, `Authorization`, long hex/base64 runs: the two workflow
  lines `ODDS_API_KEY: ${{ github.event_name != 'push' && secrets.ODDS_API_KEY || '' }}` (a
  reference, no value), the same text in test_fpl.py / tests/test_W1b.py, and
  `fpl_dryrun.py` `"Authorization": f"Bearer {token}"` (a template, no value). The test
  token is the literal `t-no...` (fake). The workflow passes no Odds key to a push run: both
  carrying steps evaluate to `''` when `github.event_name == 'push'`; `FPL_ODDS_LIVE:
  ${{ inputs.odds_live }}` is empty on a push; the `--due` step gets only `github.token`
  (needed for `actions: read`), and `fpl_dryrun.py` never prints it
  (`Cap.test_no_token_means_no_count_and_the_token_is_never_shown`). PASS.

## Check 7 - the real nightly on master is unchanged

- `due_main`: the gate is entered only when `fpl_publish.run_mode(env)[0] == "dry"`;
  `run_mode` returns "real" for a scheduled run on master and for a master dispatch with
  `dry_run` unticked (unchanged function). `--due` runs before `pip install`, and the new
  imports it reaches (`fpl_publish` -> `random`, `fpl_gate`; `fpl_dryrun` only on a dry run)
  are standard library.
- Workflow: the `push` trigger is `dry/**` only (no tags, paths or other branch); the two
  crons and the three dispatch inputs are unchanged; `concurrency.group` and `FPL_DRY_RUN`
  lines are unchanged (`nightly-data` / `'false'` for master dispatch and schedule);
  `run-name` is `nightly` unless push, or a dispatch that is dry; `actions: read` is an added
  permission on the one job; the key expression yields `secrets.ODDS_API_KEY` for every
  non-push event. The runner freeze: GW8 `events.deadline_time` = 2026-10-23T17:30:00Z in the
  data database (read-only), so the 30-hour freeze starts Thu 22 Oct 11:30 UTC, as the launch
  message says. My probe above: the three real-run environments print no `DRY RUN` line and
  give `run=true`. PASS.

## Acceptance tests of the prereg (items 1-9)

1. Trigger `dry/**` only; a push's ref is never master so always dry - PASS (Trigger tests;
   `run_mode`).
2. Dry path: key `''` on push in both steps; `FPL_ODDS_LIVE` empty; group `nightly-dryrun`,
   `cancel-in-progress: false` - PASS.
3. `data-dryrun-<item>` for a push, `data-dryrun` for a dispatch; `push_dry` refuses anything
   else without a git call; the hook allows `dry/*` and `data-dryrun-*` deletions - PASS
   (ResultBranch, PushRunPublishes with a bare remote, Hook; M16, M17).
4. Cap: counted with the Actions API, `actions: read` on the one job, push and manual
   together, a run counts once its "Nightly run" step started, this run left out; cannot
   count = skip; now 12 of 12 (F-A supersedes the "6 of 6" wording of this item) - PASS.
5. Quiet windows: 21:30 until the data commit, 04:00 at the latest; 1 hour either side of a
   deadline - PASS.
6. Manual dispatch keeps its inputs and `data-dryrun`; a real run is never gated - PASS.
7. Tests in `tests/test_W1b.py`: trigger, windows, cap, naming, workflow parse, hook, `--due`
   end to end with a fake API, no network - PASS (with D2: the manual-dispatch path through
   `due_main` is not pinned).
8. CLAUDE.md and BUILD_PLAN.md Part E record the procedure - PASS.
9. Readings (a) and (b): both ruled on (morning ruling point 4; (b)'s 03:17 became 04:00)
   and implemented as ruled - PASS.

## Defects for the chat

- **D1** - two W1b-added comments still say 6 (`nightly.yml` line 14; `fpl_nightly.py` line
  351, the `due_main` docstring); `nightly.yml` line 9 (pre-W1b) also says 6. Comment-only;
  the constant, the log line, the tests, CLAUDE.md and BUILD_PLAN.md say 12. A one-line
  docs fix each.
- **D2** - no test drives a manual dispatch dry run through `due_main` (mutation M13
  survives); the behaviour is verified by my probe. One `DueGate` test would close it.

## VERDICT: PASS

The merge of 09fcff4 brings exactly W1b's 11 files onto a master tip that is its own merge
base, so nothing of master is displaced and cd6d039 kept both the W1b procedure and Part F;
1118948 implements the morning ruling's point 4 (04:00 close; a missing deadline row warns and
goes on) and 09fcff4 implements F-A (CAP 12, manual and push together, windows untouched),
both rulings verbatim in the prereg before the code; the suite is green on clean checkouts
bare (708 -> 738) and runner-like with the read-only data (738, Hermetic ok); the recording
path is untouched and a frozen-clock regeneration on both codes is byte-identical; 16 of 17
mutations go red and the one survivor is a test gap whose behaviour my probe confirms; no
secret value is in the diff and no key reaches a push run; the real nightly (schedule, master
dispatch unticked, backup cron) never reaches the gate. Two defects remain, neither
behavioural: three comments that still say 6 (two of them W1b's), and the missing end-to-end
test for a manual dry run.
