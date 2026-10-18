# Verifier report: S1-closing

**Model that ran this verification:** Fable 5.1 (`claude-fable-5-1`), launched as the `backtest-verifier` agent from `.claude/agents/backtest-verifier.md` at `69b360d` (`model: fable`, `effort: high`). The effort setting is read from the agent file; it is not observable from inside the run. No usage-credit prompt and no fallback to Opus occurred. Instructions: the agent file on disk was read first; it equals the loaded instructions plus the masking sentence, which this report applies.

- **Item:** S1-closing (setup and docs; no forecast, feature or metric).
- **Prereg:** `prereg/S1-closing.md`, commit `44358a0` 2026-10-18 10:02:19 +0200.
- **Item commit:** `69b360d` 2026-10-18 10:05:05 +0200, parent `44358a0`, local only (`origin/master` = `44358a0`, confirmed by the GitHub branches API).
- **Files changed (5):** `.claude/agents/backtest-verifier.md`, `.github/workflows/secret-scan.yml`, `BUILD_PLAN.md`, `CLAUDE.md`, `test_fpl.py`. The only `.py` change is `test_fpl.py` (+13/-1).
- **Scratch:** three throwaway clones (`before` at `44358a0`, `after` and `mut` at `69b360d`) and two data copies under `%TEMP%\claude\...\scratchpad\v`, deleted after this report. Nothing in `C:\GIT\FPL` was changed except this file; `C:\GIT\FPL-data` was read only (`git status` clean before and after).

## Prereg ordering

PASS. `44358a0` (prereg) precedes `69b360d` (code) by 2m46s and is its parent. The prereg carries the eight-point ruling verbatim and "No re-tuning after viewing results."

## Check 1: point-in-time leak check

n/a. The item produces no forecast, feature or evaluation metric: the diff touches two docs, the agent file, one workflow and the test suite. 1a and 1b have no input to rebuild; 1c has no correlation to probe. Check 5 shows the recorded forecasts are unchanged.

## Check 2: clean-checkout test run

PASS.

| tree | result |
|---|---|
| `before` clone at `44358a0` | `Ran 308 tests in 36.195s`, `OK (skipped=3)`, exit 0 |
| `after` clone at `69b360d` | `Ran 309 tests in 36.195s`, `OK (skipped=3)`, exit 0 |

The one new test is `VerifierAgent.test_the_verifier_runs_on_fable_at_high_effort_and_masks_keys`. The identity test `VerifierAgent.test_the_plan_block_is_the_agent_file` is green in both runs (ruling point 8). The 3 skips are the same in both trees (data-dependent tests; the clones hold no `data` files).

## Check 3: pre-registered evaluation

n/a. The prereg has no hypothesis, metric, sample, bootstrap or threshold.

## Check 4: metric, filter, bootstrap, threshold; the ruling

PASS. The ruling (points 1-8) is present verbatim in `prereg/S1-closing.md` and is checked point by point below. No metric exists to promote and nothing was re-tuned.

### Ruling point by point

