# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** none. **S1 and S1-closing are done** (verifiers: S1 PASS on
  Opus; S1-closing PASS on Fable 5.1, effort high), and pushed. Waiting for
  Boris.
  - Data lives on `data`; the local worktree is `C:\GIT\FPL-data`. The local
    commands start with `python C:\GIT\FPL\fpl_nightly.py --restore`.
  - The pre-push hook is installed in `C:\GIT\FPL`.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`). Before it: `69b360d`.
- **Before Step 2 (S1 closing ruling, point 7):**
  - **Pending:** confirm the first scheduled nightly on the new layout, a
    "nightly 2026-10-18" commit on `data` with the gate green (21:40 UTC, 18
    Oct), and report it.
  - **Done:** the Sunday secret scan, run 39098380500, success, 04:48Z.
- **Open decisions for the chat:** none.
- **Next item:** Step 2 (D2) when Boris says so, after the confirmation
  above. Model and effort per `CLAUDE.md` item h: Opus 5.5, effort xhigh.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
