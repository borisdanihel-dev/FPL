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
- **Models (FAST-TRACK amendment 1, which replaces item 9):** lane B's main
  session runs on Fable (Boris selects it). The verifier runs on Fable for
  every item; it falls back to Opus at xhigh only if the Fable weekly bar is
  above 80% before its reset. Each report names the models used.
- **Current item:** none started. The rulings for Steps 4-7 arrived on
  2026-10-18 (item 7); `prereg/S4.md`, `S7.md`, `S5.md` and `S6.md` are
  written (every template row filled, each ruling verbatim) and pushed on
  `lane-b`. Waiting for the chat's "go"; then S4, S7, S5, S6 in that order
  under auto-continue (item 6). Each prereg is never edited after any of its
  evaluation numbers exist. Open points for the chat before the go are in
  the chat reply of 2026-10-18 (S4 `selected` timing; S5 download approval
  and the undated pre-closing odds; S5/S6 2025/26 exclusions of own, xg,
  fpl_ep; S7 "after normal transfers" without Step 8; S6 penalty inputs
  and the development cut).
- **Queue (item 8):** Step 4 (harness, offline part), Step 7, Step 5 (model and
  backtest), Step 6, Step 9, Step 8, Steps 11-13, Step 14, Step 15, Step 19.
- **Items since the last chat review:** 0 of 6.
- **Open for the chat:** none.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_B.md`).
