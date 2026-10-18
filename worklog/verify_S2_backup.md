# Verifier report: S2 decisions, point 2 (the weekly backup) - pre-merge pre-check

Verifier: backtest-verifier agent, model Fable 5.1 (claude-fable-5-1), effort high,
as `.claude/agents/backtest-verifier.md` on disk says (read first; it matched the
loaded instructions). Date 2026-10-18. Nothing written outside this file; no push,
no fetch and no ref change in `C:\GIT\FPL` or `C:\GIT\FPL-data`; GitHub read only
through `git ls-remote`. All work in a scratch clone of `C:\GIT\FPL` under the
session scratchpad (`.../scratchpad/vb/`).

## Scope

The fix on branch `s2-backup`, head `3ae739b` (one commit on master `d2cf781`),
touching `.github/workflows/nightly.yml` (the Weekly backup step) and `test_fpl.py`
only (`git diff --stat d2cf781 s2-backup`: 2 files, +132 -7). The ruling checked is
the verbatim text in `prereg/S2.md`, section "Decisions (after amendment 2)", point 2:

> Backup: one backup per Sunday, made by the scheduled run. Manual dispatches back up
> only when force_backup is ticked. A backup step that finds the day's release already
> exists skips with a log line and never fails the run.

The merge itself (tag, byte-identical commit, before 21:00 UTC) was not checked.

## Prereg before code

`git log -- prereg/S2.md`: the Decisions section landed in `d2cf781` at
2026-10-18 14:28:31 +0200; the fix commit `3ae739b` is dated 14:33:09 +0200 and is
the only commit on top of `d2cf781`. Prereg precedes code. PASS.

## Claim 1: the merged step did not meet the ruling

From the diff of `3ae739b` the step at `9b4a462`/`d2cf781` had
`if [ "$FORCE_BACKUP" != "true" ] && [ "$(date -u +%u)" != 7 ]; then ... skip`, so on a
Sunday a manual dispatch without `force_backup` fell through to the create; and the
create was a bare command under the runner's `bash -e`, so a release made between
`gh release view` and `gh release create` turned the run red. Confirmed by running
the new BackupStep tests against the old step (below): the two matching tests fail
with exactly those symptoms. Claim 1 holds.

## Claim 2: the new step against the ruling (read from `s2-backup:.github/workflows/nightly.yml`)

| Ruling clause | Step |
|---|---|
| one backup per Sunday, made by the scheduled run | `GITHUB_EVENT_NAME = schedule` -> backs up only when `date -u +%u` is 7, else `BACKUP skipped: not Sunday`, exit 0; the day's tag `backup-$(date -u +%F)` plus the exists check make it one per day |
| manual dispatches back up only when force_backup is ticked | any other event -> `elif [ "$FORCE_BACKUP" != "true" ]` -> `BACKUP skipped: a manual dispatch backs up only with force_backup ticked`, exit 0; with it ticked, any day |
| an existing day's release skips with a log line and never fails the run | `gh release view` before the create -> `BACKUP skipped: <tag> exists`, exit 0; and again after a failed create -> same line, exit 0; any other create failure -> `BACKUP FAILED: <tag> could not be created`, exit 1 |
| (unchanged) dry run | first line unchanged: `BACKUP skipped: dry run`, exit 0; the step's `if:` also excludes `FPL_DRY_RUN == 'true'` |

That is exactly the ruling. Can anything else fail the run on an existing release?
No: both "exists" paths `exit 0` before the pruning line is reached, and every `gh`
call before that point sits inside an `if` condition, where `bash -e` does not fire.
Two notes that do not touch the ruling's cases:

- The pruning pipeline (`gh release list ... | grep '^backup-' | sort -r | tail -n +9
  | while read ...; do gh release delete ...; done`) runs only after a successful
  create. A `gh` API failure there would still turn a run red after the backup was
  made. That line is unchanged from the merged step and is not an "existing release"
  case.
- GitHub's default shell for a `run:` step with no `shell:` key is `bash -e {0}`
  (no `pipefail`); the test harness runs the script under `set -eo pipefail`, which
  is stricter than the runner. Conservative, so not a problem; the implementer's
  wording "the runner's bash -e -o pipefail" is slightly inaccurate.

