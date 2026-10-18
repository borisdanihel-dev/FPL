# Session state — lane A (C:\GIT\FPL)

Lane A: runner work, wiring items and history items (RULING FAST-TRACK, item
4; `prereg/FAST.md`, BUILD_PLAN.md Part E). Updated at the end of every item,
before the push. A fresh lane-A session reads `CLAUDE.md`, `BUILD_PLAN.md` and
this file, then waits for the next instruction.

- **Current item:** S3 (Step 3, D3), ruling in `prereg/S3.md`. Started 18 Oct
  on Boris's instruction after RULING FAST-TRACK, including FAST-TRACK item 5
  (test discovery: `test_fpl.py` plus `tests/`). Branch `s3-wip`. Merge by the
  fast lane by Wed 21 Oct 20:00 UTC, else after the GW8 deadline.
- **S2: closed** (RULING FAST-TRACK: "S2 is closed"). On master since `9b4a462`
  and `50abf60`; final verifier PASS (`worklog/verify_S2.md`); report
  `worklog/cc_2026-10-18_S2.md`. Revert tags `pre-S2` (`1cddca9`) and
  `pre-S2-backup` (`2bee604`). Two S2 checks still fall to lane A:
  1. Tonight's scheduled nightly (18 Oct, 21:40 UTC). It confirms S1 and S2
     together and should make `backup-2026-10-18`. If it fails, revert to
     `pre-S2` first, then investigate.
  2. After GW7 locks down (Tue 20 Oct or later): the GW7 before/after
     calibration comparison, reported with the GW7 grading (S2 amendment 2,
     point 1). If it differs, revert to `pre-S2` first.
- **Open for the chat:**
  - reverting to `pre-S2` after the GW8 deadline would grade GW8's several
    snapshots together (S2 final decision 1);
  - `CLAUDE.md` items b and g still name `worklog/SESSION_STATE.md`, which is
    now an index pointing to the two lane files.
- **Queue (FAST-TRACK item 8):** S3, W1 (by Wed 21 Oct 20:00 UTC: fpl_ep and the
  Odds API collector), Step 10, W2 (after the GW8 deadline), Step 16, W3,
  Steps 17-18, W4.
- **Dry runs used:** 18 Oct: 2 of 6.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_A.md`).
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
