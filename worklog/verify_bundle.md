# Verifier report: bundle, re-verification (tools/gw_pass.py; amendment 1 and RULING landing + S11 item 3)

Verifier: Fable 5.1 (claude-fable-5-1), effort high, as `.claude/agents/backtest-verifier.md` says. The agent file was read from disk first; it is identical to the loaded instructions. Run 2026-10-19 07:12-07:32 UTC in `C:\GIT\FPL-b` (branch lane-b, task said f6e4757; the tree moved to `bce4109` during the run: `worklog/SESSION_STATE_B.md` only, the item's files untouched, status clean). Only this file was written in the tree; every other artefact is in the session scratchpad under `vb2/`. The three background planner replays under `tools/out/planner/` and the background suite run were left alone; `tools/planner.py --replay` was not run. The data worktree was only read.

## Summary of the first run (3029867, 06:55-07:15 UTC, kept in git at f6e4757)

The first run verified the single code commit `3029867`: prereg order PASS (0df1443, a01c862, ed1bbb6 before the code); check 1 PASS (newest dated export 2026-10-18, 1084 own/minutes rows for event 8 all made 2026-10-17/18, deadline 2026-10-23 17:30 UTC, 0 rows at/after it); check 2 PASS (571 -> 576 OK in clean checkouts); check 3 PASS (my run on 3029867 equal to the implementer's line for line except the generated time and the header; the implementer's run.txt said commit ed1bbb6, i.e. uncommitted code, not citable); check 4 PASS (S5, S7, S9 the tools' outputs line for line, S8 the planner's block plus four baseline/default lines, side-by-side and keeper line reproduced from the raw log, xp_v2.forecast and minutes_v2.live); check 5 PASS (no runner file touched, data folder and projection log unchanged); check 7 PASS. **Verdict FAIL on check 6 alone**: the pinned captain tie rule (ties by the lower id) survived its inverse mutation. The remedy asked for was one tied-projection hand case; `f6e4757` adds it.

## Scope of this run

The code as of `f6e4757`: `500dae7` (amendment 1 code: norm_name, find_player, why_illegal, value_bb, evaluate_bb, named_plans, CONFIRMED_FT, sqlite_deadline, the NAMED PLANS block) and `f6e4757` (the tie test). `b6637c8` (the merge of master) does not touch `tools/gw_pass.py` or `tests/test_bundle.py` (`git diff --stat b6637c8~1 b6637c8` on those paths: empty); `tools/planner.py` and `tools/chips.py` were last changed on lane-b (7f72141, 5423434, ff8422f), all before 500dae7.

## Prereg order: PASS

`git log` on `prereg/bundle.md`: `60a75df` 2026-10-19 09:00:41 +0200 (amendment 1 verbatim and the pinned definitions, 18 lines, prereg only), `76cbbbb` 09:05:07 (RULING landing + S11 verbatim, item 3, prereg only). First code commit of the amendment `500dae7` 09:10:12; the tie test `f6e4757` 09:14:02. Both prereg commits precede the code. The amendment text, the pinned definitions and ruling item 3 are in `prereg/bundle.md` as verbatim text; those texts are what I checked against.

## Check 1 (point in time): PASS

The bundle still forecasts and records nothing; the named rows are scored by `planner.evaluate` on the same inputs the planner uses live. Independent timestamp audit of the raw CSV (data worktree HEAD `9da6ff1`, nightly 2026-10-18; `projection_log.csv` sha256 `e466c9cd...`, the same bytes as in the first run): 1084 own/minutes rows for event 8, made_at values `2026-10-17T22:04:06/07+00:00` and `2026-10-18T21:58:06+00:00`, rows at or after the GW8 deadline `2026-10-23T17:30:00Z`: 0. Export used: `fpl_export_gw7_2026-10-18.json.gz` (the newest dated export, dated before the deadline; its events[8].deadline_time equals the sqlite value). The P(start) map for the named rows is built from `E.forecasts(log_rows, d_ev)` (the S2 reader: last snapshot before the deadline) with the same expression as `planner.live` lines 253-254. Truncation test and shift probe: no feature or correlation metric; nothing to truncate or shift.

## Check 2 (clean-checkout suite): PASS

`git archive` of `76cbbbb` (before the amendment's code) and `f6e4757` into the scratchpad; `python -m unittest discover -p "test*.py"` in each, no FPL_DATA_DIR:
- before (76cbbbb): Ran 576 tests, OK (skipped=10), rc 0.
- after (f6e4757): Ran 629 tests, OK (skipped=10), rc 0.
The +53 includes master's tests merged by `b6637c8`; the item's own file goes 5 -> 6 (`python -m unittest tests.test_bundle`: 5 OK before, 6 OK after).

## Check 3 (re-run): PASS

`python tools/gw_pass.py --out <scratch>/vb2/run1` from the tree at f6e4757. Its run.txt: commit `f6e475739f0cc0549b02ba2a8f4bac65b1e29477`, modified tracked files 0, 07:15:25-07:16:38 UTC (73 s), `gw8_pass.txt` sha256 `a725b6d3...` (211 lines). Header: `GW PASS  GW8 (deadline 2026-10-23 17:30 UTC) from fpl_export_gw7_2026-10-18.json.gz`.

NAMED PLANS block of my run (free transfers 1 confirmed by Boris, planner estimate 1, no DIFFERS flag):
```
 1    1.55    2.55     0    1.00   +0.6  +0.2  +0.8  +0.5  +0.8  +1.2  Thiago -> Joao Pedro: Thiago -> João Pedro (CHE, £7.8m)
 2    0.00    0.00     0    0.00   +0.0  +0.0  +0.0  +0.0  +0.0  +0.0  roll: roll
 3    2.90    3.90     0    1.00   +1.3  +0.0  +1.1  +1.3  +1.1  +1.2  best single bench upgrade under Bench Boost (...): Slater -> Ayari (BHA, £5.4m)   (GW term 1 under Bench Boost)
```
Against the implementer's reference (`scratchpad/gw_pass2/gw8_pass.txt`, 07:02-07:04 UTC): `diff` shows one differing line, the header's generated time; every section line, every number, identical (within 1e-6 trivially). Provenance caveat as in the first run: the reference's run.txt says commit `60a75df` with 1 modified tracked file, i.e. the amendment's code before it was committed, so by ruling (e) that run may not be cited; my run on `f6e4757` is the citable one. No CHANGELOG entry and no `worklog/cc_*bundle*` report exist yet, so nothing cites it.

Independent recomputation (`vb2/recompute.py`, the planner's functions only, `named_plans` not called), inputs rebuilt with `planner.live`'s own expressions: bank £1.9m, k estimate 1, 264 P(start) rows for GW8, market 285:
- Row (1): our squad has one player normalising to "thiago" (106 Thiago BRE, selling 7.8), the market one "joao pedro" (165 João Pedro CHE, 7.8); legal by my own budget/club/GK+DEF check and by `planner.legal`; `PL.evaluate(((Thiago,), (João Pedro,)), squad, xp_weeks, 0.85, boris, k=1, p_start)` = score 1.546037, gain 2.546037, hits 0, lost 1.000000, gains [0.577, 0.163, 0.805, 0.515, 0.805, 1.157]. Printed 1.55 / 2.55 / 0 / 1.00 / +0.6 +0.2 +0.8 +0.5 +0.8 +1.2: equal.
- Row (2): `PL.evaluate(((), ()), ..., k=1, ...)` = 0 / 0 / 0 / 0, gains all 0: equal.
- Row (3): GW8 XI by own via `chips.xi_and_bench` = Verbruggen, Calafiori, Muharemović, Tarkowski, Thomas, Branthwaite, Groß, Mbeumo, Saka, Haaland, Thiago; bench = Kelleher (GK), Rudoni, Barry, Slater. Over those four as outgoing and every legal same-position market incoming (264 candidates), GW8 valued as sum of 15 + max, GW9-13 by `PL.evaluate`'s gains: best = Slater -> Ayari (BHA, £5.4m) score 2.902621, gain 3.902621, lost 1.0, gains [1.259, 0.004, 1.053, 1.300, 1.057, 1.192]; printed 2.90 / 3.90 / +1.3 ...: equal. The GW8 term under Bench Boost (1.259) differs from the planner's XI valuation of the same swap (0.899): confirmed on the real run. The bench-only restriction matters: the best single swap over all 15 under the same valuation would be Thomas -> De Cuyper (6.09), which the row does not show.

## Check 4 (prereg definitions): PASS

No metric, filter, bootstrap or threshold is pinned ("none; information only"); none appears. Against the pinned definitions of amendment 1 and ruling item 3:
- Row (1) scored by `planner.evaluate` (gw_pass.py line 199) on `planner_inputs` (squad, bank, xp_weeks, market with the planner's own expressions, lines 96-110) and the P(start) map built as in `planner.live` (lines 266-267), with `k = CONFIRMED_FT.get(target, inp["k"])` = 1 for GW8 (line 264); both numbers printed, `[DIFFERS]` when unequal (line 270). Confirmed by the recomputation above. Name matching by `norm_name` (NFKD, combining marks stripped, lower, strip): "Joao Pedro" finds "João Pedro" in the real market; missing or ambiguous -> `MissingInput` -> printed as `missing input: ...` with no score (lines 138-144, 201-202); illegal -> `why_illegal` reason (budget, club cap 3, GK+DEF cap 2, the planner's constants) printed, never scored (lines 195-197). Mutations `ambiguous`, `illegal_scored`, `confirmed_ft` go red.
- Row (2) is `PL.evaluate(((), ()), ...)` with the confirmed k (line 203); refused at the cap with the reason. Mutation `roll_k` red.
- Row (3) searches only `{sub GK} | {three outfield bench}` of `chips.xi_and_bench(squad, xp_weeks[0])` (lines 205-208), same position, not already owned, legal; GW8 via `value_bb` = sum of 15 + max, GW9-13 from `PL.evaluate`'s gains (lines 162-178); the printed line is labelled "(GW term 1 under Bench Boost)". Mutations `bench_all15`, `samepos`, `bb_xi_term` red. See check 6 for the two pinned parts of this row that no test protects.
- Header deadline: `sqlite_deadline(data_dir, target)` reads `select deadline_time from events where id = ?` from `fpl.sqlite` read-only (lines 72-87, 249); direct call on the data folder: GW8 `2026-10-23 17:30:00+00:00`, GW9 `2026-10-31 11:00:00+00:00`, a folder without the database -> None -> the header says "not in fpl.sqlite events". The real header prints `deadline 2026-10-23 17:30 UTC`. The source is as ruled; see check 6 for its test cover.
- Nothing promoted or re-tuned: the named rows are information only and their definitions were pinned in `60a75df` before `500dae7`.

## Check 5 (recording path): PASS

`git diff --stat 76cbbbb f6e4757` restricted to the item: `tools/gw_pass.py`, `tests/test_bundle.py`, `worklog/verify_bundle.md` only; no runner file (the merge's changes are master's landed items, verified there). The nightly-isolation test passes in the clean after-checkout. The data worktree before and after all my runs: `git status` empty, HEAD `9da6ff1`, `projection_log.csv` sha256 `e466c9cd...` (unchanged, equal to the first run), `fpl.sqlite` sha256 `a4aca191...`, every mtime unchanged (00:37:57 +0200). The bundle writes only under `--out`. The recorder was not run; with no runner change the projection log is byte-identical by construction for every model.

## Check 6 (mutation spot-check): FAIL (three surviving mutations on pinned definitions)

Fourteen one-line mutations, each in a fresh scratch copy of the archived `f6e4757` (the tree never touched), `python -m unittest tests.test_bundle` (6 tests):
1. tie rule, own column: `-r["id"]` -> `r["id"]`: RED (the new tie case). The first run's gap is closed.
2. tie rule, xp_v2 column: RED.
3. bench-only restriction: `for out in squad` (all 15): RED.
4. BB first-week term: `gains = list(ev["gains"])` (the planner's XI term instead of the Bench Boost term): RED.
5. same-position rule dropped: RED.
6. ambiguous name accepted (`> 1` -> `> 2`): RED (error).
7. illegal swap scored anyway: RED.
8. `CONFIRMED_FT = {8: 2}`: RED.
9. roll scored with k = 0: RED.
10. **`value_bb`: `sum(projs) + max(projs)` -> `sum(projs)` (the captain dropped from the Bench Boost valuation): SURVIVES, 6 OK.** Observable: on the test's own hand case with the cheap midfielder 202 at 9.0 in GW8 (so he captains under Bench Boost), the original gives gains[0] 15.0, the mutant 8.0. The prereg pins "the sum of the 15 projections plus the captain's, the captain = the highest projection"; no hand case has the incoming bench player as the top projection, so the captain part of the pinned valuation is unprotected. (The real GW8 row is unaffected: Haaland 4.44 remains the captain.)
11. **`evaluate_bb`: `score = gain - 4 x hits - lost` -> `gain - 4 x hits` (the lost-FT value dropped from row (3)'s score): SURVIVES, 6 OK.** Observable: same hand case, score 14.0 original, 15.0 mutant (lost = 1.0 at k = 1). The prereg pins "the same columns (score, gain, hits, lost FT, ...)" for the three rows; the test asserts row (1)'s score against `PL.evaluate` but asserts nothing about row (3)'s score.
12. **`sqlite_deadline`: `return datetime.fromisoformat(...)` -> `return None`: SURVIVES, 6 OK.** And `dl = E.event_deadline(d, target)` (the export instead of fpl.sqlite): SURVIVES. The toy's fpl.sqlite has an events table (tests/test_S4.toy_data) but no test asserts the header's deadline, so RULING landing + S11 item 3 (the deadline from fpl.sqlite events.deadline_time) has no test cover.
13. best-upgrade tie among equal scores: `-inc["id"]` -> `inc["id"]`: SURVIVES. Not pinned (the prereg says "the legal swap with the highest score" and no tie rule), so a note only.

Survivors 10, 11 and 12 each invert a pinned definition or ruling and no test notices; by the item's own precedent (the first run: a surviving mutation on a pinned definition = check 6 FAIL) this is a FAIL. Remedies, each one hand case: (a) in `NamedPlans`, a run with `xp[0][202] = 9.0` asserting row (3)'s gains[0] = 15.0 and score = 14.0 (covers 10 and 11 together; shown red under both mutations above); (b) in `Toy`, assert the header prints the toy's GW8 `events.deadline_time` from its fpl.sqlite (or a direct `sqlite_deadline` test on a temporary database with one events row and on a folder without one), shown red under `return None`.

## Check 7 (secrets): PASS

`git show 500dae7` and `git show f6e4757` on `tools/gw_pass.py`, `tests/test_bundle.py`: no apiKey=, api_key, Authorization, Bearer, sk-, 32+ hex or http(s) URL; the only 32+ character runs are the commit hash line and two test method names. No key-like string appears anywhere examined; nothing to mask.

## VERDICT: FAIL

The amendment's prereg (`60a75df`, `76cbbbb`) precedes its code (`500dae7`); the three named rows reproduce from the planner's own functions on the planner's squad, bank, xP weeks and P(start) with the confirmed 1 FT (row 1 = `PL.evaluate` 1.546037, row 2 the empty plan 0, row 3 the bench-only search with GW8 = sum of 15 + captain, Slater -> Ayari 2.902621, whose GW8 term 1.259 differs from the planner's XI valuation 0.899); illegal and missing names are reported, never scored; the header's deadline is read from `fpl.sqlite` (2026-10-23 17:30 UTC); my run on `f6e4757` equals the implementer's reference on every number; the suite goes 576 -> 629 OK in clean checkouts (test_bundle 5 -> 6); the data folder and projection log are untouched; no secrets; the first run's tie gap is closed (both tie mutations red). The verdict is FAIL on check 6 alone: three one-line mutations on pinned text survive the whole suite: the captain term of the Bench Boost valuation (gains[0] 15.0 -> 8.0 on the hand case), the lost-FT value in row (3)'s score (14.0 -> 15.0), and the header's deadline from `fpl.sqlite` (ruling item 3: `return None` and reading the export both pass every test). Two hand cases close them; re-verify after that. The implementer's reference run (`gw_pass2`, commit 60a75df with 1 modified file) must not be cited; only a run on the final commit may be.
