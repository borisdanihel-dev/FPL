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
    dispatches (runs 39073872326 and 39073916594) failed, each with the **same
    single finding**:
    - `generic-api-key` in `ea7acaa`, `worklog/verify_S1_pre.md` line 281;
    - this is the first pre-check's quoted dummy test fixture (O8), not a key.
  - **Both runs scanned `master` and `data` together.** gitleaks 8.24.3 (the
    pinned action's version) runs `git log --full-history --all` when given
    no log options, and `fetch-depth: 0` fetches every branch. `ea7acaa` is
    not in `data`, so **`data` is clean**. The `branch` input changes only
    the checkout, not the coverage.
  - **Stopped by 9e:** waiting for the chat's ruling on that finding.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`). Before it: `eb3ef1e`.
- **Open decisions for the chat:**
  1. Nothing scans `data` automatically. The branch holds no workflow file,
     and the nightly's pushes start no workflow. Each data commit is checked
     by `fpl_gate.py --secrets` before it is made; a full gitleaks scan of
     `data` is a manual run with branch = data.
  2. The gitleaks finding (O8, above). Options:
     - a `.gitleaksignore` entry for exactly that commit, file, rule and line
       (recommended);
     - accept red full-history scans;
     - redact the current copy of the report (history keeps the string).
  3. Drop the now-redundant `branch` input of secret-scan.yml, or keep it?
  4. Runner warnings in tonight's runs:
     - `actions/checkout@v4` targets Node 20 and is being forced onto Node 24
       (`setup-python@v5` too);
     - `ubuntu-latest` moves to Ubuntu 26 from 19 Oct.
     Bump the action versions as a follow-up item?
- **Next item:** finish S1. Then Step 2 (D2), when Boris says so.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
