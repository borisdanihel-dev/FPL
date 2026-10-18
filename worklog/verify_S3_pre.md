# Verifier pre-check: S3 (Step 3, D3) on s3-wip 8149abd

Run on 2026-10-18, 14:20-15:20 UTC. Model: Fable 5.1 (claude-fable-5-1), effort
high as `.claude/agents/backtest-verifier.md` sets; the file on disk was read
first and matches the loaded instructions. No credits prompt, no fallback.
Pre-check by ruling S3 point 8 and the fast-lane merge rule; the final verifier
follows the merge and the real dispatch.

Scope: branch `s3-wip`, head 8149abd = c1d130a (S3) + 8149abd (amendment 1) on
master 5727db2. Master is d5aa4d2. Dry run f23d74a on `data-dryrun`, one commit
on data 4af6abe. All work in a scratch clone and copies; nothing fetched into,
written to or changed in C:\GIT\FPL, C:\GIT\FPL-data or C:\GIT\FPL-b (both
repositories `git status` clean after the run; master, s3-wip, data and
data-dryrun refs unchanged). Key-like strings masked: first 4 characters, "...".

## Prereg ordering: PASS

- The ruling text first entered `prereg/S3.md` at adf3d32 (12:50 +0200);
  the template rows at 5727db2 (15:29); first S3 code commit c1d130a (15:57).
