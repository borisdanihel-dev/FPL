# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** none. S0c is done (verifier PASS) and pushed; waiting for
  Boris.
- **Last pushed commit:** the S0c closing commit, which carries this version
  of the file (`git log -1 -- worklog/SESSION_STATE.md`). Before it: `76d939b`
  (S0c changes), `4dca2b5` (S0c prereg), `01d6d0f` (S0b).
- **Open decisions for the chat** (detail in `worklog/cc_2026-10-17_S0c.md`):
  1. 9d names `deadline_time` in the newest export; the export has no such
     field. Use `fpl.sqlite` `events`, or add it to the export (runner path)?
  2. "One step per session" (`CLAUDE.md` work-item protocol, `BUILD_PLAN.md`
     standing rules) now sits beside "Use the current Claude Code session"
     and 9a. Reword?
  3. Should a ruling-only prereg also carry the full template rows?
- **Next item:** not started. Per `BUILD_PLAN.md` the next step is Step 1
  (D1, data safety). It starts only when Boris says so.
- **Runner freeze window (9d):** not active. Next deadline GW8
  2026-10-23T17:30Z (19:30 Prague); the window opens 2026-10-22T11:30Z
  (13:30 Prague). Source: `fpl.sqlite` `events.deadline_time` (decision 1).
