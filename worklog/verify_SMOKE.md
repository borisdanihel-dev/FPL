# verify_SMOKE — backtest-verifier report

- **Item:** SMOKE (BUILD_PLAN.md Step 0.6, verifier smoke test), branch `scratch/verifier-smoke`
- **Commits (`git log master..HEAD`):** `98ce2f3` prereg (adds `prereg/SMOKE.md` only), `9e2199e` code (adds `toy_eval.py` only). Base: `master` = `5828d1e`.
- **Implementer's claim:** `python toy_eval.py` prints a mean per-GW Spearman of 1.000000 over GW2-38, n = 37.
- **Verified:** 2026-10-17, Python 3.14.7. Clean checkouts were temporary git worktrees outside the repo, removed afterwards. The 2025/26 data was read from `C:\GIT\FPL\historical\2025-26`. Scratch scripts and outputs are in the session scratchpad, `vsmoke\` (`indep_eval.py`, `pit_check.py`, `regen.py`).

## Prereg order — PASS

`prereg/SMOKE.md` was added in `98ce2f3`, which is an ancestor (the parent) of the code commit `9e2199e`. `toy_eval.py` is absent at `98ce2f3`, and neither file was changed after its first commit. Both commits carry the same timestamp (2026-10-17 17:32:43 +0200), so the order comes from ancestry, not from the clock.

## 1. Point-in-time — FAIL

- **The feature is the target.** In `toy_eval.py` `evaluate()`, the lines `feature = pts[g]` and `target = pts[g]` are the same dict: gameweek g's realised points, used as the feature for gameweek g. The prereg itself pre-registers this ("each player's points for gameweek g"), which breaks `prereg/README.md`: "point-in-time sources only".
- **Timestamps.** Deadline(g) is 90 min before g's first kickoff (the `fpl_edge.next_deadline` rule, applied to `fixtures.csv`). All 29,065 source rows feeding the GW2-38 feature come from matches that kick off after deadline(g); 0 come from before it. The smallest gap is +1:30:00, which is g's first match. For example, GW2's deadline was 2025-08-22 17:30 UTC and its first kickoff 19:00 UTC. So no feature value exists before its gameweek's deadline.
- **Result signature.** The per-GW Spearman is exactly 1.000000000000 in all 37 gameweeks (582-841 players per GW).
- **Leak probe (target shifted by one GW):**
  - Shifted +1 (feature pts[g], target pts[g+1], GW2-37, n = 36): mean 0.708429, 90% CI 0.698524..0.718193.
  - Shifted -1 (GW2-38, n = 37): mean 0.707873, 90% CI 0.698091..0.717503.

  The metric drops by 0.29 from a perfect 1.000000, so the unshifted score comes from same-gameweek alignment. It does **not** collapse toward zero, so I cannot confirm the probe's expected behaviour on this sample filter. The reason: the whole-population filter keeps every non-playing player at 0 points in consecutive weeks, so realised points are strongly autocorrelated. The +1 probe is exactly the honest lag-1 feature ("last week's points"), and about 0.71 is what a point-in-time version of this feature scores. This does not rescue the check: the inputs are post-deadline by construction.

## 2. Clean-checkout test run — PASS

| | commit | `python test_fpl.py` |
|---|---|---|
| before | `5828d1e` (master) | Ran 250 tests, OK (skipped=2), exit 0 |
| after | `9e2199e` (HEAD) | Ran 250 tests, OK (skipped=2), exit 0 |

The test names are identical before and after. Both skips are "no real export in this folder", which is expected in a fresh checkout. The item adds no tests (250 → 250).

## 3. Re-run of the pre-registered evaluation — PASS (reproduces; says nothing about validity)

There is no backtest harness yet (`backtest.py` is BUILD_PLAN Step 4), so I re-ran the item's entry point, which uses the shared `fpl_hist.canonical_from_vaastav` and `fpl_edge._spearman`. I ran it three ways:

- **The implementer's command** (`python toy_eval.py` in `C:\GIT\FPL`): `SMOKE  mean per-GW Spearman, GW2-38: 1.000000  (n = 37 gameweeks)`.
- **The committed code** from a clean worktree, with cwd `C:\GIT\FPL`: identical output.
- **An independent recomputation** (`indep_eval.py`), which reads `merged_gw.csv` directly, de-duplicates on (element, fixture) (29,757 → 29,747 rows) and uses its own tie-corrected Spearman:
  - mean 1.000000000000, n = 37, so |mine - implementer's| = 0 < 1e-6;
  - 0 (player, GW) point totals differ from `canonical_from_vaastav`;
  - the largest difference between my per-GW rho and `E._spearman` is 0, both on the identity pairs and on the lag-1 pairs.

## 4. Metric, filter, bootstrap, threshold as pre-registered — FAIL

- **Primary metric:** mean per-GW Spearman, as pre-registered. Matches.
- **Sample filter:** GW2-38, every player with a row in the gameweek (`ids = sorted(target)`, `through_gw` = 38). Matches.
- **Bootstrap:** not implemented. The prereg fixes unit = gameweek, 10,000 resamples, 90% CI, but `toy_eval.py` computes no bootstrap and prints no interval. That also breaks the CLAUDE.md rule "Every correlation is printed with its interval". Run per the prereg by the verifier, the bootstrap gives a 90% CI of 1.000000..1.000000.
- **Pass threshold:** "above 0.30" is not evaluated or printed by the code. The prereg states no CI condition for it, although `prereg/TEMPLATE.md` asks for one.
- **Post-hoc changes:** none. No metric was promoted, there are no secondary metrics, and nothing was re-tuned (one commit per file, prereg first).

## 5. Recording path — PASS

I regenerated the GW7 forecasts for all four recorded sources (own 279, xg 257, minutes 257, bottomup 257 rows) from `exports/fpl_export_gw6_2026-10-16.json` under both codes. Each run started from the committed log, with the clock frozen at the nightly's own `made_at` (2026-10-16T22:02:14/15Z).

- The `master` and HEAD logs are byte-identical: 188,681 bytes, sha256 `f95a7228ed085496d9849379887ab19ffd363b5abedd5e543b0515204ee14d66`.
- Both are also byte-identical to the committed `projection_log.csv`.
- The item does not touch `fpl_edge.py`, `fpl_hist.py`, `fpl_nightly.py`, `fpl_sync.py`, `fpl_ship.py` or `p1_eval.py`.

## 6. Mutation spot-check — FAIL

I tried two mutants of the new logic in a scratch worktree. The suite stayed green for both: `test_fpl.py` never imports or calls `toy_eval.py`.

| mutant | effect on the evaluation | `python test_fpl.py` |
|---|---|---|
| `target = pts[g]` → `target = pts[g - 1]` | `toy_eval.py` crashes with `KeyError: 1` | 250 tests, OK (skipped=2), exit 0 |
| `range(2, ...)` → `range(3, ...)` | silently changes n from 37 to 36 | 250 tests, OK (skipped=2), exit 0 |

The second mutant also shows that the printed label is hard-coded: it still says "GW2-38" while scoring GW3-38.

## 7. Secrets — PASS

The item adds only `prereg/SMOKE.md` and `toy_eval.py`. I searched their added lines and the whole files for API keys (`api_key`, `apiKey=`, `ODDS_API`), `Authorization`, `Bearer`, tokens, secrets, passwords, URLs and long opaque strings. Nothing matched.

## VERDICT: FAIL

The toy evaluation's feature for gameweek g is gameweek g's own realised points. It is literally the same object as the target, so every input comes from matches played after g's deadline. That is why it scores exactly 1.000000 in all 37 gameweeks. The prereg pre-registers this non-point-in-time feature itself, so check 1 fails at the design stage, not only in the code.

The implementer's number reproduces exactly (check 3), but it measures identity, not forecasting skill. An honest lag-1 version of the same feature scores about 0.71. The evaluation also omits the pre-registered bootstrap and never applies the pass threshold (check 4). No test covers the new code: a mutant that crashes it leaves the suite green (check 6).

For BUILD_PLAN Step 0.6: check 1 fails, as the smoke test requires.
