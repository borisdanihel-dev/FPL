# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S2 (Step 2, D2), built on branch `s2-wip` (`04acd7d`,
  GitHub backup; master has no S2 code). Prereg `9694334`.
  - **Built and tested:** items 1-10, 355 tests green, each fix red on
    master's code; the verifier's 31 mutations red.
  - **A9:** 15 of 15 selling prices match the Transfers page.
  - **Verifier pre-check:** PASS (Fable 5.1, high), `worklog/verify_S2_pre.md`.
  - **Interim report:** `worklog/cc_2026-10-18_S2.md`, with the unbackfilled
    counts (25,214 / 3,883 / 42).
  - **Waiting for:** tonight's scheduled nightly (18 Oct 21:40 UTC): the
    `nightly 2026-10-18` commit on `data`, gate green, `backup-2026-10-18`.
  - **Then:** merge Mon 19 Oct as one byte-identical commit (latest Tue 20 Oct
    before 21:00 UTC, else after the GW8 deadline), Boris's proof dispatch,
    the final verifier, the final report.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`).
- **Open for the chat:** the four decisions in `worklog/cc_2026-10-18_S2.md`.
- **Next item:** finish S2.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