| # | ruling | result | evidence |
|---|---|---|---|
| 1 | agent file and BUILD_PLAN block: `model: fable`, `effort: high`, identical; fallback opus/xhigh with the report naming what ran | PASS | Agent frontmatter lines 5-6 are `model: fable` / `effort: high`. The BUILD_PLAN block (from `---\nname: backtest-verifier` to the closing fence) and the agent file compared equal as bytes at `69b360d` (2897 = 2897 chars). The fallback sentence is in CLAUDE.md lines 53-56 ("If Fable is unavailable or Claude Code asks for usage credits, decline the credits and run the verifier with model opus at effort xhigh; the verifier report states which ran."). This report names the model at the top. |
| 2 | the masking sentence in the block | PASS | Agent file line 19 and the BUILD_PLAN block carry `Mask key-like strings in your report: the first 4 characters, then '...'.` character for character. |
| 3 | CLAUDE.md Session operating mode: Opus 5.5; effort xhigh/high/medium; steps 4, 7, 15, 16, 17 may run on Fable; report names the model | PASS | CLAUDE.md line 81, item `h` under `## Session operating mode` (line 65), is the ruling's sentence verbatim. |
| 4 | lagging docs: BUILD_PLAN 1.6 gitleaks in secret-scan.yml (no local download); CLAUDE.md line 9 says committed to the data branch; secret-scan `runs-on: ubuntu-24.04` | PASS | BUILD_PLAN.md line 228: "gitleaks runs in `.github/workflows/secret-scan.yml` (no local download): every push to master, a weekly full-history scan of every branch, and on dispatch; ...". CLAUDE.md line 9: "committed to the `data` branch". secret-scan.yml line 31: `runs-on: ubuntu-24.04   # pinned, as the nightly (S1 closing ruling)`; `ubuntu-latest` no longer appears in the file and is now on the test's banned list. Cosmetic only: CLAUDE.md line 9 is now 88 characters, past the file's wrap. |
| 5 | CLAUDE.md: no manual nightly dispatch within 1 hour either side of an FPL deadline | PASS | CLAUDE.md lines 129-131 under `## Data branch`: "**No manual nightly dispatch within 1 hour either side of an FPL deadline.** A dispatch across a deadline fails the gate (its forecasts were recorded before it, the gate runs after) and commits nothing that night." |
| 6 | delete local branch `scratch/s1-wip` | PASS | `git branch -a` lists only `data`, `master` and the two remotes; `git cat-file -t b738e6d` = `commit` (the WIP tip is still in the object store, as the task stated). Tags `backup-2026-10-17` and `pre-data-branch`, the two worktrees and the empty stash list are unchanged. |
| 7 | before Step 2: confirm the first scheduled nightly on the new layout and the Sunday 04:23 UTC secret-scan run | PARTIAL, as expected | **secret-scan:** run `39098380500`, `event=schedule`, `status=completed`, `conclusion=success`, created 2026-10-18T04:48:38Z (a Sunday), head `f214c36` on master; the 25-minute lag after the `23 4 * * 0` cron is GitHub's normal schedule delay. That run pre-dates the `runs-on` pin in `69b360d`; the pin is unpushed, so no run has exercised it yet. **nightly 2026-10-18:** pending. The schedule is 21:40 UTC today; at the time of this report the `data` branch's latest commit is `e84bee6` "nightly 2026-10-17 [skip ci]" (2026-10-17T22:04:08Z, from dispatch run `39073502058`), and the latest `nightly.yml` run is that dispatch. Not a failure; it cannot exist yet. Both must be confirmed by the main session before Step 2. |
| 8 | tests before and after (identity test green); verifier on this item, first run on Fable; write guard; push | PARTIAL, as expected | Tests: check 2 (308 OK -> 309 OK, identity test green both times). Verifier: this run, on Fable. Write guard: the main session's `git status` / `git diff` after this run; from this side, only `worklog/verify_S1-closing.md` was written. Push: not done yet, `origin/master` = `44358a0`; `69b360d` is a fast-forward of it (`git merge-base --is-ancestor` true), so the push itself is trivial. Pending until after the write guard. |

## Check 5: recording path

PASS.
- **Method.** Two identical data copies (`fpl.sqlite`, `projection_log.csv`, `fpl_export_gw3..7.json` from `C:\GIT\FPL-data` at `e84bee6`; sha256 `51c906ab...`, `f052c028...`, ...). Time frozen at 2026-10-18T12:00:00Z by a scratch `sitecustomize.py` on `PYTHONPATH` (replaces `datetime.datetime` with a subclass whose `now()` is fixed). `fpl_edge.py --record --source {own,xg,minutes,bottomup} --status status.tmp` run from the `before` tree against copy A and from the `after` tree against copy B, with the data copy as the working directory, as `fpl_nightly.py` does. The record output's "5 days, 5:30:00 before deadline" places the GW8 deadline at 2026-10-23T17:30Z.
- **Result.** Both: `RECORD OK own 275 / xg 260 / minutes 260 / bottomup 260`. The two logs are **byte-identical** (`cmp` silent), 4680 lines each, sha256 `69d3f73b...`, 1055 rows carrying the frozen stamp; the status files are identical.
- **Against the committed `data` log.** Same 4679 `(source, event, player_id)` keys; 0 rows differ outside `made_at`; all 3624 non-GW8 rows identical including `made_at`. The sha256 `69d3f73b...` equals the one the S1 verifier recorded for the same inputs, so no model moved in S1-closing or since.

