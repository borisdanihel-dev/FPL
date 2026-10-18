# Session state — lane A (C:\GIT\FPL)

Lane A: runner work, wiring items and history items (RULING FAST-TRACK, item
4; `prereg/FAST.md`, BUILD_PLAN.md Part E). Updated at the end of every item,
before the push. A fresh lane-A session reads `CLAUDE.md`, `BUILD_PLAN.md` and
this file, then waits for the next instruction.

- **Monday 19 Oct, first task** (RULING S3 dispatch result): confirm
  tonight's scheduled run - the data commit, status.txt with checks 9 and
  26 now active instead of SKIP, release backup-2026-10-18, and what the
  03:17 UTC backup run did. Then ask Boris for three Actions-log lines of
  the 18:45 dispatch (due, backup, failure issue).
- **Current item:** W1 (wiring: fpl_ep and the Odds API collector), built on
  `w1-wip` (`fec087a`, GitHub backup); prereg `prereg/W1.md` (`7efc2b2`).
  - Tests 459 -> 478; green bare, hermetic, and with the data and zones.
  - 15 of the 19 W1 tests are red on master's runner code; 18 of 18
    mutations red.
  - The frozen four record byte-identically; the export only gains
    `ep_next`.
  - Local rehearsal on a data copy: `RECORD OK fpl_ep 668`; without a key
    `ODDS SKIPPED` gives check 30 WARN; `GATE OK` with 15 tables.
  - Next (Mon 19 Oct, after the first task): the dry run of `w1-wip` (the
    first real Odds API call: credits, totals coverage), read back, the
    verifier pre-check, tag `pre-W1`, merge (at most one wiring merge a
    day, never in a freeze window), Boris's real dispatch. Lands by Wed
    21 Oct 20:00 UTC.
  - Open for the chat (W1):
    1. 4 credits a call (h2h,totals x uk,eu), about 120 a month plus 4
       per dry run; the plan said about 60.
    2. A failed or keyless odds night is a WARN (check 30), not a FAIL.
    3. An export without `ep_next` is RECORD FAIL fpl_ep, so check 29
       FAILs and the night commits nothing. Keep that strict?
    4. `fpl_ep` records every player FPL gives an ep_next for, not the
       frozen models' population.
    5. `ODDS_API_KEY` must exist as a repository secret; it cannot be
       seen from here (a missing one shows as ODDS SKIPPED).
  - Nothing on master after 21:00 UTC on 18 Oct.
- **S3: done** (18 Oct). Merged `1af9644` (tag `pre-S3` = `3ce5a08`); real
  dispatch `e8629f0` STATUS WARN 24/25, ruled green (the WARN is check 3, a
  new FPL player); final verifier PASS (`worklog/verify_S3.md`). Report
  `worklog/cc_2026-10-18_S3.md`. Open S3 decisions are listed there.
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
- **Queue (FAST-TRACK item 8):** W1 (by Wed 21 Oct 20:00 UTC: fpl_ep and the
  Odds API collector), Step 10, W2 (after the GW8 deadline), Step 16, W3,
  Steps 17-18, W4.
  - **Step 10 addition** (RULING Step 10 addition, 18 Oct, verbatim; also in
    BUILD_PLAN.md Step 10): once lane B has merged tools/hist_pit.py, re-measure the earlier 2025/26 findings that used fpl_hist.canonical_from_vaastav (the horizon test H=6, the F test, backtest_2025-26 and concentration_2025-26) with the point-in-time club map. Descriptive only: report old against new side by side; no rule changes unless a pre-registered test calls for one.
- **Models (FAST-TRACK amendment 1):** lane A's main session stays on Opus
  5.5; the verifier runs on Fable for every item, falling back to Opus at
  xhigh only if the Fable weekly bar is above 80% before its reset. Each
  report names the models used.
- **Dry runs used:** 18 Oct: 4 of 6.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_A.md`).
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
