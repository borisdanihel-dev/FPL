# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S2 (Step 2, D2), in progress on branch `s2-wip` (GitHub
  backup; master untouched). Prereg `9694334`.
  - **Built and tested:** items 1-10, 355 tests green, each new test shown
    red against the code before its fix.
  - **Recording path:** `forecasts()` of the new log equals the baseline
    log row for row, with a frozen clock.
  - **Rehearsal:** nightly and publish against a copy of `data` went
    green: 14 tables, frozen forecasts unchanged.
  - **Waiting for:** Boris's Transfers-page screenshot (A9), to check all
    15 selling prices.
  - **Then:** the verifier pre-check. The merge comes after the 18 Oct
    nightly is confirmed: planned Mon 19 Oct, latest Tue 20 Oct before
    21:00 UTC.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`).
- **Open for the chat:** none yet. The S2 report will list them.
- **Next item:** finish S2.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
