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
- **Merging an item (item 4, as RULING lane B branch handling, 2026-10-18,
  verbatim below):** tests, then the verifier, write guard, report,
  CHANGELOG. `lane-b` stays on GitHub as a backup and is only ever
  fast-forwarded; it is never rebased. To land an item on master: create a
  temporary local branch from `origin/master`, bring the item's commits onto
  it (cherry-pick or rebase that temporary branch, never `lane-b`), rerun
  the full suite (`test_fpl.py` plus `tests/`), push `HEAD:master`. Then
  merge `origin/master` into `lane-b` (a merge commit, no rebase) and push
  `lane-b`. No force-push, ever. On a CHANGELOG conflict, keep both entries.

  RULING lane B branch handling:
  lane-b stays on GitHub as a backup and is only ever fast-forwarded; it is never rebased. To land an item on master: create a temporary local branch from origin/master, bring the item's commits onto it (cherry-pick or rebase that temporary branch, never lane-b), rerun the full suite, push HEAD:master. Then merge origin/master into lane-b (a merge commit, no rebase) and push lane-b. No force-push, ever. Record this in worklog/SESSION_STATE_B.md.
  END RULING
- **No dry run, no dispatch, no freeze restriction** for offline items (item 1).
- **Auto-continue (item 6):** after an item with verifier PASS, a clean write
  guard and no open decision, start the next queued item and still print the
  15-line summary. Stop on FAIL, WARN, an open decision, a model result that
  would change a live decision, or after 6 items without a chat review.
- **Models (FAST-TRACK amendment 1, which replaces item 9):** lane B's main
  session runs on Fable (Boris selects it). The verifier runs on Fable for
  every item; it falls back to Opus at xhigh only if the Fable weekly bar is
  above 80% before its reset. Each report names the models used.
- **Rulings:** Steps 4-7 pre-registered on 2026-10-18 (`prereg/S4.md`,
  `S7.md`, `S5.md`, `S6.md`, every template row filled, rulings verbatim);
  RULING lane B go appended as Amendment 1 to each (`94fbc36`). Order under
  auto-continue: S4, S7, S5, S6. No prereg is edited after any of its
  evaluation numbers exist.
- **Current item:** S4 (code `4eab638`, amendment 2 fix `973b3f8` on
  `lane-b`). First verifier run FAIL (club-map leak in the frozen adapter);
  RULING S4 amendment 2 → `tools/hist_pit.py`; second verifier run:
  pending at the time of this commit — the report and CHANGELOG carry
  VERIFIER2 placeholders until it returns. Merge by the branch-handling
  ruling only after PASS; auto-continue (S7, S5, S6) resumes only then.
- **S4 facts the next items use:** `tools/backtest.py` — `Harness(season,
  data_dir, hist_dir)`, `.compare(a, b, filt)`, `.rows(ev, source, filt)`,
  `.decision(ev, source)`; `bootstrap_mean(values, b, seed)`,
  `power_gameweeks(s_d, delta)`, `holm`, `benjamini_hochberg`;
  `rebuild_2526(hist, t)` (bottomup/minutes from rounds < t, with P(cs) and
  P(DEFCON) per fixture, players at their point-in-time club via
  `tools/hist_pit.py` — every 2025/26 replay in S7, S5, S6 goes through
  `canonical_at(hist, g)` / `hist_pit.club_at`); `best_fifteen(cands, budget)`
  (exact legal 15 by a metric). Residuals for S7 come from `Harness.rows()` (actual − forecast).
  Power: starters Spearman s_d = 0.103 (G = 163 gameweeks for Δ = 0.02),
  whole population 0.022 (G = 7), decision metric 5.7 points (G = 50 for
  Δ = 2 points).
- **Historical data:** `C:\GIT\FPL-b\historical\2025-26` (gitignored copy
  of `C:\GIT\FPL\historical\2025-26`, vaastav, verified 2026-09-14).
- **Queue (item 8):** Step 4 (harness, offline part), Step 7, Step 5 (model and
  backtest), Step 6, Step 9, Step 8, Steps 11-13, Step 14, Step 15, Step 19.
- **Items since the last chat review:** 1 of 6 (S4).
- **Open for the chat:** the S4 fix ruling (report, Decisions 0 and 1).
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_B.md`).
