# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S2 (Step 2, D2) with amendments 1 and 2. **Merged to
  master** on 18 Oct at 12:19 UTC as `9b4a462`: one commit, ten files
  blob-identical to `s2-wip` `08f29fb`. Tag **`pre-S2`** = `1cddca9` is the
  revert target. Prereg `9694334`, Amendment 1 `b1d691e`, Amendment 2 `adf3d32`,
  Decisions `d2cf781` (CLAUDE.md item e names the `data-dryrun` force-push
  exception).
  - **Backup fix (decisions, point 2):** merged at 12:48 UTC as `50abf60`, two
    files blob-identical to `s2-backup` `3ae739b`. Tag `pre-S2-backup` =
    `2bee604`. Verifier PASS (`worklog/verify_S2_backup.md`); dry run 2 of 6
    green (`data-dryrun` `b4efd66`).
  - **Verifier pre-checks, all PASS** (Fable 5.1, high):
    `worklog/verify_S2_pre.md`, `worklog/verify_S2_a1.md`,
    `worklog/verify_S2_a2.md`, `worklog/verify_S2_backup.md`.
    **Final verifier PASS:** `worklog/verify_S2.md`.
  - **Proof dispatch:** green, `data` `4af6abe` ("nightly 2026-10-18"),
    read back. There is no backup release, as a dispatch without
    `force_backup` must not make one.
  - **Dry run of `s2-wip` on GitHub** (1 of 6 on 18 Oct): green. Read back
    from `data-dryrun` `705ac42` against `data` `e84bee6`; see the report.
  - **Report:** `worklog/cc_2026-10-18_S2.md` (with the amendment, decisions
    and final sections).
  - **Still pending (by the rulings' own schedule):**
    1. Tonight's scheduled nightly (21:40 UTC, 18 Oct). Per point 10 it
       confirms S1 and S2 together; it should make `backup-2026-10-18`. If
       it fails, revert to tag `pre-S2` first, then investigate.
    2. After GW7 locks down (Tue 20 Oct or later): the GW7 before/after
       calibration comparison, reported with the GW7 grading (amendment 2,
       point 1). If it differs, revert to `pre-S2` first.
  - **Pending until a scheduled night has run (point 8):** the cron start;
    the Sunday backup made by the scheduled run (tonight).
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`).
- **Open for the chat:** reverting to `pre-S2` after the GW8 deadline
  would grade GW8's several snapshots together (final decision 1 in
  `worklog/cc_2026-10-18_S2.md`).
- **Next item:** S3, ruling in `prereg/S3.md` (verbatim). Its start
  condition holds (S2 merged, real dispatch green); it starts when Boris
  says so. It merges by the fast lane by Wed 21 Oct 20:00 UTC, else after
  the GW8 deadline.
- **Dry runs used:** 18 Oct: 2 of 6.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