## Check 1: point-in-time leak

Not applicable: no forecast, feature or metric is produced. The seven runner files
(`fpl_nightly.py`, `fpl_publish.py`, `fpl_gate.py`, `fpl_edge.py`, `fpl_sync.py`,
`p1_eval.py`, `requirements.txt`) have identical blob ids at `d2cf781` and
`s2-backup`. PASS (N/A).

## Check 2: clean-checkout test runs (scratch worktrees of the scratch clone)

| Tree | Env | Result |
|---|---|---|
| `d2cf781` (before) | bare | Ran 378, OK (skipped=8) |
| `3ae739b` (after) | bare | Ran 386, OK (skipped=8) |
| `3ae739b` | `GITHUB_REF=refs/heads/s2-backup FPL_DRY_RUN=true` | Ran 386, OK (skipped=8) |
| `3ae739b` (copy) | `FPL_DATA_DIR=<scratch copy of C:\GIT\FPL-data, no .git>` `PYTHONTZPATH=<my own stand-in TZif>` | Ran 386, OK, 0 skips |

The 8 added tests are exactly the 8 `BackupStep` tests (set difference of the
verbose listings). The 8 bare skips are 2 no-real-export, 1 no-real-sqlite,
4 no-real-projection_log, 1 no-tz-database; all cleared with the data copy and a
time zone. The stand-in `Europe/London` TZif was generated by my own script into the
scratch folder (verified: 2026-10-17 BST, 2026-10-26 GMT), never in a repository.
The data copy had no file modified by the run. On this machine `shutil.which("bash")`
is `C:\Program Files\Git\usr\bin\bash.EXE` from both Git Bash and PowerShell, so
the BackupStep tests ran (not skipped) on Windows. PASS.

## Red before the fix (the item's acceptance tests)

`3ae739b`'s `test_fpl.py` against `d2cf781`'s `nightly.yml` (`BackupStep NightlyWorkflow`):
Ran 19, FAILED (failures=4):

- `test_a_manual_dispatch_on_sunday_without_force_backup_makes_no_backup` - gh was called (view + create)
- `test_a_release_made_meanwhile_is_skipped_and_never_fails` - exit 1 != 0
- `test_a_create_that_fails_for_another_reason_is_red` - no `BACKUP FAILED` line
- `test_weekly_backup_on_sundays_keeps_the_last_eight` - the pinned lines

The other 5 BackupStep tests pass on the old step, as the implementer said. Matches
claim 3. PASS.

## Checks 3 and 4: pre-registered evaluation

No metric, filter, bootstrap or threshold in this ruling; nothing was promoted or
re-tuned. The ruling text is present verbatim in `prereg/S2.md` and the step matches
it clause by clause (table above). PASS.

## Check 5: recording path

