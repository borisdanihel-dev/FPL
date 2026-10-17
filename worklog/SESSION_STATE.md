# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S1 (Step 1, D1). **Migrated; waiting for the proof
  dispatch, then the final verifier and the report.**
  - **Second pre-check: PASS** (`worklog/verify_S1_pre2.md`).
  - **Migration**, done 21:58–21:59 UTC on Sat 17 Oct, after "nightly
    2026-10-17" (`26f543a`) landed and its run finished:
    - tag `pre-data-branch` on `26f543a`;
    - code commit `dddcb92`, a blob-identical copy of `scratch/s1-wip`
      `b738e6d`, never a merge;
    - `data` = `eeeede6`, orphan, with 103 files byte-identical;
    - migration commit `57abbf1`, deletions only, pushed through the
      pre-push hook;
    - the worktree `C:\GIT\FPL-data` tracks `origin/data`.
  - GitHub holds `master` `57abbf1`, `data` `eeeede6` and the tag. The
    push-triggered secret-scan run was green.
  - **Next:** Boris runs nightly with `force_backup` ticked, and secret-scan
    with branch = master and with branch = data. Then the final verifier,
    `worklog/cc_2026-10-17_S1.md` (final) and the CHANGELOG.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`). Before it: `57abbf1`.
- **Open decisions for the chat:**
  1. Nothing scans `data` automatically. The branch holds no workflow file,
     and the nightly's pushes start no workflow. Each data commit is checked
     by `fpl_gate.py --secrets` before it is made; a full gitleaks scan of
     `data` is a manual run with branch = data.
  2. The first pre-check's report (`worklog/verify_S1_pre.md`, in history
     since `ea7acaa`) quotes the old dummy test fixtures, which are key-like
     strings. Accept them, allowlist them for gitleaks, or redact the current
     copy (history stays)?
- **Next item:** finish S1. Then Step 2 (D2), when Boris says so.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
