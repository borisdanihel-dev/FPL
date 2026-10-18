# FAST — the fast track (two kinds of work, two lanes)

The chat's ruling, pasted verbatim on 2026-10-18, after S2 closed and before
S3 starts. It is copied into BUILD_PLAN.md as Part E, and items 1, 4, 5 and 6
into CLAUDE.md's work-item protocol.

RULING FAST-TRACK:
Paste this verbatim into prereg/FAST.md and add it to BUILD_PLAN.md as "Part E - Fast track" (CLAUDE.md gets items 1, 4, 5 and 6 in its work-item protocol). Commit before the next item. Applies now; S2 is closed.
1. Two kinds of work. Runner work = anything the nightly workflow runs or imports, or the workflow itself: the fast-lane merge rule, dry run, Boris's real dispatch and the freeze windows apply. Offline work = new modules under tools/ or analysis/ that the runner does not import; they read a local copy of data (C:\GIT\FPL-data, pulled, read-only) and never write to data. Offline items merge to master after tests, verifier PASS and the write guard; no dry run, no dispatch, no freeze restriction. A test proves the nightly imports nothing under tools/ or analysis/.
2. Wiring: an offline tool reaches the nightly only through a wiring item (W1, W2, ...), which is runner work. Batch several tools per wiring item; at most one wiring merge a day; never inside a freeze window.
3. Collect first. W1 lands by Wed 21 Oct 20:00 UTC: record FPL's ep_next nightly as source fpl_ep (Step 4 item 2), and store Odds API snapshots with their fetch time (Step 5's collector only; ODDS_API_KEY reaches the runner here, under S1 amendment 1 item 1). Models that use them come later, offline.
4. Two lanes. Lane A works in C:\GIT\FPL: runner work, wiring items and history items. Lane B works in a second worktree, C:\GIT\FPL-b (lane A creates it with git worktree add, on its own branch): offline items. One Claude Code session per lane, never two sessions in one folder. Each lane keeps worklog/SESSION_STATE_A.md or worklog/SESSION_STATE_B.md. Either lane may merge its own items: fetch, rebase onto master, rerun the full test suite, push; never force. On a CHANGELOG conflict, keep both entries.
5. Tests: new items put their tests in tests/test_<item>.py. S3 switches the nightly gate and local runs to test discovery (test_fpl.py plus tests/). Only lane A edits test_fpl.py.
6. Auto-continue: after an offline item with verifier PASS, a clean write guard and no open decision, the lane starts its next queued item without waiting; it still prints its 15-line summary. It stops on FAIL, WARN, an open decision, a model result that would change a live decision (adoption needs Boris's acceptance in chat), or after 6 items without a chat review.
7. Pre-registration up front: the chat sends the rulings for Steps 4-7 together; each prereg is committed before its item starts and is never edited after any of its evaluation numbers exist.
8. Queues. Lane A: S3, W1, Step 10, W2 (after the GW8 deadline: chip calculator, Free Hit screen, league odds into the report), Step 16, W3, Steps 17-18, W4. Lane B: Step 4 (harness, offline part), Step 7, Step 5 (model and backtest), Step 6, Step 9, Step 8, Steps 11-13, Step 14, Step 15, Step 19.
9. Usage: the verifier runs on Fable for model tests (Steps 4-7, 11-18) and on Opus at xhigh for tooling and wiring items. If the weekly allowance runs low, lane B pauses first.
END RULING

## Amendment 1

Appended verbatim on 2026-10-18.

RULING FAST-TRACK amendment 1:
Append verbatim to prereg/FAST.md and BUILD_PLAN.md Part E. On this account Fable has its own weekly limit, separate from the main allowance. Replace item 9: the verifier runs on Fable for every item; it falls back to Opus at xhigh only if the Fable weekly bar is above 80% before its reset. Lane B's main session runs on Fable (Boris selects it); lane A's stays on Opus 5.5. Each report names the models used.
END RULING
