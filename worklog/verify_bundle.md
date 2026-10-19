# Verifier report: bundle (tools/gw_pass.py, the Thursday deadline-pass bundle)

Verifier: Fable 5.1 (claude-fable-5-1), effort high, as `.claude/agents/backtest-verifier.md` says. The agent file was read from disk first; it is identical to the loaded instructions. Run 2026-10-19 06:55-07:15 UTC in `C:\GIT\FPL-b` (branch lane-b). Only this file was written in the tree; every other artefact is in the session scratchpad under `verify_bundle/`.

**Scope.** The item as committed in `3029867` (the single code commit: `tools/gw_pass.py`, `tests/test_bundle.py`). While this verification ran, the lane moved on: `60a75df` (bundle amendment 1, prereg only), `76cbbbb` (RULING landing + S11, item 3: the header's deadline from `fpl.sqlite`, prereg only), `ddcceda` (S11), and at 07:08 UTC edits to `tools/gw_pass.py` and `tests/test_bundle.py` (the amendment's code, committed at 07:10 UTC as `500dae7`). All of my tree-based runs predate 07:08 UTC; the suite, the bundle run and the mutations were run on `git archive` copies of `ed1bbb6` and `3029867`, so nothing below depends on the edited tree. The amendment and ruling item 3 are **not verified here**; they need their own verifier run after their code is committed.

## Prereg order: PASS

`git log` on `prereg/bundle.md`: `0df1443` 08:01:24 +0200 (RULING morning 19 Oct, verbatim, items 3 and 6 present), `a01c862` 08:22:03 (RULING S8 verifier FAIL, verbatim, item (d) present), `ed1bbb6` 08:43:21 (template rows: the six sections pinned in order, acceptance tests, "none" for metric/bootstrap/threshold). First and only code commit `3029867` 08:56:07. All three prereg commits precede the code. Both rulings are in the prereg as verbatim text; the rulings I checked against are those texts.

## Check 1 (point in time): PASS (not applicable beyond the sources; the inputs checked)

The bundle forecasts nothing and records nothing; it composes `odds_lambda.live`, `chips.live`, `planner.live` (+ `planner.baseline_plan`), `league.report`, `xp_v2.forecast` + `chips.xi_and_bench`, and `minutes_v2.live`, each of which passed its own verification. What I checked:
- Input selection: `chips.newest_export` picks the newest dated export by (gw, date): `fpl_export_gw7_2026-10-18.json.gz` (the two dated gw7 exports are 10-17 and 10-18; data worktree HEAD `9da6ff1`, nightly 2026-10-18). The log is read through `fpl_edge.read_log` + `fpl_edge.forecasts` (the S2 reader: last snapshot made before the deadline; a row at/after the deadline is never read).
- Timestamp audit (raw CSV, independent of the reader): 1084 `own`/`minutes` rows for event 8; made_at values are only `2026-10-17T22:04:06/07Z` and `2026-10-18T21:58:06Z`; the GW8 deadline is `2026-10-23T17:30:00Z` in both `fpl.sqlite` and the export's events; rows at/after the deadline: 0. Export date 2026-10-18 <= deadline date. The deadline is in the future at run time, so no later data can exist.
- Truncation test and shift probe: no feature or correlation metric is produced; nothing to truncate or shift.

## Check 2 (clean-checkout suite): PASS

`git archive` of `ed1bbb6` (before) and `3029867` (after) into the scratchpad; `python -m unittest discover -v -p "test*.py"` in each:
- before: Ran 571 tests, OK (skipped=10)
- after: Ran 576 tests, OK (skipped=10) — +5 = `tests/test_bundle.py` (3 hand tests, the toy bundle, the nightly-isolation test).
`python -m unittest tests.test_bundle` in the tree (at 3029867, before the 07:08 edits): 5 tests OK. The isolation test (nightly modules import nothing under tools/ or gw_pass) passes.

## Check 3 (re-run): PASS

No pre-registered evaluation exists (information only). I re-ran the tool itself: `python tools/gw_pass.py --out <scratch>/bundle` on `3029867`. Its `run.txt`: commit `3029867da007e00b31fb538ff3e3a7d29ca034fb`, modified tracked files 0, 06:58:14-06:59:33 UTC (79 s), output `gw8_pass.txt` sha256 `1ad2760b...` (205 lines).

