# Verifier report: bundle, third verification (tools/gw_pass.py; tests/test_bundle.py at 96b9dfd)

Verifier: Fable 5.1 (claude-fable-5-1), effort high, as `.claude/agents/backtest-verifier.md` says. The agent file was read from disk first; it is identical to the loaded instructions. Run 2026-10-19 07:24-07:40 UTC in `C:\GIT\FPL-b` (branch lane-b at `96b9dfd`, status clean before and after). Only this file was written in the tree; every other artefact is in the session scratchpad under `vb3/`. The three background planner replays under `tools/out/planner/` were left alone; `tools/planner.py --replay` was not run. The data worktree was only read; nothing was pulled, synced, recorded or run through the nightly.

## Summary of the first run (code 3029867; report kept in git at f6e4757)

Verified the single code commit `3029867`: prereg order PASS (0df1443, a01c862, ed1bbb6 before the code); check 1 PASS (newest dated export 2026-10-18, 1084 own/minutes rows for event 8 all made 2026-10-17/18, GW8 deadline 2026-10-23 17:30 UTC, 0 rows at or after it); check 2 PASS (571 -> 576 OK in clean checkouts); check 3 PASS (my run equal to the implementer's line for line except the generated time); check 4 PASS (every section reproduced from the tools' own outputs); check 5 PASS; check 7 PASS. **FAIL on check 6 alone**: the pinned captain tie rule (ties by the lower id) survived its inverse mutation; `f6e4757` added the tie case.

## Summary of the second run (code 500dae7 + f6e4757; report kept in git at 96b9dfd)

