# Session state — lane B (C:\GIT\FPL-b)

Lane B: offline items only (RULING FAST-TRACK, items 1 and 4; `prereg/FAST.md`,
BUILD_PLAN.md Part E). Updated at the end of every item, before the push. A
fresh lane-B session works in `C:\GIT\FPL-b`, reads `CLAUDE.md`,
`BUILD_PLAN.md` and this file, then waits for the next instruction.

- **Worktree:** `C:\GIT\FPL-b` on branch `lane-b`, created by lane A on 18 Oct
  with `git worktree add` from master (`git log -1 lane-b` at creation: the
  commit that adds this file). One Claude Code session here; never a second
  session in this folder, and never lane B's work in `C:\GIT\FPL`.
- **What lane B may change:** new modules under `tools/` or `analysis/` that
  the runner does not import, their tests in `tests/test_<item>.py`, and docs
  (`prereg/`, `worklog/`, CHANGELOG entries). Lane B never edits
  `test_fpl.py` (item 5) or any runner file (anything the nightly runs or
  imports, or the workflow).
- **Data:** a local copy only: `C:\GIT\FPL-data`, pulled, read-only. Never
  write to it. Run `python C:\GIT\FPL-b\fpl_nightly.py --restore` only in a
  scratch copy if working exports are needed; never `fpl_sync.py`,
  `--record`, or `fpl_nightly.py` without `--restore`.
- **Merging an item (item 4):** tests, then the verifier (model per item 9),
  write guard, report, CHANGELOG. Then `git fetch origin`, `git rebase
  origin/master`, rerun the full suite (`test_fpl.py` plus `tests/`, by
  discovery once S3 has landed), and `git push origin HEAD:master`. Never
  force. Branch `lane-b` exists only locally: a rebased branch is never pushed
  to GitHub, so no push ever needs force. On a CHANGELOG conflict, keep both
  entries.
- **No dry run, no dispatch, no freeze restriction** for offline items (item 1).
- **Auto-continue (item 6):** after an item with verifier PASS, a clean write
  guard and no open decision, start the next queued item and still print the
  15-line summary. Stop on FAIL, WARN, an open decision, a model result that
  would change a live decision, or after 6 items without a chat review.
- **Verifier model (item 9):** Fable for model tests (Steps 4-7, 11-18); Opus
  at effort xhigh for tooling items. If the weekly allowance runs low, lane B
  pauses first.
- **Current item:** none yet. The first is Step 4 (harness, offline part).
  Waiting for the chat's rulings for Steps 4-7, which come together (item 7).
  Each prereg is committed before its item starts and never edited after any
  of its evaluation numbers exist.
- **Queue (item 8):** Step 4 (harness, offline part), Step 7, Step 5 (model and
  backtest), Step 6, Step 9, Step 8, Steps 11-13, Step 14, Step 15, Step 19.
- **Items since the last chat review:** 0 of 6.
- **Open for the chat:** none.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_B.md`).