- Amendment 1 verbatim at d5aa4d2 on master (16:04); its code 8149abd (16:16).
- `prereg/S3.md` on s3-wip equals the 5727db2 version (s3-wip does not contain
  d5aa4d2; the merge brings the amendment's prereg and code together).
- RULING S3 points 1-8 and Amendment 1 points 1-4 are present with END RULING
  markers; RULING FAST-TRACK items 1 and 5 are in `prereg/FAST.md`. I did not
  read any transcript; verbatim-ness against the chat cannot be checked here.

## Check 1 (point-in-time): not applicable, with evidence

The item produces no forecast, feature or metric. `fpl_edge.py` is
blob-identical between 5727db2 and s3-wip; the nightly's `--record`, `--watch`
and `--diff` invocations are unchanged (fpl_nightly.py lines 226-255). Check
20 of the new code audits made_at against the deadline on the real log: "0 of
5742 rows at or after their deadline" (dry run, and my re-run). No shift probe
applies (no correlation metric).

## Check 2 (clean-checkout test counts): PASS

| run | command | result |
|---|---|---|
| before, 5727db2 | `python test_fpl.py` | 386 tests, OK (skipped=8) |
| after, s3-wip, bare | `python -m unittest discover -v -p "test*.py" -s . -t .` | 459 tests, OK (skipped=9) |
| after, FPL_DATA_DIR=<scratch clone of data> + PYTHONTZPATH (stand-in TZif) | same | 459 tests, OK (skipped=0) |
| after, GITHUB_REF=refs/heads/s3-wip FPL_DRY_RUN=true | same | 459, OK (skipped=9) |
| after, hermetic (below) | same | 459, OK (skipped=9) |

Stand-in zones: TZif v2 files for Europe/Prague and Europe/London written by
my own generator with POSIX footer rules only (`PYTHONTZPATH`); verified
00:30Z 25 Oct -> 02:30 CEST, 01:30Z -> 02:30 CET, 28 Mar 2027 01:30Z -> 03:30.
The data clone used for the FPL_DATA_DIR run stayed `git status` clean.

Hermetic (amendment 1, point 1), proven first: in an environment with
HOME/USERPROFILE/XDG_CONFIG_HOME at an empty folder, GIT_CONFIG_NOSYSTEM=1,
GIT_CONFIG_GLOBAL=<empty file> and no GIT_AUTHOR_*/GIT_COMMITTER_*/EMAIL, a
`git commit` in a fresh repo fails with "Author identity unknown ... unable to
auto-detect email address" (exit 128) and `git config --list` shows only the
repo's own .git/config. The whole discovered suite under that environment:
459 tests, OK (skipped=9). The tests' own `Hermetic` class does the same for
the git-using classes in a child process.

## Check 3 (re-run of the pre-registered evaluation): PASS

No metric is pre-registered; the acceptance tests are Step 3 points 1-6, the
27-check table, ruling points 1-8 and FAST items 1 and 5. What I re-ran:

- `checks.py --stamp 2026-10-18` over the dry run's exact content (worktree at
  4af6abe with f23d74a's files checked out over it, exports restored), in dry
  mode: every line of checks 1-22 and 26-29 equals `status_dryrun.txt` from
  f23d74a; 23 says 8 files instead of 6 (my reconstruction also holds fpl.sql
  and status_dryrun.txt, which did not exist at check time), 24 is SKIP (no
  GITHUB_REPOSITORY locally; 4 MB on GitHub), 25 is measured against my clock.
- Dry run f23d74a read back with `git cat-file`: 459 tests OK (skipped=11),
  TESTS OK, SYNC STATS with 4 core calls at 200, four RECORD OK (own 277, xg
  262, minutes 262, bottomup 262), CHECKS OK, `STATUS OK ... checks 25/25 |
  repo 4 MB`, 28 "459 tests green", 29 OK; the commit adds
  `reports/status_dryrun.txt` and no `status.txt`; the report file starts with
  the status line; the log differs from data only by the same-day GW8 block
  (12:53 rows replaced by 14:18 rows), the other 4679 rows identical.
- Action pins (ruling 2), by `git ls-remote --tags` on the public repos:
  checkout `3d3c...` = refs/tags/v7.0.1, setup-python `5fda...` =
  refs/tags/v7.0.0; both are the newest tags of their repositories. Both
  workflows carry them; the old @v4/@v5 are gone.
- Local end-to-end rehearsal (claim 11), on a scratch clone of data with a
  scratch bare remote, `fpl_sync.py`'s `__main__` replaced by a stub printing
  the dry run's SYNC STATS line (module API kept), PYTHONTZPATH set:
  1. planted failing test in tests/: nightly exit 1, "FINISHED WITH ERRORS:
     tests, record, checks"; `STATUS FAIL ... checks 22/24` with 28 FAIL and
     29 FAIL (all four sources "skipped - test suite is red"); publish exit 1,
     "CHECKS FAIL nothing committed tonight (Step 3.1)"; remote data unchanged.
  2. healthy: 459 OK, TESTS OK, four RECORD OK, `STATUS OK ... 24/24`, the
     report headed by the status line, publish GATE OK + PUSH OK, commit holds
     `reports/status.txt` (9, 22, 24, 26, 27 SKIP). A fresh clone then answers
     `--due` for the 03:17 cron with NOT DUE.
- `--due` by hand: backup cron with no status.txt -> DUE; with a status.txt
  generated after the last 21:40 slot -> NOT DUE, `run=false` written to
  GITHUB_OUTPUT, data folder `git status` clean; nightly cron -> DUE.

## Check 4 (metric, filter, bootstrap, threshold): PASS (n/a item)

The prereg states n/a for hypothesis, sample, metric, bootstrap and threshold
and names the acceptance tests; nothing was promoted or re-tuned. The rulings
are present in the prereg (see ordering above).

## Check 5 (recording path): PASS

Frozen clock (a `datetime` shim first on PYTHONPATH pinning `now()` to
2026-10-18T15:00:00Z), two identical copies of the data clone, `fpl_edge.py
--record` for own/xg/minutes/bottomup, `--watch`, `--diff` from the 5727db2
tree and from the s3-wip tree: `diff -r` of the two copies is empty.
projection_log.csv md5 c526... on both, report 83db..., watch 63c5...; the
only change against data is the same-day GW8 block (12:53 -> 15:00, 275/260/
260/260 rows), the other 4679 rows byte-identical. The status-line prepend is
done by `checks.py` in the nightly's checks step, not by `--diff`.

## Check 6 (mutation spot-check): PASS, one survivor noted

30 distinct one-line breaks in a scratch worktree, each run against
tests/test_S3.py (plus test_fpl.NightlyWorkflow/DryRunMode/NightlyRunner where
relevant): 29 red, 1 green. Red: c03 5% band, c04 FAIL->WARN, c13 boundary,
c16 decrease ignored, c20 new late rows FAIL->WARN, c22 run mid-gameweek, c22
always SKIP, c26 threshold, c28 red suite ignored, c29 missing source ignored,
run_all lets a check crash, status line counts SKIP, dry run writes status.txt,
publish FAIL blocks only dry runs, backup_due inverted, nightly runs
test_fpl.py only, nightly never says TESTS OK, alert acts on dry runs, alert
keeps a second open issue, alert API failure on a red run exits 0, sync retries
every HTTP error, sync retries bad JSON, sync pause outside 0.3-0.5, sync
stats only when finished, setup-python unpinned, workflow without issues:
write, failure-issue step not dry-guarded, backup cron removed, a step not
gated on due. Survivor: c11's allowance loosened from 0.1 to 0.2 a night stays
green, because the test plants a +0.3 step in one night (a test-precision gap,
not a code fault).

With master's runner files restored (fpl_sync, fpl_publish, fpl_nightly,
fpl_gate, both workflows) and checks.py, fpl_alert.py and tests/ kept, 25
distinct tests of tests/test_S3.py are red (12 failures, 13 errors); the
implementer's 18 presumably restored a smaller set.

## Check 7 (secrets): PASS

The 12 added or changed files scanned for apiKey=/api_key=, Authorization
header values, token-shaped strings and 32-hex strings, and with
`fpl_gate.secret_hit`: no key value, no URL with a key, no header value. The
two gate hits are the pattern definition in `fpl_gate.py` (KEY_PATTERNS, its
docstring) and the pre-existing comment in `nightly.yml` line 16, both present
at 5727db2. `checks.py` and `fpl_alert.py` build an `Authorization: Bearer`
header from GH_TOKEN at run time and never print or write it.

## The 27-check table and the readings (claim 1): judged

