# verify_S0 — backtest-verifier report

- **Item:** S0 (BUILD_PLAN.md Step 0: protocol, verifier, small fixes). A descriptive / data-pipeline item: `prereg/S0.md` has no pass/fail metric, so checks 1, 2, 5, 6 and 7 apply, plus the prereg's acceptance tests 1-6. Checks 3 and 4 do not apply.
- **Commits (`git log 07d10a1..master`):** `037b7dd` protocol files and `prereg/S0.md`; `5828d1e` code (`fpl_edge.py`, `test_fpl.py`, `watchlist.txt`). `07d10a1` precedes the item: it is docs-only (`BUILD_PLAN.md`, `CLAUDE.md`, `CLAUDE_fable chat.md`, `FPL_PLAN.md`).
- **Verified:** 2026-10-17, Python 3.14.7, `PYTHONIOENCODING=utf-8`. Clean checkouts were temporary git worktrees under the session scratchpad (`vs0\before` = `07d10a1`, `vs0\after` = `5828d1e`, plus `vs0\red` and `vs0\mut` for tests and mutants). All four were removed afterwards. Exports were restored in each worktree with `fpl_nightly.restore_exports('.')`; the restored `fpl_export_gw6.json` is byte-identical to `exports/fpl_export_gw6_2026-10-16.json`. My scripts are in the scratchpad: `vs0\regen.py`, `vs0\probe.py` and `vs0\mutate.py`. I did not use the implementer's scratch scripts.

## Prereg order — PASS

`prereg/S0.md` was added in `037b7dd` (17:27:34 +0200), which is the parent of the only code commit, `5828d1e` (17:32:14 +0200). `037b7dd` contains Markdown files only. `prereg/S0.md` has no later commit, and it is identical at `037b7dd` and `master`.

## 1. Point-in-time — PASS

The item produces no forecast and adds no input to any forecast. I checked the inputs it does use:

- **Export timestamp.** The export behind the watchlist lookup and the bench audit is `fpl_export_gw6_2026-10-16.json`, generated `2026-10-16T22:02:14+00:00`. That is before GW7's deadline, `2026-10-17 10:00 UTC` (`fpl_edge.next_deadline`).
- **The watch file's forecasts.** The watch file now shows 165 and 115 with GW7 forecasts. These are rows already in `projection_log.csv`, with `made_at` `2026-10-16T22:02:14/15+00:00`, which is before the GW7 deadline. Its header reads "forecasts recorded 2026-10-16T22:02".
- **The bench audit's points.** The audit for GW6 reads GW6's own realised points. That is its purpose: it is a hindsight audit, not a forecast. It runs after GW6 is final: event 6 has `finished = 1` and `data_checked = 1`, all 10 GW6 fixtures are finished, and the last kickoff was 2026-10-12 19:00Z. All 105 squad `gw_points` values match the GW6 rows of `player_gw_recent` (0 mismatches). No forecast or recorder reads the audit's output (see check 5).
- **Leak probe.** The item has no forecast metric, so I ran the probe on the one number it adds, the keeper-swap term. I ran the item's `sec_bench` on the GW6 squads with every player's points shifted by one gameweek (from `player_gw_recent`):

  | points fed | our keeper term | our perfect-XI gain | keeper term summed over the 7 managers |
  |---|---|---|---|
  | GW6 (aligned) | Verbruggen +7 | +12 | 9 |
  | GW5 (shifted -1) | Verbruggen +0 | +8 | 3 |
  | GW4 (shifted -2) | Verbruggen +5 | +7 | 5 |

  GW7 has not been played, so there is no +1 shift.

  Our +7 is specific to GW6 (Verbruggen 9, Kelleher 2). It collapses to 0 when GW5's points are fed (6 and 6). So the term reads the gameweek it is given, not another field.

  The full perfect-XI gain does not collapse to zero under a shift. It is a non-negative hindsight maximum and is positive for almost any set of points. That is expected for an audit, and it is not a leak, because nothing is being forecast.

## 2. Clean-checkout test run — PASS

| | commit | `python test_fpl.py` |
|---|---|---|
| before | `07d10a1` | Ran 246 tests, OK (skipped=2), exit 0 |
| after | `5828d1e` | Ran 250 tests, OK (skipped=2), exit 0 |

- **Test names.** The after-run adds exactly four tests: `BenchAudit.test_the_keeper_swap_joins_the_outfield_swap`, `test_a_worse_bench_keeper_adds_nothing`, `test_the_keeper_swap_alone` and `test_a_squad_without_a_bench_keeper_reads_a_dash`. No test was removed. `WatchFile.SEED` changed in place.
- **Skips.** Both skips are "no real export in this folder", which is expected in a fresh checkout.
- **Red before the fix.** I ran the item's `test_fpl.py` against the pre-item code and watchlist (worktree at `07d10a1`). The result was 250 run, FAILED (failures=5): all four BenchAudit tests plus `WatchFile.test_repo_watchlist_holds_the_seed`, which fails on 542 vs 165 and the missing 115.