## Check 6: mutation spot-check

PASS. Seven one-line mutations in the `mut` clone at `69b360d`, each restored with `git checkout --` and the clone clean afterwards (`git status --porcelain` empty). Targeted run: `python test_fpl.py VerifierAgent NightlyWorkflow.test_secret_scan_runs_the_pinned_gitleaks_action` (4 tests, green at baseline).

| # | file | mutation | red test(s) |
|---|---|---|---|
| M1 | agent file | `model: fable` -> `model: inherit` | identity test + `test_the_verifier_runs_on_fable_at_high_effort_and_masks_keys` |
| M2 | agent file | `effort: high` line removed | both |
| M3 | agent file | masking sentence "first 4 characters" -> "first 3 characters" | both |
| M4 | BUILD_PLAN block only | `effort: high` -> `effort: medium` | identity test |
| M5 | secret-scan.yml | `runs-on: ubuntu-latest` | `test_secret_scan_runs_the_pinned_gitleaks_action` |
| M6 | secret-scan.yml | `runs-on: ubuntu-22.04` | same |
| M7 | agent file and block together | `model: fable` -> `model: opus` in both (identity still holds) | `test_the_verifier_runs_on_fable_at_high_effort_and_masks_keys` alone, as intended |

The mutation output printed no key-like string.

## Check 7: secrets

PASS. The full diff `44358a0..69b360d` and each of the 5 changed files at `69b360d` were grepped for `apiKey=`, `Authorization`, `api_key` and any 32+/36+ character token. Hits, all benign: the literal rule text "a URL with apiKey=" in the agent file (line 48) and BUILD_PLAN (lines 150, 224); the secret's *name* `ODDS_API_KEY` in CLAUDE.md line 90 (no value); the pinned gitleaks action commit `e0c4...` in secret-scan.yml; test names in test_fpl.py. The workflow still runs with `permissions: contents: read`, no `secrets.` reference, no `ref:`, no `inputs`.

## Open points for the main session

1. Point 7 is half-confirmed: the Sunday secret-scan run is green; the first scheduled nightly on the new layout ("nightly 2026-10-18" on `data`, gate green, 21:40 UTC) is pending and must be confirmed before Step 2.
2. Point 8's push is pending (`origin/master` = `44358a0`); run the write guard first.
3. The `runs-on: ubuntu-24.04` pin in secret-scan.yml has no live run yet; the next push to master will be its first.

VERDICT: PASS

Reason: the prereg with the verbatim eight-point ruling was committed before the item's only code commit; every doc and config change the ruling asks for is present with the exact wording (agent file and BUILD_PLAN block byte-identical with `model: fable`, `effort: high` and the masking sentence; CLAUDE.md fallback, operating-mode item h, data-branch wording and the dispatch-near-deadline rule; BUILD_PLAN 1.6 gitleaks wording; secret-scan pinned to ubuntu-24.04); `scratch/s1-wip` is deleted with its commit retained; tests go 308 OK to 309 OK with the identity test green; all seven mutations of the new logic go red; the recording path regenerated from the before and after trees is byte-identical and matches the committed log outside `made_at`; no secret appears in any changed file; the Sunday secret-scan schedule run is confirmed green via the public API, and the two items that cannot be complete yet (tonight's nightly and the push) are correctly pending rather than failed.
