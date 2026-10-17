# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S1 (Step 1, D1), **stopped at a consistent point**
  (ruling point 8).
  - Part 0 is done and pushed (`53383fd`).
  - D1 is built, tested (281 tests) and rehearsed on the **local** branch
    `scratch/s1-wip` (`ca8821c`). It is not pushed and nothing is migrated:
    `master` and the nightly are unchanged.
  - The verifier has not run. The migration plan is in
    `worklog/cc_2026-10-17_S1.md`.
- **Last pushed commit:** the S1 stop-point commit, which carries this version
  of the file (`git log -1 -- worklog/SESSION_STATE.md`). Before it: `53383fd`
  (Part 0) and `3318b08` (prereg).
- **Open decisions for the chat** (detail in `worklog/cc_2026-10-17_S1.md`):
  1. The secret value is checked wherever `ODDS_API_KEY` is set; the runner
     gets the key only from Step 5. Accept, or pass it to the commit step now?
  2. The gate's "table list unchanged" rule versus Step 2's `automatic_subs`:
     an override, a column instead of a table, or one red night?
  3. Is the full-database `prices.sql` dump accepted?
  4. Is the hook allowing deletions on `master` (needed for the migration)
     accepted?
  5. `FPL_DATA_DIR` read by `fpl_nightly.py` only (steps run in the data
     folder): accept?
  6. Boris clicks Run workflow for the proof dispatch. May gitleaks be
     downloaded, or will Boris install it?
  7. Migrate on Sunday 18 Oct before 23:00 Prague?
- **Next item:** continue S1 (the migration, the dispatch, gitleaks, the
  verifier) once Boris says so. Then Step 2 (D2).
- **Runner freeze window (9d):** not active. Next deadline GW8
  2026-10-23T17:30Z (19:30 Prague); the window opens 2026-10-22T11:30Z
  (13:30 Prague). Source: `fpl.sqlite` `events.deadline_time`.
