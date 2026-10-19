# Session state — lane B (C:\GIT\FPL-b)

**Closed 19 Oct (the lanes merged).** This file is lane B's record and is
no longer updated; the one state file is `worklog/SESSION_STATE_A.md`.

Lane B: offline items only (RULING FAST-TRACK, items 1 and 4; `prereg/FAST.md`,
BUILD_PLAN.md Part E). Updated at the end of every item, before the push. A
fresh lane-B session works in `C:\GIT\FPL-b`, reads `CLAUDE.md`,
`BUILD_PLAN.md` and this file, then waits for the next instruction.

## HANDOVER — lanes merge (RULING S6b acceptance + lanes merge, 2026-10-19 ~12:00 UTC; verbatim in `prereg/S6b.md`)

Lane B's last task. `lane-b` is pushed and left as is; `C:\GIT\FPL-b` and
its `tools/out` stay untouched (the replay and test outputs with their
`run.txt` live there until the next landing's provenance check). Whoever
continues works from `C:\GIT\FPL` (lane A's folder) after merging or
landing `lane-b`; `lane-b` is only ever fast-forwarded, never rebased.

### Where everything stands

| item | state | on master | report |
|---|---|---|---|
| S4, S7, S5, S6, S9 | landed 2026-10-19 (`6bd378b`) after the green dry run | yes | `worklog/cc_2026-10-19_landing.md` |
| S8 planner | a screen (ruling d); final-code replay +2.90 [−12.74, +18.40] FAIL; no-hit line +9.00 [−4.74, +22.56]; re-verified PASS | no (lane-b) | `worklog/cc_2026-10-19_S8.md` |
| S12 minutes v2 | not adopted; the keeper lock prints in the bundle | no | `worklog/cc_2026-10-19_S12.md` |
| S13 DEFCON v2 | shelved; revisit at the GW19 checkpoint | no | `worklog/cc_2026-10-19_S13.md` |
| S11 shares | PASS, adopted as the xg-half share input of xp_v2 | no | `worklog/cc_2026-10-19_S11.md` |
| provenance | `tools/provenance.py`; every tool writes `run.txt` into `tools/out/<tool>/` | no | `worklog/cc_2026-10-19_landing.md` (the proposed CLAUDE.md line) |
| bundle | `tools/gw_pass.py` with amendment 1; verified PASS (3 runs) | no | `worklog/cc_2026-10-19_bundle.md` |
| S6b | PASS (+0.358 [+0.126, +0.592] per squad per gameweek); **accepted** for XI and captain from GW8 | no | `worklog/cc_2026-10-19_S6b.md` |

`lane-b` is 91 commits ahead of `origin/master` (`4b4ffce`), 49 files;
master is ahead of lane-b by lane A's S16 part 1, W2 prereg and state
commits (not merged into lane-b; nothing of lane B's depends on them).
Lane-b's own files beyond master: `tools/provenance.py`, `gw_pass.py`,
`shares.py`, `xp_v2_replay.py`, `defcon.py`, `minutes_v2.py`, `planner.py`;
`tests/test_S8.py`, `test_S11.py`, `test_S12.py`, `test_S13.py`,
`test_S6b.py`, `test_bundle.py`, `test_provenance.py`; the provenance
wiring and per-tool output folders in `tools/backtest.py`, `chips.py`,
`league.py`, `odds_lambda.py`, `xp_v2.py`; `tests/test_S5.py` (the toy
schema) and `tests/test_S9.py` (run.txt in the CLI test); the preregs,
reports, verifier reports and CHANGELOG entries. Every tool suite and the
discovery suite were green at `841c4bc` (646 tests) and the tools' suites
after.

### The accepted decision rule (ruling 1 and 3)

- From GW8: XI and captain by **xp_v2 as tested in S6b** — P(start) ×
  (E_xg + E_bl) / 2 + P(sub) × E[pts | sub], with S11's shares in the xg
  half and S5's bottomup_lambda in the bottomup half, P(start) from the
  current minutes model. `own` keeps being recorded nightly and is printed
  beside xp_v2 at every deadline; both are compared weekly in grading.
  Vetoes on hard facts as before.
- **If the live forecast cannot use S11's shares by the GW8 pass, own picks
  GW8.** Today the live xp_v2 (`tools/xp_v2.py --forecast`, the bundle's
  "own v xp_v2" section) reads the recorded `xg` rows, not S11's shares:
  the S6b allocation exists only in the replay (`tools/xp_v2_replay.py`,
  `Replay.xp_v2`). A live "xp_v2 as tested" needs the S11 allocation on the
  2026/27 data (S11's `shares.Season` is 2025/26-only; the live inputs are
  the export's players, `fpl.sqlite`'s fixtures and the odds snapshot for
  λ_team, the 2024/25 priors from `historical/2024-25/`) — an open item.
- **Revert rule, fixed now:** at the GW10 checkpoint, if the live paired
  decision metric over GW8–10 (the realised points of the XI and captain
  chosen by xp_v2 minus those chosen by own, the S6b metric on our real
  squad) has its 90% upper bound below 0, own returns.

### Open items, in order

1. **S6c, the safety check (ruling 2):** `own_rebuilt` = live own's formula
   (`fpl_edge.project`: the form term from the last four gameweeks per 90
   shrunk by `SHRINK` to the positional prior, the minutes-reliability
   scaling, the FDR adjustment 1 + (3 − FDR) × 0.12 from the file's
   end-of-season FDR — `fixtures.csv` `team_h_difficulty` /
   `team_a_difficulty`), status and chance taken as available for both
   sides; the same 50 squads, metric and bootstrap as S6b
   (`tools/xp_v2_replay.py` has the machinery: add an `own_rebuilt`
   projection beside `own_proxy`). The switch is suspended for GW8 only if
   the 90% upper bound of (xp_v2 − own_rebuilt) is below 0. Also print
   2026/27 GW5–7, recorded own against xp_v2 as tested, as information
   (recorded own from the projection log; xp_v2 as tested needs the live
   allocation of item 2, or is printed as "not available" — never
   substituted). Prereg first (`prereg/S6c.md`, the ruling verbatim).
2. **The live "xp_v2 as tested" forecast in the bundle:** S11's allocation
   on 2026/27 (λ_team from the odds snapshot via `odds_lambda`, shares from
   the season's rows in `fpl.sqlite`/the export, the 2024/25 priors by name
   and club, k as measured) feeding `xp_v2`'s xg half; printed beside own
   in the bundle's "own v xp_v2" section and in the keeper line. Without it
   by Thursday's pass, own picks GW8 (ruling 1).
3. **The bundle runs:** Thursday 2026-10-22 about 18:00 and Friday
   2026-10-23 morning (deadline 17:30 UTC): `git -C C:\GIT\FPL-data pull
   --ff-only`, then `python tools/gw_pass.py` (from the lane's folder; the
   data folder defaults to `C:\GIT\FPL-data`); the file and its `run.txt`
   are committed under `worklog/gw_pass/gw8/` (copy
   `tools/out/gw_pass/gw8_pass.txt` and `run.txt` there with a dated
   name). The bundle prints the baseline as the default where the planner
   differs, the three named rows (Thiago → João Pedro, roll, the best
   Bench-Boost bench upgrade), 1 FT confirmed, the keeper line.
4. **The next landing:** S8, S11, S12, S13, S6b, S6c, the bundle and the
   CLAUDE.md provenance line (the text is in
   `worklog/cc_2026-10-19_landing.md`), as the Monday landing was done: a
   temporary branch from `origin/master`, lane-b's commits after `6bd378b`
   (the merge commits `b6637c8` and `2970141` are merges of master and are
   skipped), CHANGELOG = master's plus lane-b's later entries (the scripted
   resolution in the session scratchpad `land.py` / `merge_master.py`
   pattern: master's file plus lane-b's entries from the "S8:
   rolling-horizon transfer planner" heading on), the discovery suite, a
   green dry run (tests/ changes), outside 9d; before it, the provenance
   check of every recorded number (each tool's `run.txt` commit must be
   its item's final code; the outputs under `tools/out/<tool>/` were all
   produced on the final code: `s8_*` at `7f72141`, `shares` at `7f72141`,
   `gw_pass` at `96b9dfd`, `xp_v2_replay` at `37c6493`; the tie-test
   commit `bb7dd78` and `f6e4757` are tests only).
5. **Step 14** (and 15, 19) need rulings before any prereg.

### How to run what lane B built (from the lane's folder, data read-only)

- `python tools/gw_pass.py` → `tools/out/gw_pass/gw<N>_pass.txt` (75 s).
- `python tools/xp_v2_replay.py --test` → `tools/out/xp_v2_replay/` (13 s;
  needs `historical/2025-26/players_raw.csv`, `historical/2026-27/
  game_config.json` and `elements_positions.csv` — lane A's downloads,
  copied with their recorded SHA-256 `412ce017…`, `a72a9908…`, `ac3dc891…`;
  and `historical/2024-25/` for S11's priors, `5bbbcba6…`, `ce696e18…`,
  `d10a6db8…`).
- `python tools/shares.py --test`, `tools/defcon.py --test`,
  `tools/minutes_v2.py --test | --live`, `tools/planner.py [--replay]
  [--no-hits] [--buffer 3.0]` (a replay is 4 h 20 min), `tools/chips.py`,
  `tools/league.py`, `tools/odds_lambda.py --live`, `tools/xp_v2.py
  --forecast`, `tools/backtest.py --report`. Each writes `run.txt` beside
  its output.
- Tests: `python -m unittest discover -p "test*.py"` from the folder
  (hermetic; `FPL_DATA_DIR` unset). The mutation scripts lived in the
  session scratchpad only; each report lists its mutations.

### Lessons recorded for the next session

- Never put repository text in an unquoted heredoc (backticks are shell
  command substitution): write patch scripts with the file-writing tool,
  or quote the delimiter. One state commit (`1a2a967`) lost its code
  names that way and was repaired in `b4ce107`.
- Never run mutations while another process is starting from the same
  files; never cite a run whose `run.txt` commit is not the item's final
  code (the S8 lesson).
- Boris's rulings are pasted verbatim and checked with `diff`.

---

Everything below is the session history that led here (kept for the record; the handover above governs).

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
- **Resumed 2026-10-18 18:50 UTC** (Boris: "resume"). S4 was pushed to
  master as `70f026d` at 18:49 UTC (temporary branch rebased onto S3's
  `1af9644`, CHANGELOG conflict kept both entries, 491 tests OK by
  discovery). **RULING lane B landing arrived two minutes later: S4 does not
  land tonight.** Master was reverted at 18:51 UTC by one revert commit
  `32bf218` (no history rewrite): its tree is byte-identical to `1af9644`,
  the tree the S3 dry run tested, so tonight's nightly runs S2 + S3 only.
  S4 stays complete on `lane-b` (and in master's history under the revert).
- **Monday landing (RULING lane B landing, verbatim below):** after tonight's
  nightly has finished and outside 9d: temporary branch from
  `origin/master`, `git revert 32bf218` (restores the S4 files exactly), then
  S7 and whatever else is clean, full suite locally, push the landing
  branch, ask Boris for the dry-run click, land only on green. **Until
  then never merge `origin/master` into `lane-b`** (it would carry the
  revert and delete S4 from lane-b); after the landing, merge master into
  lane-b as usual. Dry runs are capped at 6 a day; batch items.
- **S7:** complete on `lane-b` (`8e8583b`): failed replay bar accepted by
  RULING S7 result; amendment (real fixtures to GW19, comparators) verified
  PASS. Lands with S4 on Monday.
- **Current item:** S5 built (`tools/odds_lambda.py`, `tests/test_S5.py`,
  odds CSVs `df5d5fa`, code `01be62b`). **Both pre-registered parts pass**
  (Brier +0.0153 [+0.0098, +0.0214]; the 2026/27 condition on two
  gameweeks). Verifier PASS (Fable 5.1; a 1c shift-probe WARN cleared by 1a/1b, reported
  to the chat), write guard clean. RULING S5 result (`4abc716`): accepted;
  `bottomup_lambda` adopted as an S6 input; Part C tie-break change recorded
  (**edit the Part C line in BUILD_PLAN.md at the landing**). Amendment
  built (`fa05534`): the `condition_2627` toy test and `--live` for the
  Thursday deadline pass (W1's snapshots; reader shape to confirm when W1
  lands). Verifier on the amendment FAILed on check 3 only (console
  encoding); RULING S5 amendment fix (`9ea56c4`) → `tools/console_utf8.py`
  called by the three mains, cp1252 subprocess tests (`313bcb0`).
  Verifier rerun **PASS** (Fable 5.1), write guard
  clean. S5 complete on `lane-b`.
- **S6:** complete on `lane-b` (`f25fe4d`): cut GW6, validation empty,
  INCONCLUSIVE by construction; re-run `python tools/xp_v2.py --validate
  --cut 6` at the GW10 and GW19 checkpoints; the chat rules on the metric
  power before GW10.
- **S9:** complete on `lane-b` — fixed under RULING S9 decisions (`629da70`,
  `5aceef2`), re-verified **PASS** (Fable 5.1), write guard clean. For lane
  A: S2b (Tuesday) and the verifier's note that `standings` "event 2" rows
  are mislabelled GW3 snapshots.
- **S8:** built (`tools/planner.py`, `tests/test_S8.py`; code `51520ef`,
  `7f8ba52`, `22a179c`; 7 tests, mutations 19 of 19 red). **The replay
  FAILS its bar**: +7.68 [−6.58, +22.06] against ≥ +10 with a positive lower
  bound (`tools/out/s8_run1/`; run 2 on the final code and the verifier's
  own run confirm). **Verifier FAIL** (Fable 5.1, `worklog/verify_S8.md`): the
  recorded replay is the first commit's, whose candidate generator
  dropped 30–45% of the distinct pairs; the verifier's replay of the
  final code gives +2.90 [−12.74, +18.40]; my "run 2 byte-identical"
  claim was false (written 32 s after run 1). The lane stopped on the
  FAIL (mode e); a rerun of the replay on the final code was started
  into the session scratchpad (`s8_run3`, about four hours) and is
  recorded only under the ruling. Nothing adopted; the item is not done.
- **S12:** complete on `lane-b` (`tools/minutes_v2.py`, `tests/test_S12.py`;
  prereg rows `3b94269`; code `005531a`, `d8a2ee5`, `e68bf70`; 7 tests,
  mutations 20 of 20 red). **The pre-registered test FAILS on (a)**: Brier
  +0.0017 [−0.0001, +0.0033] against ≥ 0.01 with a positive lower bound;
  (b) MAE −0.0042 and (c) keeper mismatches 76 → 56 pass. Verifier PASS
  (Fable 5.1), write guard clean. Nothing adopted; the decision is parked
  below. Report `worklog/cc_2026-10-19_S12.md`.
- **S13:** complete on `lane-b` (`tools/defcon.py`, `tests/test_S13.py`;
  prereg rows `b456909`; code `385bd90`; 7 tests, mutations 22 of 22
  red). **The pre-registered test FAILS on both bars**: Brier comparator −
  v2 −0.0188 [−0.0248, −0.0128] (v2 worse than the hit-rate rule) and 1 of
  10 deciles within 5 points. Verifier PASS (Fable 5.1), write guard
  clean. Nothing adopted; the decision is parked below. Report
  `worklog/cc_2026-10-19_S13.md`.
- **Monday 19 Oct, morning (RULING morning 19 Oct; RULING S8 verifier FAIL; RULING landing + S11; Boris's bundle amendment 1):**
  - **Landed:** `landing-2026-10-19` (S4 via the revert of `32bf218`, S7, S5, S6, S9, the Part C rule 2 tie-break bullet, a header-only
    `overrides.csv`, the landing report `worklog/cc_2026-10-19_landing.md` with the provenance table) - dry run green (590 tests,
    record OK, the WARN is the dry run's own odds skip), fast-forwarded to `master` at `6bd378b` 07:12 UTC; `origin/master` merged
    into `lane-b` (`b6637c8`, a merge commit). The temporary worktree is removed.
  - **Provenance (ruling e):** `tools/provenance.py`; every tool writes `run.txt` into its own folder `tools/out/<tool>/`; every recorded
    test and replay number of S4, S5, S6, S7, S9, S12, S13 reproduces byte for byte on the final code; two live screens moved with the
    data (in the landing report). The proposed CLAUDE.md line is in the landing report.
  - **S8:** done. The verifier's FAIL was corrected under RULING S8 verifier FAIL: the final-code replay `s8_run3` (+2.90
    [-12.74, +18.40], bar FAIL) and the exploratory lines (buffer 3.0 +0.48; no hits +9.00 [-4.74, +22.56], 0 hits) recorded in
    a new CHANGELOG entry beside the first run's (marked as the buggy generator's), with `run.txt` at `7f72141`; the five test
    gaps closed; the lost-FT reading in the prereg; re-verified **PASS**. The planner stays a screen, printed beside the baseline
    in the bundle. Report `worklog/cc_2026-10-19_S8.md` (the record section).
  - **S11:** complete and **adopted** (RULING landing + S11 item 2) as the share input to the xg half of `xp_v2`; not a decision input
    on its own; it enters `xp_v2`'s past-season test, ruled once Step 10 lands. Verifier: FAIL on check 6 (a test gap) then PASS on
    the re-run; both metrics pass their Holm-adjusted bars (goals +0.0061, assists +0.0043). Report `worklog/cc_2026-10-19_S11.md`.
  - **Bundle** (`tools/gw_pass.py`): complete with amendment 1 (1 FT confirmed; Thiago -> Joao Pedro, roll, the best Bench-Boost bench
    upgrade beside the top 5) and the sqlite deadline; verifier PASS on the third run (two rounds of test gaps closed), write guard
    clean; report `worklog/cc_2026-10-19_bundle.md`. Thursday: `git -C C:\GIT\FPL-data pull`, then `python tools/gw_pass.py`
    (morning, from Wednesday night's snapshot; again after Thursday's nightly) -> `tools/out/gw_pass/gw8_pass.txt` with `run.txt`.
  - **Items since the chat review (restarted at 0 by RULING morning 19 Oct):** S11, bundle = 2 of 6; the S8 corrections are a
    continuation of S8.
  - **S6b:** complete on `lane-b` (`tools/xp_v2_replay.py`, `tests/test_S6b.py`; code `37c6493`, the tie test `bb7dd78`):
    **PASS** - xp_v2 beats own_proxy by +0.358 points per squad per gameweek, 90% [+0.126, +0.592], +12.2 per squad per season
    on 2025/26 re-scored under the 2026/27 rules; verifier PASS (Fable 5.1), write guard clean. **Stopped for Boris's acceptance
    (ruling 5)**: the chat would propose switching XI and captain to xp_v2 from the next deadline, own printed beside it, the
    live GW7-10 numbers checked at the GW10 checkpoint. Report `worklog/cc_2026-10-19_S6b.md`.
  - **Queue:** nothing without Boris: the S6b acceptance; Thursday's bundle (a lane-B session Thursday morning and after the
    nightly: `git -C C:\GIT\FPL-data pull`, then `python tools/gw_pass.py`); Steps 14, 15, 19 need rulings.
- **Old S9 state (superseded):** S9 built (`tools/league.py`, `tests/test_S9.py`, code
  `1dc2263` + `2d56fd5`; prereg `98ebddd` with RULING Step 9 verbatim).
  Descriptive; pooled σ_d 18.6 [10.5, 20.6], every rival inside the
  variance line. **Verifier FAIL** on a data finding: `entry_gw.points` is
  provisional on settled gameweeks (the runner's sync stops re-fetching
  at `finished = 1`); the tool's mechanics passed. **Stopped** for the
  rulings (report, Decisions 0: lane A sync fix and backfill; the tool's
  behaviour on pre-lockdown rows; three textual deviations). Then rerun
  S9 and re-verify. Next in the queue after that: Step 8 — needs its ruling.
- **Monday landing (RULING Step 9):** after W1's real dispatch is green,
  S4 + S7 + S5 + S6 (+ S9 if verified) on one landing branch from
  `origin/master`: `git revert 32bf218`, cherry-pick the lane-b commits
  after `70f026d`, edit the BUILD_PLAN Part C line (RULING S5 result point
  2), full suite, push the branch, ask Boris for the dry-run click; land
  only on green, outside 9d, then merge master into `lane-b`.
- **S7 facts for later items:** `chips.live(data_dir)`, `chips.replay(
  hist_dir)`, `induction(v_bb, v_fh, first, last, chips)`, `Replay`
  (origin-t forecasts on `canonical_at`), `sample_squads(seed=7)`.
- **Overnight mode (Boris's instruction of 2026-10-19 ~00:30 UTC, verbatim
  below): ask nothing until about 08:00 Prague; park anything needing Boris
  here under "Needs Boris (morning)"; lane-b only, no landings, merges or
  dispatch requests; the usual gates; stop on FAIL, WARN, an open decision
  or after 6 items; one report block per finished item in the morning.**
- **Needs Boris, in order (19 Oct, after the landing):**
  1. The CLAUDE.md provenance line (proposed in `worklog/cc_2026-10-19_landing.md`): lane A edits CLAUDE.md, or a ruling for lane B.
  2. S8 after the replays: the recorded numbers and the re-verify (reported when they land, about 10:40 UTC).
  3. Thursday's bundle: who runs it (a lane-B session Thursday morning and after the nightly), and whether the Thursday files are
     committed for the record (e.g. `worklog/gw8_pass_*.txt`) or stay in `tools/out/gw_pass/` (gitignored).
  4. S12 and S13 stay as ruled (not adopted / shelved); the keeper lock prints in the bundle.

  Boris is asleep until about 08:00 Prague. Until then:
  - Ask nothing. Anything that needs me (a click, a download approval, a decision) gets parked in your SESSION_STATE file with the exact question, and you move on to the next queued item that doesn't need it.
  - Work on your own branches only. Nothing goes to master except preregs and your SESSION_STATE file. No landings, merges or dispatch requests.
  - Keep the usual gates: prereg first, tests, mutations, Fable verifier, write guard. Stop on FAIL, WARN, an open decision, or after 6 items without a chat review.
  - If you hit a usage limit, stop cleanly and record where you are.
  - Morning: one report block per finished item, then your list of what needs me, in order.
  END

- **Standing rule (RULING pause, verbatim below):** once S3 is on master
  the nightly runs `tests/` by discovery and a failing test fails the gate,
  so any push to master that adds or changes a file under `tests/` is
  runner path under 9d: never between 21:00 UTC and the end of that
  night's nightly, never within 30 hours of a deadline
  (`events.deadline_time`; next: GW8 Fri 23 Oct 17:30 UTC, so the window
  closes Thu 22 Oct 11:30 UTC). Lane B's tests stay hermetic: no network,
  no `C:\GIT\FPL-data`, no real git identity. `tests/test_S4.py` complies:
  toy data in temp folders; one test reads the repo's gitignored
  `historical/2025-26` copy and is skipped where it is absent (the runner).

  RULING lane B landing (S3 is now on master):
  S4 does not land tonight. Tonight is the first scheduled run with S2 and S3 together plus the Sunday backup, and the nightly now runs tests/: a test that fails on the Linux runner would block tonight's record. Continue S7 on lane-b (it may build on S4).
  From now on, a landing that adds or changes anything under tests/ needs a green dry run of the temporary landing branch first (it runs the whole suite on the runner), and lands outside 9d. Batch items into one landing where you can (dry runs are capped at 6 a day). First landing: Monday after tonight's nightly has finished, S4 plus whatever is clean by then; push the landing branch and ask me for the dry-run click.
  END RULING

  RULING pause (Boris away, connection unreliable):
  Finish the step you are in, then stop at a clean checkpoint. Land nothing on master and start no new item until I say resume. Commit work in progress; push lane-b only as a fast-forward (no rebase, no force). A verifier run cut off by the connection is recorded as interrupted (not FAIL) and rerun on resume. Update worklog/SESSION_STATE_B.md, then wait.
  Standing rule from now on: once S3 is on master, the nightly runs tests/ by discovery (fpl_nightly.py TEST_ARGS) and a failing test fails the gate. So any push to master that adds or changes a file under tests/ counts as runner path under 9d: never between 21:00 UTC and the end of that night's nightly, and never within 30 hours of a deadline. Your tests stay hermetic: no network, no C:\GIT\FPL-data, no real git identity.
  END RULING
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
- **Items since the last chat review:** 3 of 6 (S11, bundle, S6b; RULING morning 19 Oct reviewed S9, S8, S12, S13).
- **Open for the chat:** the S9 FAIL rulings (report, Decision 0); RULING Step 8; the S9 report's Decision 1 (σ_d in Part C rule 1); the GW8 chip call (S7, Thursday); S4 Decisions 1 (S6 primary metric power) and 3 (the frozen 2026-09-14 2025/26 bottomup results used end-of-season clubs); the Monday landing (S4 + S7?).
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_B.md`).