## 3, 4. Pre-registered evaluation; metric / filter / bootstrap / threshold — n/a

This is a descriptive item: the prereg pre-registers no metric, bootstrap or threshold, and the item reports none. No metric was promoted afterwards, and nothing was tuned.

## 5. Recording path — PASS

I regenerated the GW7 forecasts for all four recorded sources from `exports/fpl_export_gw6_2026-10-16.json` under both codes.

- **How.** Each source went through `fpl_edge.main()` with `--record --source X --status F`, as the nightly calls it. The clock was frozen at the 16 Oct nightly's own `made_at`: 22:02:14Z for own, xg and minutes, and 22:02:15Z for bottomup. I froze the clock instead of moving the deadline guard, so the regenerated log can be compared byte for byte with the committed one.
- **Rows.** Every run printed RECORD OK: own 279, xg 257, minutes 257, bottomup 257. That is 1,050 GW7 rows, matching the implementer's count.
- **Starting logs.** I used two: (A) the committed `projection_log.csv` as checked out, and (B) the same log with all 1,050 GW7 rows removed, so that identity can only come from regeneration.
- **Result.**
  - All four outputs are byte-identical to each other and to the committed `projection_log.csv`: before/A, before/B, after/A and after/B, each 188,681 bytes, sha256 `f95a7228ed085496d9849379887ab19ffd363b5abedd5e543b0515204ee14d66`.
  - The item changed no model, and every model's log is unchanged.
- **The nightly's other outputs, regenerated under both codes:**
  - **The report** (`fpl_edge.py --diff --out`) differs only in the 7 bench-audit lines (report lines 319-325).
  - **The watch file** (`--watch watchlist.txt`) differs only in two rows. The 542 E.Le Fée row is replaced by 165 João Pedro (CHE FWD 7.8, own 3.4 / xg 3.9 / bu 3.2 / min 0.75). A new 115 De Cuyper row is added (BHA DEF 5.1, own 5.1 / xg 6.8 / bu 5.7 / min 1.00). The file is 6,481 bytes, under the 15 KB limit.

## 6. Mutation spot-check — PASS

Each mutant was applied alone in a scratch worktree at `5828d1e`, the full suite was run, and the file was restored.

| mutant (one line) | `python test_fpl.py` | red tests |
|---|---|---|
| M1 the total prints `+{gain}` (keeper swap left out) | FAILED (failures=2) | `test_the_keeper_swap_joins_the_outfield_swap`, `test_the_keeper_swap_alone` |
| M2 the keeper term is not floored at 0 (`max(0, ...)` removed) | FAILED (failures=1) | `test_a_worse_bench_keeper_adds_nothing` |
| M3 the incoming keeper is taken from the XI, not the bench | FAILED (failures=4) | all four BenchAudit tests |
| M4 `watchlist.txt` loses the 115 line | FAILED (failures=1) | `WatchFile.test_repo_watchlist_holds_the_seed` |

M1-M3 show that the new tests check the arithmetic, not only the new line format. Before the fix, three of the four failed only because their regex needs the new "keeper" field.

## 7. Secrets — PASS

The item adds or changes 9 files: `.claude/agents/backtest-verifier.md`, `CLAUDE.md`, `fpl_edge.py`, `prereg/README.md`, `prereg/S0.md`, `prereg/TEMPLATE.md`, `test_fpl.py`, `watchlist.txt` and `worklog/README.md`.

I searched their added lines and their whole files at `master` for `api_key`, `apiKey`, `apiKey=`, `Authorization`, `Bearer`, `ODDS_API`, tokens, secrets, passwords, URLs and 32+ character opaque strings. There were only two hits, both documentation and neither a value:
- the verifier's own rule text ("with apiKey=, or an Authorization header value");
- the variable name `ODDS_API_KEY` in the CLAUDE.md secrets rule.

The added lines contain no URL. `ODDS_API_KEY` is not set in this shell, so I could not check for the value itself.

## Acceptance tests (prereg/S0.md)