Verified amendment 1 and RULING landing + S11 item 3: prereg order PASS (`60a75df` 09:00:41 and `76cbbbb` 09:05:07 before the code `500dae7` 09:10:12); check 1 PASS (independent timestamp audit of the raw CSV at data HEAD `9da6ff1`: 0 of 1084 GW8 rows at or after the deadline; the named rows use the planner's own inputs and `E.forecasts`, the last snapshot before the deadline); check 2 PASS (576 -> 629 OK); check 3 PASS (my run on `f6e4757`, run.txt commit f6e4757 with 0 modified files, equal to the implementer's reference on every number; independent recomputation with the planner's functions only: row 1 `PL.evaluate` 1.546037 / gain 2.546037 / lost 1.0, row 2 all 0, row 3 Slater -> Ayari 2.902621 / 3.902621 with GW8 term 1.259 under Bench Boost against 0.899 by the planner's XI valuation); check 4 PASS (every pinned definition located in the code and confirmed by recomputation; the header's deadline read from `fpl.sqlite` events.deadline_time); check 5 PASS; check 7 PASS. **FAIL on check 6 alone**: of fourteen mutations, three on pinned text survived the whole suite: `value_bb` without the captain term (gains[0] 15.0 -> 8.0 on the hand case), `evaluate_bb`'s score without the lost-FT term (14.0 -> 15.0), and `sqlite_deadline` returning None or the export's deadline (ruling item 3 untested). The implementer's reference run (`gw_pass2`, commit 60a75df with 1 modified file) may not be cited; only a run on the final commit may be.

## Scope of this run

`96b9dfd` (09:25:48 +0200) changes `tests/test_bundle.py` (+26 lines; +35 since 500dae7) and `worklog/verify_bundle.md` only (`git show --stat 96b9dfd`). `tools/gw_pass.py` is blob `b00b02ccab2f4bd6ac672c4ec8616031a137c17f` at `500dae7`, at `96b9dfd` and at HEAD: the code is unchanged since my second run. The data worktree is at the same HEAD `9da6ff1` with `projection_log.csv` sha256 `e466c9cd...` and `fpl.sqlite` sha256 `a4aca191...`, both equal to the second run; the inputs are unchanged. Checks 1, 3, 4, 5 and 7 therefore stand on the second run's evidence, restated below with what I re-checked; checks 2 and 6 were redone in full.

## Prereg order: PASS (unchanged)

`git log` on the item's files: prereg commits `0df1443`, `a01c862`, `ed1bbb6`, `60a75df`, `76cbbbb` all precede their code commits `3029867` (08:56:07) and `500dae7` (09:10:12); `f6e4757` and `96b9dfd` are test-only. The rulings (morning 19 Oct item 6, S8 verifier FAIL item (d), amendment 1 with the pinned definitions, landing + S11 item 3) are verbatim in `prereg/bundle.md`; those texts are what the checks are against.

## Check 1 (point in time): PASS (unchanged since the second run)

Code blob and data HEAD identical to the second run (above), so the second run's audit holds: the bundle forecasts and records nothing; 0 of the 1084 own/minutes rows for event 8 are at or after the GW8 deadline `2026-10-23T17:30:00Z`; the export used (`fpl_export_gw7_2026-10-18.json.gz`) is dated before the deadline; no feature or correlation metric, so no truncation test or shift probe applies.

## Check 2 (clean-checkout suite): PASS (redone)

`git archive` of `76cbbbb` (before the amendment's code) and of `96b9dfd` into the scratchpad; `python -m unittest discover -p "test*.py"` in each with `FPL_DATA_DIR` unset:
- before (76cbbbb): Ran 576 tests in 314.1 s, OK (skipped=10), rc 0.
- after (96b9dfd): Ran 631 tests in 331.8 s, OK (skipped=10), rc 0.
The +55 is master's +53 merged by `b6637c8` plus the item's two new hand cases; `tests.test_bundle` alone goes 6 -> 8 (8 OK in the tree at 96b9dfd as well).

## Check 3 (re-run): PASS (unchanged since the second run)

No pre-registered evaluation exists (information only). The tool's code and inputs are byte-identical to the second run (blob `b00b02cc...`, data HEAD `9da6ff1`, export and log hashes equal), so the second run's citable run on `f6e4757` (run.txt commit f6e4757, 0 modified tracked files; `gw8_pass.txt` sha256 `a725b6d3...`, 211 lines; header `GW PASS  GW8 (deadline 2026-10-23 17:30 UTC)`; named rows 1.55/2.55/0/1.00, 0/0/0/0, 2.90/3.90/0/1.00 Slater -> Ayari) and its independent recomputation stand. A run on `96b9dfd` would execute the same bytes; by ruling (e) the implementer's report must cite a run whose run.txt commit equals the final code commit.

## Check 4 (prereg definitions): PASS (unchanged since the second run)

No metric, filter, bootstrap or threshold is pinned ("none; information only"); none appears. The code is unchanged, so the second run's line-by-line mapping of the pinned definitions stands: row 1 by `planner.evaluate` on the planner's inputs with the confirmed 1 FT beside the estimate (`[DIFFERS]` when unequal), names by `norm_name`, missing/ambiguous reported, illegal swaps refused with the reason; row 2 the empty plan with the confirmed k; row 3 over the four bench slots of `chips.xi_and_bench` only, same position, legal, GW8 as sum of 15 plus the captain, GW9-13 by the planner, labelled; the header's deadline from `fpl.sqlite` `events.deadline_time` read-only. The two new tests pin exactly the three previously unprotected terms; nothing was promoted or re-tuned.

## Check 5 (recording path): PASS (unchanged since the second run)

`96b9dfd` touches no runner file (a test file and this report). The data worktree before and after all my runs: `git status` empty, HEAD `9da6ff1`, `projection_log.csv` sha256 `e466c9cd...` and `fpl.sqlite` sha256 `a4aca191...` with mtimes 00:37:57 +0200, all equal to the second run. The nightly-isolation test passes in the clean after-checkout. The recorder was not run; with no runner change the projection log is byte-identical by construction for every model.

## Check 6 (mutation spot-check): PASS (redone)

Each mutation in its own fresh copy of the archived `96b9dfd` (the tree file never touched; `git diff --no-index` against the unmutated copy shows exactly 1 line changed each time), then `python -m unittest -v tests.test_bundle` (8 tests) in that copy. Control, the unmutated copy: 8 OK.

The three survivors of the second run, and the export variant:
1. `value_bb`: `return sum(projs) + max(projs)` -> `return sum(projs)`: **RED**, `NamedPlans.test_bench_boost_value_counts_the_captain_and_the_score_charges_the_lost_ft` FAIL (gains[0] 15.0 expected; the 9.0 incoming is the captain on the hand case; `value_bb` on 15 x 1.0 = 16.0).
2. `evaluate_bb`: `score=gain - PL.HIT * ev["hits"] - ev["lost"]` -> `score=gain - PL.HIT * ev["hits"]`: **RED**, the same test FAIL (score 14.0 expected with lost 1.0 at k = 1).
3. `sqlite_deadline`: `return datetime.fromisoformat(...)` -> `return None`: **RED**, `NamedPlans.test_sqlite_deadline` ERROR (`'NoneType' object has no attribute 'year'`) and `Toy.test_bundle_on_the_toy_export_reports_missing_sections` FAIL: header printed `GW PASS  GW8 (deadline not in fpl.sqlite events)`, expected `(deadline 2026-10-23 17:30 UTC)`.
4. Export variant: `dl = sqlite_deadline(data_dir, target)` -> `dl = E.event_deadline(d, target)`: **RED**, the toy test FAIL: header printed `(deadline 2026-10-28 11:00 UTC)` (the toy export's own GW8 deadline, `2026-10-{20+ev}T11:00:00Z` in `tests/test_S7.py`) against the sqlite row's `2026-10-23 17:30 UTC`. The toy's two deadline sources differ, so the test distinguishes the ruled source from the export.

Two earlier mutations re-spot-checked:
5. Captain tie rule, own column: `(r["proj"], -r["id"])` -> `(r["proj"], r["id"])`: **RED**, `Hand.test_side_by_side_two_projections` FAIL.
6. Bench-only restriction: `for out in [r for r in squad if r["id"] in bench_ids]` -> `for out in squad`: **RED**, `NamedPlans.test_named_swap_roll_and_the_bench_boost_upgrade` FAIL.

Green restored: the unmutated control copy and the tree itself (`tests.test_bundle` 8 OK at 96b9dfd, `git status` clean). The only survivor noted in the second run that remains untested is the best-upgrade tie among equal scores (`-inc["id"]`), which the prereg does not pin ("the legal swap with the highest score"); a note, not a gap.

## Check 7 (secrets): PASS

`git show 96b9dfd -- tests/test_bundle.py worklog/verify_bundle.md` grepped for apiKey=, api_key, Authorization, Bearer, sk-, 32+ hex and http(s) URLs: the only hits are 40-hex commit hashes and the scan vocabulary quoted in the previous report's own check-7 text; the test file diff has none. `tools/gw_pass.py` is the same blob already scanned clean in the second run. No key-like string appears anywhere examined; nothing to mask.

## VERDICT: PASS

The code under verification is byte-identical to the second run (`tools/gw_pass.py` blob `b00b02cc...` at 500dae7, 96b9dfd and HEAD) and the inputs are unchanged (data HEAD `9da6ff1`, log and database hashes equal), so the second run's PASSes on checks 1, 3, 4, 5 and 7 stand; the prereg and its two amendments precede the code. `96b9dfd` adds only the two hand cases asked for, and they close every gap that failed the second run: the Bench Boost captain term, row 3's lost-FT charge, and the header's deadline from `fpl.sqlite` (both the `return None` and the export-deadline variants now go red, the latter because the toy's export and database deadlines differ). Two earlier mutations re-checked red; the control and the tree are green; the suite goes 576 -> 631 OK in clean checkouts (test_bundle 6 -> 8); no secrets; the data worktree is untouched. Reminder for the item's report: cite only a bundle run whose run.txt commit is the final code commit (the implementer's `gw_pass2` run on 60a75df with a modified file is not citable).
