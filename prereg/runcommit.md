# runcommit — real runs record their code commit

Committed before any code for this item. Runner work (CLAUDE.md, Fast track
item 1): dry run, Boris's real dispatch and the freeze windows apply.

## The ruling (Boris's message verbatim)

Rulings, Tue 3 Nov night.
1. Yes: the test for a captain with no player_gw row (= 0 minutes). Put it on w3-wip so it lands with W3 on Sat 7 Nov; tonight's runner change is used, and Wednesday stays clear before the GW10 freeze.
2. Yes: real runs record their code commit (log line, status header, commit message), as dry runs do. Runner change: prereg first, then schedule it in the international break after W3 and the S8c landing (Mon 9 Nov or later).
3. CHIPS reading the previous night's archived export is fine as is: chips are only revealed after a deadline. If the section header doesn't already name the export's date, add that with W3.
Wednesday: no runner change. Resume Step 16 parts 3-4 on s16b-wip (offline). Thursday: the GW10 bundle on Boris's paste.

## The finding

- W2's final verifier (`worklog/verify_W2_final.md`) had to establish which
  code a real run used from the push history and the test count. Neither
  the log, the status file nor the commit message says.
- What a dry run records today (master `7841ef0`): only the commit message
  carries the commit, `dry run <date> <ref> <7 characters> [skip ci]`
  (`fpl_publish.py:177-179`, from `GITHUB_SHA`). A dry run's log header
  (`fpl_nightly.py:202-206`) and status line (`checks.status_line`) carry
  none, the same as a real run's.
- So "as dry runs do" holds for the commit message. **The log line and the
  status header are new for both kinds of run.** This item gives both kinds
  all three.

## The design, pinned before the code

- **The commit:** `GITHUB_SHA`, its first 7 characters, as in the dry-run
  message. The nightly's master checkout has no `ref:`, so `GITHUB_SHA` is
  the commit it checks out.
- **No `GITHUB_SHA`** (a run outside Actions): never a substitute.
  - The log line says `code commit: unknown (no GITHUB_SHA)`.
  - The status field says `code ?`, as the repo size says `? MB`.
  - The commit message omits the field, as the dry-run message collapses an
    empty one.
- **The log line:** `code commit: <7>` in the run header of
  `logs/run_<date>.log`, after `using:`.
- **The status header:** ` | code <7>`, the last field of the first line of
  `reports/status.txt` and `reports/status_dryrun.txt`.
  - It goes last, so the fields before it do not move.
  - `status_time`, and `fpl_publish.py`'s `STATUS FAIL` test, read only the
    fields before it. `tests/test_S3.py`'s exact-line test changes with it.
- **The commit message:** `nightly <date> <7> [skip ci]`. Nothing parses
  the message; `[skip ci]` stays.
- **Nothing else moves:** no forecast, no section, no check result, no
  `projection_log.csv` row. The recording path is proved unchanged by
  diffing the log under a frozen clock, as the change protocol requires.

## Acceptance tests

- `tests/test_runcommit.py`, hermetic:
  - all three records with `GITHUB_SHA` given, for a real run and a dry run;
  - all three with `GITHUB_SHA` absent: the log and status words above, and
    the message without the field;
  - `status_time` and the `STATUS FAIL` test still read the longer line.
- Each record shown red when its change is removed; mutations 1 per record
  and 1 for a substitute value (the commit read from anywhere but
  `GITHUB_SHA`).
- A push to `dry/runcommit`: `data-dryrun-runcommit`'s commit message, log
  and `reports/status_dryrun.txt` all carry the pushed commit's 7 characters.
- The whole suite before and after, bare and with the data; the verifier;
  the write guard.
- Boris's real run on master: the data commit's message, `logs/run_<date>.log`
  and `reports/status.txt` all carry master's 7 characters.

## The schedule

- No code before W3 (Sat 7 Nov) and the S8c landing (Sun 8 Nov) are on
  master. W3 changes `fpl_nightly.py` and `checks.py`, so this item builds
  on them.
- Monday 9 Nov or later, in the international break.
  - GW11's deadline is Sat 21 Nov 11:00 UTC, so its freeze starts Thu 19 Nov
    05:00 UTC. The push must land before that.
  - Never between 21:00 UTC and the end of that night's nightly.
- It starts only on Boris's word (Session operating mode a).