No Python runner file changed (blob ids identical, above). Readback of the dry run
of `s2-backup` (data-dryrun `b4efd66`, "dry run 2026-10-18 s2-backup 3ae739b
[skip ci]", one commit on data `e84bee6`, fetched into the scratch clone from
`C:\GIT\FPL`'s `refs/remotes/origin/data-dryrun`; blobs read with `git cat-file`):

- `logs/run_2026-10-18.log`: `Ran 386 tests ... OK (skipped=11)`; the 11 skips are
  the Windows-only ones (2 BatchRecordCheck, 1 NightlyRunner, 7 RecordResilience,
  1 StrandedTmp); all 8 BackupStep tests `ok` on Linux (Python 3.14.8); seven
  migration lines (`+ player_gw.fetched_at_utc`, `+ player_gw.ruleset`,
  `+ price_history.fetched_at_utc`, `+ price_history.london_date`, `+ fixtures.started`,
  `+ fixtures.fetched_at_utc`, `+ entry_gw.fetched_at_utc`); `RECORD OK own 275`,
  `xg 260`, `minutes 260`, `bottomup 260`; `STUCK CHECK OK`.
- `projection_log.csv`: data blob 239,265 bytes, 4,680 rows, 0 CR; dry blob
  293,477 bytes, 5,735 rows, 0 CR; the dry blob begins with the data blob byte for
  byte; +1,055 rows, all `made_at 2026-10-18T12:35:37+00:00`, event 8, by source
  own 275 / xg 260 / minutes 260 / bottomup 260.
- Gate re-run: a scratch worktree of `data` (`e84bee6`) with the dry-run content
  checked out on top, `python <s2-backup>/fpl_gate.py <dir>` -> `GATE OK integrity
  ok, 14 tables, price_history 25881 rows, frozen forecasts unchanged; fpl.sql
  written`; the regenerated `fpl.sql` hashes to `09860eff...`, identical to
  `dryrun:fpl.sql`; `fpl.sqlite` blob `f61140f3...` identical.
- `git ls-remote`: data still `e84bee6`; no `backup-2026-10-18` tag (a
  `backup-2026-10-17` tag exists at `e84bee6`, from before this item); data-dryrun
  `b4efd66`; master `d2cf781`; s2-backup `3ae739b`.

The dry run skips the backup step by design, so the step's behaviour is shown by its
tests inside that run, which passed. PASS.

## Check 6: mutation spot-check (scratch copies of `3ae739b`, `BackupStep NightlyWorkflow`)

| Mutation | Red |
|---|---|
| M1 dry-run guard line removed | 1 (`test_a_dry_run_calls_no_gh`) |
| M2 `= "schedule"` -> `!= "schedule"` | 8 |
| M3 Sunday `7` -> `6` | 5 |
| M4 `elif FORCE_BACKUP != true` -> `= true` | 4 (incl. dispatch-without-force) |
| M5 pre-create exists check removed | 3 (`exists`, `made meanwhile`) |
| M6 post-failure exists check removed | 1 (`made meanwhile`) |
| M7 `BACKUP FAILED ... exit 1` -> `exit 0` | 1 (`another reason is red`) |
| M8 `if ! gh release create` -> `if gh release create` | 4 |

Every mutation turns at least one test red. PASS.

## Check 7: secrets

`git show s2-backup` for the two files: no `apiKey=`, no `Authorization` header
value, no key-like string in the added lines. `GH_TOKEN: ${{ github.token }}` is an
expression, not a value; the test's `GH_TOKEN="x"` is a stand-in. PASS.

## Point 1 of the ruling (CLAUDE.md item e)

`d2cf781:CLAUDE.md` item e ends with "Exception: the dry-run workflow force-pushes
to data-dryrun only. Claude Code itself never force-pushes, and nothing ever
force-pushes to master or data." - character for character the ruling's sentence.
PASS.

## Observations (not blocking)

1. `BackupStep._run` opens `gh.log` without closing it (ResourceWarning at
   `test_fpl.py:5411` in the Linux run log). Cosmetic.
2. Tag `pre-S2` is an annotated tag object `b5b1712` pointing at commit `1cddca9`,
   as the launch message says.
3. The pruning pipeline and the runner's actual default shell (`bash -e`, no
   `pipefail`) are noted under claim 2; neither affects the ruling's cases.

## Write guard

`git status --short` in `C:\GIT\FPL` and `C:\GIT\FPL-data`: clean before and
after; refs unchanged (master `d2cf781`, s2-backup `3ae739b`,
origin/data-dryrun `b4efd66`, data `e84bee6`); `git worktree list` in `C:\GIT\FPL`
shows only the two real worktrees. The only file written in either repository is
this one.

VERDICT: PASS

Reason: the ruling's point 2 is in `prereg/S2.md` verbatim and committed (14:28:31)
before the one fix commit `3ae739b` (14:33:09); the new Weekly backup step maps
clause by clause onto the ruling (scheduled run -> Sundays only; any other event ->
only with force_backup; an existing day's release -> a skip line and exit 0 both
before and after the create; any other create failure -> red), and no other line can
fail the run on an existing release; the suite goes 378 -> 386 green in a clean
checkout under the bare, dry-run and real-data environments (0 skips with data and a
time zone), the 3 BackupStep tests plus the workflow pin are red on the d2cf781 step,
all 8 one-line mutations are red; no runner Python file changed and the dry run of
this exact commit appended 1,055 rows to a byte-identical copy of data's projection
log with GATE OK and an identical fpl.sql; the changed files hold no secret; and the
ruling's point 1 sentence is in CLAUDE.md item e verbatim.
