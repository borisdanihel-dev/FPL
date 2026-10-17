# verify_SMOKE2 — backtest-verifier report

- **Item:** SMOKE2 (BUILD_PLAN.md Step 0.6, rerun under S0b ruling 3). Branch `scratch/verifier-smoke2`, local only.
- **Commits (`git log master..HEAD`):** `4a7c469` is the prereg (adds `prereg/SMOKE2.md` only). `f66ba8c` is the code (adds `toy_eval.py` only). Base is `master` = `01b67a3`.
- **Implementer's claim:** `python toy_eval.py` prints `SMOKE2  mean per-GW Spearman, GW2-38: 1.000000  (n = 37 gameweeks)`.
- **Check definitions:** these come from `.claude/agents/backtest-verifier.md` as it stands on disk (amended in `01b67a3`). Check 1 is 1a truncation test (decides), 1b timestamp audit (decides) and 1c shift probe (warns only). The check 1 in my launch instructions is the older "leak probe" text. The file on disk governs, so 1a/1b/1c are reported below.
- **Verified:** 2026-10-17, Python 3.14.7, standard library only, `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1`.
  - Clean checkouts were detached `git worktree`s of `01b67a3` and `f66ba8c` in the session scratchpad (`...\scratchpad\vsmoke2\`). Both were removed and pruned afterwards.
  - The 2025/26 data was read from `C:\GIT\FPL\historical\2025-26`, which is git-ignored.
  - Scratch scripts: `verify_smoke2.py` (checks 1, 3, 4) and `regen.py` (check 5).

## Prereg order — PASS

- `prereg/SMOKE2.md` was added in `4a7c469`, which is the parent of the code commit `f66ba8c` (`git merge-base --is-ancestor` holds).
- `toy_eval.py` does not exist at `4a7c469`, and `prereg/SMOKE2.md` does not exist on `master`.
- The prereg blob is the same at `4a7c469` and at HEAD (`da22ebc8`). Each file has exactly one commit in `master..HEAD`.
- The two commits are one second apart (19:49:34 and 19:49:35 +0200). The order therefore rests on ancestry, not on the clock.

## 1. Point-in-time leak check — FAIL

The design itself is the problem. The prereg defines the feature as "for gameweek g, each player's points for gameweek g". In `toy_eval.py` `evaluate()`, `feature = pts[g]` and `target = pts[g]` are the same dict. The prereg pre-registers a non-point-in-time input, which breaks `prereg/README.md` ("point-in-time sources only").

**Deadline(g):** 90 minutes before g's first kickoff in `fixtures.csv`, the `fpl_edge.next_deadline` rule. For example: GW2 2025-08-22 17:30 UTC, GW20 2026-01-03 11:00 UTC, GW38 2026-05-24 13:30 UTC. The vaastav folder has no events file with official deadlines. The conclusions do not depend on the exact rule: any deadline at or before the first kickoff gives the same result, because a row's `total_points` exists only after its match has finished.

**Source rows:** `merged_gw.csv` has 29,757 rows. De-duplication on (element, fixture) leaves 29,747, the same as `canonical_from_vaastav` (0 player-GW totals differ). GW2-38 uses 29,057 source rows, which make 28,648 player-gameweeks.

### 1a. Truncation test (decides) — FAIL

For the earliest, middle and latest evaluated gameweeks, I rebuilt the item's feature using only historical rows with round < g:

| GW | admissible player-GW rows (events 1..g-1) | item's feature values | values rebuildable from admissible rows | differing by > 1e-9 if a missing value is read as 0 (max abs diff) | item's own `evaluate()` on the truncated slice |
|---|---|---|---|---|---|
| 2 | 690 | 705 | 0 (705 missing) | 295 (24 pts) | `KeyError: 2` |
| 20 | 14,175 | 790 | 0 (790 missing) | 286 (17 pts) | `KeyError: 20` |
| 38 | 28,497 | 841 | 0 (841 missing) | 302 (18 pts) | `KeyError: 38` |

No admissible row carries round g, so the feature cannot be built at all from point-in-time inputs. Every value is missing. Even reading a missing value as 0, about 290-300 values per gameweek differ, by up to 24 points.

### 1b. Timestamp audit (decides) — FAIL

I compared every source row feeding the GW2-38 feature against deadline(g):

- **29,057 of 29,057 rows** are dated (by match `kickoff_time`) after deadline(g). **0** are at or before it.
- The smallest gap is +1:30:00, which is each gameweek's first match. The largest is +8 days 2:00:00.
- For every row, the `kickoff_time` in `merged_gw.csv` equals the fixture's kickoff in `fixtures.csv`, and the fixture's event equals the row's `round` (0 mismatches of either kind).
- By gameweek: GW2 has 705 of 705 rows after the deadline, GW20 790 of 790, GW38 841 of 841.

### 1c. Shift probe (warns only) — WARN (not cleared: 1a and 1b both fail)

Sample: players with 60+ minutes in both g and g+1 (minutes summed over a double gameweek), g = 2..37, pooled into one Spearman.

- 5,669 pairs.
- Bootstrap: unit = gameweek, 10,000 resamples, seed 20261017, percentile 90% CI.
- Unshifted (feature g vs points g): **1.000000**, 90% CI 1.000000..1.000000.
- Shifted (feature g vs points g+1): **0.024165**, 90% CI -0.002788..0.050639.
- Unshifted minus shifted: **0.975835**, 90% CI 0.949361..1.002788.
- Both WARN conditions hold: unshifted > 0.25 (measured ceiling 0.15), and the difference > 0.10 (fixture term 0.02-0.06).
- The shifted metric collapses to about zero, as a same-gameweek leak predicts.

Cross-checks and information only:
- My counting Spearman equals `fpl_edge._spearman` on the pooled pairs to 12 decimal places (0.024165372116).
- Per-GW mean on the same filter: unshifted 1.000000, shifted 0.019647 (n = 36 GWs).
- The honest lag-1 version of the item's own metric (points in g-1 against points in g, every player with a row in g, missing = 0) has a mean of 0.700460 (n = 37). It stays high because non-playing players sit at 0 in consecutive weeks.

## 2. Clean-checkout test run — PASS

| | commit | `python test_fpl.py -v` |
|---|---|---|
| before | `01b67a3` (master) | Ran 250 tests, OK (skipped=2), exit 0 |
| after | `f66ba8c` (HEAD) | Ran 250 tests, OK (skipped=2), exit 0 |

The 250 test names are identical before and after. Both skips are "no real export in this folder", which is expected in a fresh checkout. The item adds no tests (250 to 250).

## 3. Re-run of the pre-registered evaluation — PASS (reproduces; says nothing about validity)

There is no backtest harness yet (`backtest.py` is BUILD_PLAN Step 4 and absent), so I re-ran the item's own entry point, which uses `fpl_hist.canonical_from_vaastav` and `fpl_edge._spearman`:

- **The implementer's command** (`python toy_eval.py` in `C:\GIT\FPL`): `SMOKE2  mean per-GW Spearman, GW2-38: 1.000000  (n = 37 gameweeks)`.
- **The committed code from the clean `f66ba8c` worktree** (cwd `C:\GIT\FPL`, for the relative data path): identical output.
- **`evaluate()` imported from the clean checkout:** mean 1.000000000000, n = 37, `through_gw` = 38.
- **An independent recomputation** (my own CSV read, de-duplication and tie-corrected Spearman): mean 1.000000000000, n = 37.
  - The difference from the implementer's mean is 0, within the 1e-6 tolerance.
  - The largest per-GW difference from `E._spearman` is 0.
  - The per-GW rho is 1.000000000000 in all 37 gameweeks (582-841 players per gameweek).

## 4. Metric, filter, bootstrap, threshold as pre-registered — FAIL

- **Primary metric:** the mean per-GW Spearman, as pre-registered. Matches.
- **Sample filter:** GW2-38, every player with a row in the gameweek (`ids = sorted(target)`, `range(2, through_gw + 1)`, `through_gw` = 38). Matches. However, the filter's data is not point-in-time (see check 1), contrary to `prereg/README.md`.
- **Bootstrap:** not implemented. The prereg fixes unit = gameweek, 10,000 resamples, 90% CI. `toy_eval.py` computes no bootstrap and prints no interval, which also breaks the CLAUDE.md rule "Every correlation is printed with its interval". Run to the prereg by the verifier (seed 20261017), the result is 1.000000, 90% CI 1.000000..1.000000.
- **Pass threshold:** "above 0.30" is never evaluated or printed by the code. The prereg also gives no CI condition for it, although `prereg/TEMPLATE.md` asks for one.
- **Label:** the printed "GW2-" is hard-coded. Mutant 3 in check 6 scores GW3-38 and still prints "GW2-38".
- **Post-hoc changes:** none. No metric was promoted (there are no secondary metrics), nothing was re-tuned, and each file has one commit, prereg first.

## 5. Recording path — PASS

I regenerated the current forecasts: GW7, all four recorded sources, from `exports/fpl_export_gw6_2026-10-16.json`, the nightly's last input.

- Each run went through `fpl_edge.main()` with `--record --source <s>`, under both `01b67a3` and `f66ba8c` code.
- The clock was frozen at the nightly's own `made_at` (own, xg and minutes at 2026-10-16T22:02:14Z, bottomup at 22:02:15Z). Each run started from the committed log.
- Rows written: own 279, xg 257, minutes 257, bottomup 257.
- The base log, the head log and the committed `projection_log.csv` are byte-identical: 188,681 bytes, sha256 `f95a7228ed085496d9849379887ab19ffd363b5abedd5e543b0515204ee14d66`.
- Sanity run: I deleted all 1,050 GW7 rows from a copy of the log and regenerated them under the head code. The result is also byte-identical to the committed log, so the rows really were rewritten.
- The item changes no model. `git diff master HEAD` is empty for `fpl_edge.py`, `fpl_hist.py`, `fpl_nightly.py`, `fpl_sync.py`, `fpl_ship.py`, `p1_eval.py`, `test_fpl.py`, `projection_log.csv` and `exports/`.

## 6. Mutation spot-check — FAIL

`test_fpl.py` never imports or mentions `toy_eval` (no match on grep). Each mutant below is a one-line change in a scratch copy of the `f66ba8c` checkout, and the suite stayed green for all three:

| mutant (line of `evaluate()`) | effect on `toy_eval.py` | `python test_fpl.py` |
|---|---|---|
| `feature = pts[g]` → `feature = pts[g - 1]` | crashes, `KeyError: 691` | 250 tests, OK (skipped=2), exit 0 |
| `rhos.append(E._spearman(...))` → `rhos.append(-E._spearman(...))` | silently prints -1.000000 | 250 tests, OK (skipped=2), exit 0 |
| `range(2, ...)` → `range(3, ...)` | silently n = 36, label still "GW2-38" | 250 tests, OK (skipped=2), exit 0 |

## 7. Secrets — PASS

The item adds only `prereg/SMOKE2.md` and `toy_eval.py`. I searched the added diff and both whole files, case-insensitively, for `api_key`/`apikey`/`ODDS_API`, `Authorization`, `Bearer`, `token`, `secret`, `passw`, `http(s)://` and opaque strings of 32+ characters. Nothing matched.

## Write guard

- Before this report was written, after both worktrees were removed and pruned:
  - `git status`: "nothing to commit, working tree clean" on `scratch/verifier-smoke2`.
  - `git diff`: empty.
  - `git status --ignored`: only the pre-existing `fpl_export_gw3..6.json` and `historical/`; no `__pycache__`.
  - `git worktree list`: only `C:/GIT/FPL`.
- The only file I wrote in the repository is this report, `worklog/verify_SMOKE2.md`.

## VERDICT: FAIL

The toy evaluation's feature for gameweek g is gameweek g's own realised points, literally the same dict as the target. Both deciding parts of check 1 fail:

- **1a:** at GW2, GW20 and GW38, none of the 705, 790 or 841 feature values can be rebuilt from rows with round < g. The item's own `evaluate()` raises `KeyError` on the truncated slice.
- **1b:** all 29,057 source rows behind the GW2-38 feature are dated after their gameweek's deadline, and none at or before it.

The 1c shift probe warns on both conditions (unshifted 1.000000; shifted 0.024165, 90% CI -0.002788..0.050639), and 1a and 1b do not clear it. The implementer's 1.000000 reproduces exactly (check 3), but it measures identity, not forecasting skill. Three further problems:

- The pre-registered bootstrap and pass threshold are never applied (check 4).
- No test covers the new code: three one-line mutants, one crashing and two silently wrong, all leave the suite green (check 6).
- The prereg itself pre-registers the non-point-in-time feature.

Checks 2, 5 and 7 pass, and the prereg order is correct. For S0b acceptance test 2, this is the required outcome: verdict FAIL with 1a FAIL and 1b FAIL.
