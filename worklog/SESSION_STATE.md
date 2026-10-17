# Session state

Updated at the end of every item, before the push (`CLAUDE.md`, "Session
operating mode"). A fresh session reads `CLAUDE.md`, `BUILD_PLAN.md` and this
file, then waits for the next instruction.

- **Current item:** S1 (Step 1, D1). **Stopped by 9e: the verifier pre-check
  FAILed** (`worklog/verify_S1_pre.md`). Nothing has changed since the verdict.
  - Part 0 is pushed (`53383fd`), and so is Amendment 1 (`a2bd8ef`, prereg).
  - Amendment 1 items 1–6 are built on the **local** branch `scratch/s1-wip`
    (`84a1bb0`, unpushed), with 288 tests green and every mutation red.
  - Rehearsal 2 (throwaway clones, bare origin) passed end to end:
    - the migration moved 99/99 files byte-identical;
    - the hook accepted the deletions and rejected a planted data file;
    - the nightly exited 0 and the publish pushed only to `data`, with
      `fpl.sql` written.
  - Rehearsal 2 also found a hook bug, now fixed on the branch and
    test-pinned: worktrees share the hook, and the hook looked for its script
    in the data worktree.
  - GitHub still holds only `master` = `a2bd8ef`. No runner change was pushed
    and nothing is migrated.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE.md`). Before it: `a2bd8ef`.
- **Open decisions for the chat** (from the pre-check, detail in
  `worklog/verify_S1_pre.md`):
  1. **F1:** the staged-secret scan reads `.json.gz` as compressed bytes, so a
     key inside a gz export passes. Proposed fix: decompress `*.gz` before
     matching, with a test shown red then green.
  2. **F2:** the local command pattern fails on a fresh data worktree (no
     working export; `fpl_edge.py` and the frozen `p1_eval.py` cannot read
     `.json.gz`). Proposed: `python C:\GIT\FPL\fpl_nightly.py --restore`
     restores the working exports (plain JSON, ignored on `data`) into the
     current folder, with no change to `fpl_edge.py` or `p1_eval.py`. Fix the
     `CLAUDE.md` test claim with it. Alternatives: a gz-aware loader in
     `fpl_edge.py` (record path), or plain dated copies alongside the gz.
  3. **F3:** "projection log tables": `fpl.sqlite` has none, and
     `projection_log.csv` may shrink legitimately before a deadline.
     Proposed: the gate fails if any row for a gameweek whose deadline has
     passed (`events.deadline_time`) is missing or changed against the last
     commit. Or accept `price_history` only. Also F11: should other
     append-only tables (`player_gw`, `entry_gw`, `picks`, `transfers`,
     `chips`) join `GROW_ONLY`?
  4. **F4 / F8:** key-shaped test fixtures. gitleaks may flag the 32-hex
     dummy key, and a failing secret test prints `API_KEY=abc` into the run
     log, which would trip the scan and lose that night's prices. Proposed:
     assemble the fixtures at runtime and label subtests by index.
  5. **F9:** add `fpl_publish.py` and `fpl_gate.py` to the 9d runner-path list
     in `CLAUDE.md`?
  6. **Plan notes for the migration**, unless the chat objects:
     - code goes onto `master` as one byte-identical commit, never a merge
       (a merge over the overnight nightly trips the hook: F5);
     - `pre-data-branch` is tagged at the pulled `master` before the code
       commit, so the rollback text holds (F6);
     - `.gitattributes` on `data` says `*.sqlite binary`, as the plan does
       (F7);
     - a Sunday dispatch means that evening's run skips the backup as
       "exists" (F10).
- **Next item:** S1 continues after the chat rules on 1–5. Then fix and test
  on `scratch/s1-wip`, rerun the pre-check, and migrate on Boris's go (all
  before 23:00 Prague). Then Step 2 (D2).
- **Runner freeze window (9d):** not active. Next deadline GW8
  2026-10-23T17:30Z (19:30 Prague); the window opens 2026-10-22T11:30Z
  (13:30 Prague). Source: `fpl.sqlite` `events.deadline_time`.