1. **Verifier file — PASS.** `.claude/agents/backtest-verifier.md` is byte-identical to the fenced block under "Verifier agent" in `BUILD_PLAN.md`. Both are 1,908 bytes with LF endings and the same sha256 `87c367c9...b8745c49`. This holds for the committed file and the working-tree file.
2. **Protocol files — PASS.**
   - `prereg/README.md`, `prereg/TEMPLATE.md` and `worklog/README.md` are committed.
   - The template carries every field Step 0.3 lists:
     - id and hypothesis;
     - data and sample filter, with point-in-time only and "starters" = forecast P(start) >= 0.8, never realised minutes;
     - the comparison;
     - one primary metric, with secondaries marked information only;
     - bootstrap unit = gameweek, 10,000 resamples, 90% CI;
     - the pass threshold;
     - "No re-tuning after viewing results."
   - `CLAUDE.md` has a "Work-item protocol" section with the standing rules: one step per session, stdlib-only runner, frozen models under a new source name, the item order, secrets, and stop-and-report.
3. **(a) Watchlist — PASS.**
   - `watchlist.txt` no longer holds 542.
   - The id lookup in the 16 Oct export gives exactly one player with web_name "João Pedro" and team CHE: id **165** (FWD, 7.8).
   - id 115 is De Cuyper (BHA DEF).
   - All 19 ids exist in the export, with no duplicates.
   - `WatchFile.test_repo_watchlist_holds_the_seed` pins the list (M4 turns it red).
4. **(b) Bench audit — PASS.** On the GW6 export, our line reads:
   `>> 1. FC Kiripolcz        bench= 13  best benched Rudoni      ( 7)  worst XI E.Le Fée    ( 2)  keeper Verbruggen  +7   perfect-XI gain +12`
   - The same line read `perfect-XI gain +5` before the fix.
   - I recomputed all 7 managers' keeper terms independently from the squads (+7, 0, 0, +2, 0, 0, 0). They match the printed lines.
   - The unit tests fail before the fix and pass after (check 2).
5. **Verifier smoke test — PASS.**
   - **The report.** `worklog/verify_SMOKE.md` (untracked) is a verifier report on a scratch branch `scratch/verifier-smoke`. The branch had its own prereg (`98ce2f3`, `prereg/SMOKE.md`) and a toy evaluation (`9e2199e`, `toy_eval.py`).
   - **The leak is real.** I read those objects: `toy_eval.py` sets `feature = pts[g]` and `target = pts[g]`.
   - **The verdict.** The report's verdict is FAIL, with check 1 FAIL, as required.
   - **The branch is deleted.**
     - No local ref matches scratch or smoke.
     - `git ls-remote --heads origin` lists only `master`.
     - `toy_eval.py` and `prereg/SMOKE.md` are on neither `master` nor disk.
     - The two commit objects still exist, but only in HEAD's reflog ("checkout: moving from scratch/verifier-smoke to master"). That is normal after a branch is deleted.
6. **Recording path unchanged — PASS.** See check 5: GW7 regenerates byte-identical before and after.

## Observations (not blocking)

- **Step 0 is not finished yet.** The steps after the verifier are still open:
  - the `CHANGELOG.md` entries that Step 0.5 asks for: "each with tests and a changelog entry";
  - the report `worklog/cc_<date>_S0.md`, which must print João Pedro's id (165) and quote the smoke-test verifier output (Step 0.6);
  - the push: `origin/master` is still `07d10a1`.
  - `worklog/verify_SMOKE.md` is untracked. Commit it with the report if it is to be kept.
- **The audit ignores automatic substitutions.** This is pre-existing, and the keeper term inherits it. The audit reads slots and `gw_points` without them. If a starting keeper plays 0 minutes and the bench keeper comes on automatically, the audit would show a "keeper gain" for points that already counted. This did not happen in GW6: all 7 starting keepers played 90 minutes. The outfield swap has always had the same blind spot; in GW6, PyroNeniZlocin had 4 starters on 0 minutes. This is outside S0's scope and is a candidate for a later item.

## VERDICT: PASS

The prereg was committed before the item's only code commit. The six acceptance tests in `prereg/S0.md` all hold:
- the verifier file is byte-identical to the BUILD_PLAN block;
- the protocol files and the CLAUDE.md section exist with every required field;
- the watchlist holds João Pedro (165, the only CHE "João Pedro" in the 16 Oct export) and De Cuyper (115), without 542, and a test pins the list;
- the GW6 bench audit shows Verbruggen +7 next to Rudoni, and the perfect-XI gain went from +5 to +12;
- the smoke-test verifier FAILed check 1, and its branch no longer exists.

The suite goes from 246 to 250 tests, green on clean checkouts, and the five new or changed assertions are red on the old code. Four one-line mutants each turn a test red.

With the clock frozen at the nightly's own `made_at`, the GW7 forecasts regenerate to a projection log that is byte-identical across both codes and identical to the committed log. The nightly report and the watch file change only in the intended lines. No secrets were found.

What remains before Step 0 is done is the changelog entries, the report and the push.
