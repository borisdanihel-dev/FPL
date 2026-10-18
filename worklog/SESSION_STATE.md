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
    `worklog/verify_S2_a2.md`.
  - **Dry run of `s2-wip` on GitHub** (1 of 6 on 18 Oct): green. Read back
    from `data-dryrun` `705ac42` against `data` `e84bee6`; see the report.
  - **Report:** `worklog/cc_2026-10-18_S2.md` (interim, amendment 1 and
    amendment 2 sections).
  - **Waiting for:**
    1. Boris's real dispatch on master, dry_run unticked (amendment 2,
       point 6). Then read back its `nightly 2026-10-18` commit on `data`. Its
       backup step must log "BACKUP skipped: a manual dispatch backs up only
       with force_backup ticked"; tonight's scheduled run makes
       `backup-2026-10-18`.
    2. Tonight's scheduled nightly (21:40 UTC). Per point 10 it confirms S1
       and S2 together; if it fails, revert to tag `pre-S2` first, then
       investigate.
    3. The final verifier (S2 ruling 5), then the final report, changelog
       and this file.
    4. After GW7 locks down (Tue 20 Oct): the GW7 before/after calibration
       comparison, reported with the GW7 grading (amendment 2, point 1). If
       it differs, revert to `pre-S2` first.
  - **Pending until a scheduled night has run (point 8):** the cron start;
    the Sunday backup made by the scheduled run (tonight).
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`).
- **Open for the chat:** none (the amendment-2 decisions are ruled).
- **Next item:** S3, ruling in `prereg/S3.md` (verbatim). It starts only
  after S2 is merged and its real dispatch is green. It merges by the fast
  lane by Wed 21 Oct 20:00 UTC, else after the GW8 deadline.
- **Dry runs used:** 18 Oct: 2 of 6.
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