Against the implementer's reference (`scratchpad/gw_pass/gw8_pass.txt`; its `run.txt`: commit `ed1bbb6`, 06:49:55-06:51:10 UTC, i.e. run on the then-uncommitted code): every section line identical; the only differences are the generated time and the header's deadline (`deadline unknown` in the reference, `deadline 2026-10-23 17:30 UTC` in mine, from the export's `events.deadline_time` via `fpl_edge.event_deadline`). So the reference run's commit does not equal the final code (ruling (e)) and its header is not what `3029867` prints; it must not be cited. Nothing in the tree or CHANGELOG cites it (no bundle entry in CHANGELOG.md yet). My run is the citable one for `3029867`.

Key numbers of my run (GW8, from fpl_export_gw7_2026-10-18): baseline `Branthwaite -> De Cuyper (BHA, £5.2m)`; planner top plan `Thomas -> De Cuyper (BHA, £5.2m)`; planner no hits `Thomas -> De Cuyper`; `DEFAULT = the baseline; the planner's top plan is the note (RULING S8 verifier FAIL item d)`; own captain Haaland 4.44, xp_v2 captain Haaland 5.76, 8 of 15 slots differ, the XI differs; keepers Verbruggen own P(start) 1.00 / lock 0.95, Kelleher 1.00 / 0.95.

## Check 4 (prereg definitions): PASS

The prereg pins no metric, filter, bootstrap or threshold ("none; information only, no bar, no adoption"); none appears in the code or output, so nothing was promoted or re-tuned. The six sections appear in the pinned order with the pinned content (below). Both rulings the item cites are in `prereg/bundle.md` verbatim.

### The sections, (a)-(f) as tasked

(a) Each section is the tool's own output, unmodified. Each tool run standalone the same way into its own scratch folder (`planner.py` live, `chips.py` live, `league.py`, `odds_lambda.py --live`, `minutes_v2.py --live`, `xp_v2.py --forecast`; all rc 0, each with run.txt) and compared line by line (blank lines ignored):
- S5: 24 lines, identical set, same order, nothing added.
- S7: 33 lines, identical set, same order, nothing added.
- S8: the planner's 18 lines appear as one contiguous block equal to `planner_live.txt`; the bundle adds exactly 4 lines (BASELINE, planner top plan, planner no hits, the DEFAULT line).
- S9: 65 lines, identical set, same order, nothing added.
- Sections 5 and 6 are the bundle's own composition; verified under (c) and (d).

(b) Baseline the default where they differ: `baseline_note` compares `planner.plan_key(top)` with the baseline's (outs, ins) id sets on the same 15, not the hit count; in the real run they differ and the DEFAULT line prints; the hand test covers agreement, a differing hit plan, a differing free plan, and `k=0` -> the baseline rolls. The baseline runs on the same pool: `rank_plans` builds it with `build_pool(market, squad_ids, xp_weeks, decay)`, the same call `baseline_note` makes with `PL.DECAY`; `planner_inputs` rebuilds squad, bank, k and the market with `planner.live`'s own expressions.

(c) Side-by-side XI and captain: own column recomputed from the raw log's last `own` snapshot (2026-10-18T21:58:06Z, 15 of 15 squad values equal to `chips.own_week_points` to 1e-9) and `chips.xi_and_bench` -> same XI, same bench order (sub keeper at slot 12, outfield by projection), captain = max projection in the XI (Haaland 4.44, unique). xp_v2 column recomputed from `xp_v2.forecast` (264 rows, 15 of 15 covered): all 15 values match at 2 dp, XI and bench order equal, captain Haaland 5.76, 8 slots differ. The tie rule in code (`max(xi, key=(proj, -id))`) is the lower id; see check 6.

(d) Keeper line: own P(start) for Verbruggen (109) and Kelleher (82) read from the raw CSV's last `minutes` snapshot for event 8 = 1.0 and 1.0, printed 1.00/1.00; the lock from `minutes_v2.live` directly = 0.95/0.95 (the standalone print shows only the top 40 movers, which these are not). A missing recorded row is `None` -> printed `n/a` (`own_ps.get(id)` with no default; hand test asserts None; mutation to a 0.0 default goes red).

(e) Missing input / failed tool reported, never substituted, bundle continues: `section()` catches the tools' MissingInput classes (`missing input: ...`) and any other exception (`section failed: <type>: <msg>`) and returns None. On the S4/S7 toy export: S5, S9, OWN v XP_V2 and the keeper line print `section failed: OperationalError/AttributeError ...`, S7 and S8 print fully (baseline + DEFAULT line), rc 0, run.txt written. A data folder with no export at all returns rc 2 with "MISSING INPUT ... nothing is substituted".

(f) run.txt by `tools/provenance.Run`: commit, modified-tracked count, start/end UTC, duration, output sha256 (confirmed equal to my own sha256 of gw8_pass.txt).

## Check 5 (recording path): PASS

`git diff --stat ed1bbb6 3029867` touches only `tools/gw_pass.py` and `tests/test_bundle.py`; no runner file (fpl_edge, fpl_nightly, fpl_sync, test_fpl.py untouched). The nightly imports nothing under tools/ (isolation test). Across all my runs the data worktree is unchanged: `git status` empty, HEAD `9da6ff1`, every file's mtime and size identical before and after, `projection_log.csv` sha256 `e466c9cd...` before and after. The bundle writes only under `--out`. The recorder was not run (the runner is the only writer); with no runner change the projection log is byte-identical by construction for every model.

## Check 6 (mutation spot-check): FAIL (one surviving mutation on a pinned definition)

Six one-line mutations, each in a fresh scratch copy of the archived `3029867` (the tree file was never touched), `python -m unittest tests.test_bundle`:
1. keeper_line: missing own row -> 0.0 instead of None: RED (test_keeper_line_and_plan_text).
2. baseline_note: `agree = bool(top)` (ignores the plan): RED (2 tests).
3. side_by_side: xp_v2 captain taken from own's XI: RED (test_side_by_side_two_projections).
4. **side_by_side: captain ties by the higher id (`-r["id"]` -> `r["id"]`): SURVIVES (5 tests OK).**
5. section(): a failed section swallowed silently: RED (toy test).
6. planner.baseline_plan: a baseline move with no free transfer: RED.
Same result from the tree copy taken before the 07:08 edits. The implementer's eight claimed mutations (scratchpad `mutate_bundle.py`) do not include line 4; their 8/8 claim is consistent with my results. Mutation 4 inverts the prereg's pinned captain rule ("ties by the lower id") and no test notices: every hand case has distinct projections, so the suite cannot tell the pinned rule from its opposite. The code is right by inspection and the real GW8 output has no tie (Haaland unique), but the acceptance test "the side-by-side XI on a hand case (two projections, two XIs, two captains)" does not cover the pinned tie. By the S11 precedent (a surviving mutation = check 6 FAIL, closed by a test and a re-verify), this is a FAIL. Remedy: one tied-projection case in `Hand.test_side_by_side_two_projections` (two XI players with equal max projection; assert the lower id is captain for both columns), shown red under mutation 4.

## Check 7 (secrets): PASS

`git show 3029867 -- tools/gw_pass.py tests/test_bundle.py` greps clean for apiKey=, api_key, Authorization, Bearer, sk-, 32+ hex; no long token-like strings (the only 32+ character runs are test method names). No URL in either file.

## Masking
No key-like string appears in any file or output examined; nothing to mask.

## VERDICT: FAIL

Everything measurable about `3029867` holds: the prereg (both rulings verbatim, the six sections pinned) precedes the code; the bundle reads only the newest dated export (2026-10-18) and log rows made 2026-10-17/18, all before the GW8 deadline of 2026-10-23 17:30 UTC; S5, S7 and S9 are the tools' outputs line for line, S8 is the planner's block plus exactly the four baseline/default lines with the baseline marked the default where it differs; the side-by-side XI, bench, captains and the keeper line reproduce from the raw log, `xp_v2.forecast` and `minutes_v2.live`; failed sections are reported and the pass continues; run.txt is written; the suite goes 571 -> 576 OK in clean checkouts; the data folder and projection log are untouched; no secrets. The verdict is FAIL on check 6 alone: the prereg pins "captain = the highest projection in the XI, ties by the lower id", and a mutation to ties-by-the-higher-id survives every test, so the pinned rule is unprotected. One tied-projection hand case closes it; re-verify after that (and note that the reference run in the scratchpad was made on uncommitted code with run.txt commit `ed1bbb6` and a different header, so only a run on the final commit may be cited; the amendment 1 code, now `500dae7`, is outside this verdict).