Every row implemented in `checks.py` with the table's threshold; where the
table names no level, FAIL for an untrustworthy API answer or stored data,
WARN otherwise: 1-5, 8, 10, 11, 13, 15, 18, 23 FAIL; 6, 7, 9, 12, 14, 17, 25,
26 WARN; 16 FAIL on a decrease, WARN on growth off; 24 WARN 500/FAIL 900; 27
SKIP manual (the token has no actions scope). Readings I accept: 2 vacuous
(the nightly makes no element-summary call; `--history` only); 19 WARN agrees
with S2 ruling 2 ("duplicates among past-deadline rows are reported, not
deleted"); 20 FAIL for new late rows, WARN for committed ones; 21 WARN with
`--stuck` already turning the run red; 22 SKIP until `gameweek_settled`; a
raising check is a WARN (tested). Check 8's field list is the table's eleven.
Check 28/29 (amendment 1, point 3): the test "a night with a red suite never
reads OK" and my rehearsal both give STATUS FAIL with exactly 28 and 29.

## Claims 2-10, briefly

2. Status line format, UTC and Prague via zoneinfo, n/N over the checks that
   ran: as specified and tested on both sides of 25 Oct; a dry run writes
   status_dryrun.txt only (test and dry run). `fpl_publish.checks_failed`:
   a status file written tonight with STATUS FAIL blocks a real commit; a file
   equal to HEAD's (not written tonight) or absent does not. Judged sound:
   see observation 1 for the crash case.
3. fpl_alert.py: open/update on a red run, close on green, a second open one
   closed as a duplicate, nothing on a dry run (run_mode and the workflow `if`),
   permissions exactly contents: write + issues: write (test asserts the list).
   Fake API only; the real API is untested until the real dispatch.
4. 03:17 cron: due unless status.txt is generated at or after the last 21:40
   slot; every later step `if: steps.due.outputs.run == 'true'`; the group
   expression keys on ref/event only, so both crons share `nightly-data`.
5. Retry policy: 429/5xx/network retried with backoff, 403 once, other codes
   and non-JSON never; PAUSE 0.4; SYNC STATS in a `finally`, printed even on
   an early `sys.exit` (test and my reading of main()).
6. Pins verified above.
7. Discovery in the nightly (`TEST_ARGS`), CLAUDE.md change protocol and local
   command updated; the FAST item 1 test walks every top-level .py for imports
   of tools/analysis and sys.path edits, and the workflow's python lines.
8. Hermetic proven above; CLAUDE.md carries the sentence.
9. Counts as in Check 2.
10. As in Check 5.

## Claim 12 (outside S3's scope): mechanism confirmed

`fpl_sync.sync_entries` skips a gameweek's picks once `events.finished` is 1
(`if have and final and final[0]: continue`, line 517 on s3-wip), not
`data_checked`; a row fetched mid-gameweek is never refreshed. On a copy of
fpl.sqlite (4af6abe), stored entry_gw.points minus sum(picks.multiplier x
player_gw.total_points): GW1, 2, 5, 7 equal for all 7 entries; GW3 stored 6-21
lower (all 7 entries), GW4 0-11 lower, GW6 0-2 lower. GW3 is affected too, not
only GW4 and GW6. Rows for GW1-6 have NULL fetched_at_utc, so `entry_points()`
returns None for them and check 22 can only ever reconcile gameweeks fetched
since S2 (GW7 on); it will not surface GW3/4/6. Not fixed, by instruction.

## Observations for the chat (none fails the item)

1. Step 3.1's "FAIL = no data commit" holds for a written STATUS FAIL. If
   `checks.py` itself dies before writing (an exception in `load()`, e.g. an
   unreadable log or a missing function - seen in my first, mis-stubbed
   rehearsal), there is no status file, the nightly step is red ("checks"),
   publish commits as S2 did (gate permitting) and the issue opens with "no
   reports/status.txt". Whether a crash should also block the commit is a
   design choice the ruling does not cover.
2. After a night whose checks FAILed, status.txt is never committed, so the
   03:17 backup run finds it "missing" and does the whole night again (a new
   UTC date, so a new snapshot). Consistent with ruling 4's wording; saying so.
3. Check 1 would FAIL "standings never called" on a night with no finished
   gameweek (sync returns before the league call) - only at a season start.
4. Check 11's test precision (mutation survivor above).
5. s3-wip does not contain d5aa4d2 (the amendment's prereg); the merge does.
6. GW8 deadline 2026-10-23 17:30 UTC; the 30-hour runner freeze starts
   2026-10-22 11:30 UTC; ruling 1's latest merge is Wed 21 Oct 20:00 UTC.

VERDICT: PASS

Reason: the prereg and both rulings were committed before their code; the
suite grows from 386 to 459 by discovery and is green bare, with real data and
stand-in zones (0 skips), in dry-run mode and in a proven identity-free git
environment; the recording path is byte-identical under a frozen clock with
fpl_edge.py untouched; 29 of 30 one-line breaks turn a test red; the dry run
f23d74a reads back as claimed and my re-run of the checks over its content
reproduces every check line; a local rehearsal with a planted failing test
gives STATUS FAIL (28, 29) and no commit while a healthy night commits
status.txt and silences the backup cron; the action pins resolve to v7.0.1 and
v7.0.0; no secret is in any changed file. The observations above are readings
for the chat, not breaches of the prereg.
