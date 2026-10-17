# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S1 (Step 1, D1). **Migrated and proven; stopped by 9e on
  the secret scan.** The final verifier and the report are not yet done.
  - **Migration (21:58–21:59 UTC, Sat 17 Oct)**, after "nightly 2026-10-17"
    (`26f543a`) landed:
    - tag `pre-data-branch` on `26f543a`;
    - code commit `dddcb92`, a blob-identical copy of `scratch/s1-wip`
      `b738e6d`;
    - `data` = `eeeede6`, orphan, with 103 files byte-identical;
    - migration commit `57abbf1`, deletions only;
    - `C:\GIT\FPL-data` tracks `origin/data`.
  - **Proof dispatch** (run 39073502058, `force_backup` ticked): every step
    green.
    - `data` gained one commit, `e84bee6`, with `fpl.sql` and the `.json.gz`.
    - `master` was unchanged.
    - 4679 log rows, 0 duplicate keys.
    - Release `backup-2026-10-17` holds 2 assets.
    - Both `data` raw URLs return HTTP 200 without sign-in.
  - **Secret scan:** the push-triggered runs were green. Both full-history
    dispatches (runs 39073872326 and 39073916594) failed with "Leaks
    detected". Their findings are in the job summaries and the SARIF
    artifacts, which need a signed-in user. **Waiting for Boris** to share the
    job summaries (the action redacts values), and to confirm which branch
    each run scanned.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`). Before it: `eb3ef1e`.
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
