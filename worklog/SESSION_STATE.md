# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** none. **S1 is done: final verifier PASS**
  (`worklog/verify_S1.md`; report `worklog/cc_2026-10-18_S1.md`), pushed.
  Waiting for Boris.
  - Data lives on `data`; the local worktree is `C:\GIT\FPL-data`. The local
    command pattern is in `CLAUDE.md`, and starts with
    `python C:\GIT\FPL\fpl_nightly.py --restore`.
  - The pre-push hook is installed in `C:\GIT\FPL`.
  - The local branch `scratch/s1-wip` (`b738e6d`, never pushed) remains;
    see decision 5.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`). Before it: `81e2efa`.
- **Open decisions for the chat** (detail in `worklog/cc_2026-10-18_S1.md`):
  1. First live runs to check:
     - tonight's nightly, 18 Oct 21:40 UTC, the first on `ubuntu-24.04` and
       the first scheduled run in the new layout;
     - the Sunday 04:23 UTC secret scan.
  2. Docs that lag:
     - BUILD_PLAN.md Step 1.6 still says "gitleaks locally";
     - CLAUDE.md line 9 says "committed back";
     - `secret-scan.yml` is still on `ubuntu-latest`.
  3. The verifier block's masking sentence (the S1 closing ruling).
  4. A manual dispatch that straddles a deadline fails the gate (O5). Accept?
  5. Delete the local `scratch/s1-wip`?
- **Next item:** none started. Per `BUILD_PLAN.md`, Step 2 (D2), when Boris
  says so.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
