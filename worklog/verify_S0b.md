# verify_S0b — backtest-verifier report

- **Item:** S0b (BUILD_PLAN.md Step 0 follow-up: Boris's rulings on the S0 report). It is a descriptive item: `prereg/S0b.md` has no primary metric, bootstrap or threshold. So checks 1, 2, 5, 6 and 7 apply, plus the prereg's acceptance tests 1-8. Checks 3 and 4 do not apply.
- **Commits (`git log 4f4a7a0..master`):**
  - `7e695c1` adds `prereg/S0b.md` only.
  - `01b67a3` changes `.claude/agents/backtest-verifier.md`, `BUILD_PLAN.md`, `CLAUDE.md` and `FPL_PLAN.md`.
  - `f9c43ee` appends to `CHANGELOG.md` and adds `worklog/verify_SMOKE2.md`.
  - Base `4f4a7a0` = `origin/master`.
- **Check definitions:** taken from `.claude/agents/backtest-verifier.md` as it stands on disk (amended in `01b67a3`). My launch definition still carried the old check 1 (the "leak probe"); the file on disk governs.
- **Verified:** 2026-10-17, 18:11 UTC, Python 3.14.7, standard library only, `PYTHONIOENCODING=utf-8`.
  - Clean checkouts were `git archive` extracts of `4f4a7a0`, `01b67a3` and `f9c43ee` under the session scratchpad (`...\scratchpad\vs0b\t_<rev>`). I added no git worktree, so `.git` was not written.
  - The extracts apply this clone's `core.autocrlf=true`. The extracted `projection_log.csv`, `fpl_edge.py`, `test_fpl.py` and `fpl_nightly.py` are byte-identical to the working tree.
  - My scripts, all in `vs0b\`: `cmp_block.py`, `regen.py` + `regen_one.py` (check 5), `mutate.py` (check 6), `smoke2_repro.py` (acceptance test 2), `ruling_cmp.py` and `transcript_scan.py` (acceptance tests 1, 2, 4, 6, 7).
  - **Primary source for the ruling.** Boris's ruling exists only in chat, not in the repository. I read his message (2026-10-17T17:44:23Z) and the agent launches from this session's transcript, `C:\Users\Boris\.claude\projects\C--GIT-FPL\d7416199-b942-4f77-83ce-ae7c718f57a7.jsonl`.

## Prereg order — PASS

- `prereg/S0b.md` was added in `7e695c1` (19:47:34 +0200). That commit holds only this file and is the parent of the first change commit `01b67a3` (19:49:01 +0200); `git merge-base --is-ancestor` holds.
- The prereg does not exist at `4f4a7a0`. It has no later commit: `git diff 7e695c1 master -- prereg/S0b.md` is empty.

## 1. Point-in-time leak check — PASS (no forecast, feature or metric on `master`)

The amended check 1 applies "for any item that produces a forecast, feature or evaluation metric". On `master` this item produces none:

- `git diff --name-only 4f4a7a0 f9c43ee -- '*.py'` is empty.
- `projection_log.csv`, `exports/`, `fpl.sqlite` and `requirements.txt` are unchanged.
- The only files changed are the seven Markdown files above. `diff -rq` of the `4f4a7a0` and `f9c43ee` extracts lists exactly those seven.
- So there is no feature to truncate (1a), no input row to date (1b) and no correlation to shift (1c).

The one evaluation this item ran is the SMOKE2 toy, a planted leak on a scratch branch. Its check 1 must FAIL, and I reproduced that independently under acceptance test 2.

## 2. Clean-checkout test run — PASS

| | commit | `python test_fpl.py -v` |
|---|---|---|
| before | `4f4a7a0` (base) | Ran 250 tests, OK (skipped=2), exit 0 |
| after (last non-doc change) | `01b67a3` | Ran 250 tests, OK (skipped=2), exit 0 |
| after (HEAD) | `f9c43ee` | Ran 250 tests, OK (skipped=2), exit 0 |

- The 250 test names are identical at all three commits.
- Both skips read "no real export in this folder", which is expected in a fresh checkout.
- This matches the implementer's 250 before and after.

## 3, 4. Pre-registered evaluation; metric / filter / bootstrap / threshold — n/a

The prereg pre-registers no metric, bootstrap or threshold, and the item reports none on `master`. The item does set two thresholds for the verifier (1c: 0.25 unshifted, 0.10 difference). I checked that neither was tuned after the smoke test was seen:

- Boris's ruling fixes both numbers at 17:44:23Z.
- The committed text equals the ruling word for word (acceptance test 1). It was committed at 17:49:01Z, before the SMOKE2 verifier was launched at 17:49:59Z.
- No commit touches the agent file after `01b67a3`.

## 5. Recording path — PASS

I regenerated the current forecasts, GW7 for all four recorded sources, from `exports/fpl_export_gw6_2026-10-16.json`.

- **Export.** That file is the newest GW6 copy that `fpl_nightly.restore_exports()` restores in each extract.
- **How each source ran.** Each source went through `fpl_edge.main()` with `fpl_export_gw6.json --record --source <s>`, in the nightly's order (own, xg, minutes, bottomup).
- **Frozen clock.** I froze the clock at the nightly's own `made_at`: 2026-10-16T22:02:14Z for own, xg and minutes, and 22:02:15Z for bottomup. The deadline guard was left untouched; GW7's deadline is 2026-10-17 10:00 UTC, 11:57:46 later.
- **Code and starting logs.** I ran under the before code (`4f4a7a0`) and the after code (`f9c43ee`). Each started from two logs:
  - (A) the committed log;
  - (B) the committed log with all 1,050 GW7 rows removed (133,785 bytes), so that a match can only come from regeneration.
- **Rows.** Every run printed RECORD OK: own 279, xg 257, minutes 257, bottomup 257.
- **Result.** All four outputs (before/A, before/B, after/A, after/B) are byte-identical to the committed `C:\GIT\FPL\projection_log.csv`: 188,681 bytes, sha256 `f95a7228ed085496d9849379887ab19ffd363b5abedd5e543b0515204ee14d66`.
- **Conclusion.** The item changes no model, and every model's log is unchanged.

## 6. Mutation spot-check — PASS (no new executable logic; see the gap below)

The item adds no code, so no unit test can guard its new lines, and the prereg (acceptance test 8) forbids `.py` changes on `master`. I ran one-line mutants of the item's own changed lines anyway, each in a fresh scratch copy of the `f9c43ee` extract with the full suite run. I also mutated the guard that the one remaining stdlib rule depends on.

| mutant | `python test_fpl.py` | my acceptance check |
|---|---|---|
| M1 agent 1b "Any later row = FAIL." → "= WARN." | 250 tests, OK (skipped=2), exit 0 | agent ≠ BUILD_PLAN block: caught |
| M2 CLAUDE.md: old "Standard library only. No pip" line restored | OK, exit 0 | caught by the acceptance test 3 grep |
| M3 FPL_PLAN.md: line 1 dropped | OK, exit 0 | caught by the acceptance test 4 compare |
| M4 BUILD_PLAN Step 2: item 10 dropped | OK, exit 0 | caught by the acceptance test 6 compare |
| M5 requirements.txt: `numpy` added (enforces the runner-stdlib rule, the only stdlib rule left) | **FAILED (failures=1)**: `NightlyWorkflow.test_requirements_install_nothing` | — |

I pass this check because the item's content is prose that was checked directly against its primary source, and the rule it leaves standing is enforced by a test that goes red (M5). **Gap:** no test guards prereg acceptance test 1's "the two stay byte-identical" (M1 stays green). Drift between the agent file and the BUILD_PLAN block would be caught only by a verifier run. This is not a defect of this item.

## 7. Secrets — PASS

I searched the seven added or changed files, both their added lines and their whole contents at HEAD, case-insensitively for:

- `api_key`/`apikey`, `apiKey=`, `Authorization`, `Bearer`, `ODDS_API`;
- `token`, `secret`, `passw`;
- `http(s)://`;
- private-key headers and `ssh-ed25519 AAAA` / `ssh-rsa AAAA`;
- 32+ character opaque strings.

The files are `.claude/agents/backtest-verifier.md`, `BUILD_PLAN.md`, `CHANGELOG.md`, `CLAUDE.md`, `FPL_PLAN.md`, `prereg/S0b.md` and `worklog/verify_SMOKE2.md`.

- **Hits.** None is a secret:
  - the verifier's rule text "with apiKey=, or an Authorization header value" (agent file, BUILD_PLAN.md:139);
  - the pre-existing BUILD_PLAN.md:213 hook rule;
  - the export file name;
  - the projection-log sha256.
- **No URL** appears in any added line.
- **The deploy key's path** (`C:/Users/Boris/.ssh/fpl_deploy_ed25519`) appears in `prereg/S0b.md` and `CHANGELOG.md` as a path only. No key material is in any tracked file (`git grep` at HEAD), and no tracked file name looks like a key.
- **`ODDS_API_KEY`** is not set in this shell, so I could not search for the value itself.

## Acceptance tests (prereg/S0b.md)

1. **Verifier check 1 amended — PASS.**
   - **Same as the ruling.** The new check 1 in the agent file equals check 1 in Boris's ruling word for word (whitespace-normalised compare against the transcript). It has 1a truncation and 1b timestamp audit, both deciding, and 1c shift probe, warning only.
   - **Byte-identical to the BUILD_PLAN block.** The agent file and the fenced "Verifier agent" block of `BUILD_PLAN.md` are byte-identical at `01b67a3`, at `f9c43ee` and in the working tree (2,640 bytes, LF, sha256 `e4cfc97d8221df47…`, as the changelog says). They are also identical in a fresh autocrlf checkout (2,686 bytes, CRLF). At the base they were identical too (1,908 bytes).
   - **Nothing else in the agent text changed.** `git diff 4f4a7a0 01b67a3` of the agent file is one hunk, `@@ -15,4 +15,15 @@`, the old check 1 only.
   - **The changelog.** The `CHANGELOG.md` entry logs the amendment and cites "2026-09-14 — the ceiling on the starters question, measured" (CHANGELOG.md:840). That entry holds +0.023 (n = 5,839, 37 week-pairs), the ceiling ≈ 0.15 and the fixture term ~0.02–0.06. The S0b entry is a pure append (one hunk, 85 added lines, 0 removed), so no frozen entry was edited.
2. **SMOKE2 — PASS.**
   - **The native agent ran it.** The transcript shows an agent launch with `subagent_type: "backtest-verifier"` ("Verify SMOKE2 smoke test") at 17:49:59Z. That is after `01b67a3` (17:49:01Z) and after the scratch checkout (17:49:34Z).
   - **Branch, prereg and leak.** Commit `4a7c469` adds only `prereg/SMOKE2.md`, on top of `01b67a3`. Commit `f66ba8c` adds only `toy_eval.py`, which has `feature = pts[g]` and `target = pts[g]`.
   - **The branch is deleted.**
     - No local ref contains either commit; they survive only in HEAD's reflog (checkout to the scratch branch, the two commits, then "checkout: moving from scratch/verifier-smoke2 to master" at 17:58:21Z).
     - Neither file is on `master` or on disk.
     - `git ls-remote --heads origin` lists only `refs/heads/master` (`4f4a7a0`), and neither commit appears among the remote's refs.
   - **The verdict.** `worklog/verify_SMOKE2.md` reports VERDICT FAIL, with 1a FAIL and 1b FAIL (and 1c WARN, not cleared).
   - **I reproduced its numbers independently**, with my own CSV reader, de-duplication, deadline rule (90 minutes before the first kickoff in `fixtures.csv`) and Spearman:
     - merged_gw has 29,757 rows, 29,747 after de-duplication (0 conflicting duplicates). GW2-38 uses 29,057 rows, or 28,648 player-GWs.
     - **1b:** 29,057 of 29,057 rows fall after deadline(g). The gaps run from 1:30:00 to 8 days 2:00:00, with 0 kickoff mismatches and 0 event mismatches.
     - **1a:** none of the feature values can be rebuilt from round < g. At GW2 that is 0 of 705 (690 admissible player-GWs), at GW20 0 of 790 (14,175) and at GW38 0 of 841 (28,497). Reading a missing value as 0, 295, 286 and 302 values differ (max 24, 17 and 18 points).
     - **1c:** 5,669 pooled pairs. Unshifted 1.000000, shifted 0.024165 (`fpl_edge._spearman` agrees to 12 decimals: 0.024165372116). The shifted 90% CI, with the gameweek as the unit, 10,000 resamples and seed 20261017, is −0.002788..0.050639, identical to the report.
3. **CLAUDE.md, one stdlib rule — PASS.**
   - The line "Standard library only. No pip, no third-party dependencies." is present at `4f4a7a0` (line 15) and gone at HEAD.
   - The only standard-library rule left in CLAUDE.md is the work-item protocol's "Runner code is Python standard library only … `tools/`" (lines 37-38).
4. **FPL_PLAN.md — PASS.**
   - Line 1 of the committed blob is exactly the ruling's sentence.
   - The new blob equals that line plus LF plus the old blob, byte for byte (numstat 1/0).
   - The working tree differs only by the CRLF of this clone's autocrlf checkout, uniformly over all 134 lines.
5. **Push setup — PASS (the final push is still pending).**
   - `git config --show-origin` places `remote.origin.url` = `git@github.com:borisdanihel-dev/FPL.git` and `core.sshCommand` = `ssh -i C:/Users/Boris/.ssh/fpl_deploy_ed25519 -o IdentitiesOnly=yes` in `.git/config`. Both strings equal the prereg's.
   - The global config has no `core.sshCommand`, `url.*` or `remote.*` key. Its md5 is `0a3a74a4de76695260d95175836bf30c`, the main session's before/after value. I can only confirm the current value, not the before value.
   - `git ls-remote origin` works through this config.
   - No key material is in the repository (check 7).
   - The final push happens after this verdict, so I could not observe it. As instructed, I did not run the dry-run push.
6. **BUILD_PLAN Step 2 — PASS.**
   - Item 10, "Bench audit respects automatic substitutions", equals the ruling's text once the Markdown markers are stripped, including the test ("a starter on 0 minutes whose bench player came on shows no gain").
   - The verifier step is renumbered to 11.
   - The changelog's measurement holds: `exports/fpl_export_gw6_2026-10-16.json` has 0 occurrences of `automatic_subs`, and neither `fpl_sync.py` nor `fpl_edge.py` mentions it.
7. **Verifier write guard — PASS for the rule and for SMOKE2; the S0b record is still pending.**
   - **Where the rule is.** It is in the work-item protocol section of `CLAUDE.md` (line 48) and in Part B of `BUILD_PLAN.md` (line 44, between the Part B header at line 37 and Part C at line 46). Both wordings carry the ruling's content: `git status` and `git diff`, any change outside `worklog/verify_<item>.md` voids the verdict, revert and rerun.
   - **SMOKE2.** `CHANGELOG.md` records what the main session saw: only `?? worklog/verify_SMOKE2.md`, an empty `git diff`, and unchanged HEAD, worktree list, branches, stash and local config. The SMOKE2 report records its own clean status. I cannot rerun the main session's check, but the reflog sequence is consistent with it.
   - **S0b.** The main session's after-run check and its record in `worklog/cc_2026-10-17_S0b.md` come after this report. My own before/after snapshot is under "Write guard" below.
8. **Tests before and after — PASS.** 250 tests, green at `4f4a7a0`, `01b67a3` and `f9c43ee` (check 2). No `.py` file changed, and the recording path is byte-identical (check 5).

## Observations (not blocking)

- **No test guards the agent/BUILD_PLAN byte identity** (check 6, M1). A future amendment could leave the two out of step without anything going red.
- **`requirements.txt`'s comment still quotes the deleted CLAUDE.md wording** ("CLAUDE.md: \"stdlib only, no pip\""). It is now a stale cross-reference. The changelog discloses this and leaves it in place; the rule it enforces still holds (M5).
- **Push timing.** At 18:11 UTC the remote `master` is still `4f4a7a0`, so the push is a fast-forward. The nightly commits back to `master` at 21:40 UTC. A push after that needs a `git pull` first.
- **Still open for S0b to be done:**
  - the report `worklog/cc_2026-10-17_S0b.md`, which the ruling names;
  - the main session's write-guard record for this run;
  - the push.

## Write guard (this run)

- Before starting I snapshotted HEAD (`f9c43ee`), `git status --porcelain --untracked-files=all` (empty), `git diff`, `git diff --cached`, the worktree list, branches, stash, and the md5 of the local and global config.
- After all runs, and before writing this file, the same snapshot was byte-identical.
- `git status --ignored` showed only the pre-existing `fpl_export_gw3..6.json` and `historical/`, with no `__pycache__`.
- I added no worktree, did not commit, fetch, stash or switch branches, and changed no config. The only network operation was a read-only `git ls-remote`.
- The only file I wrote in the repository is this report, `worklog/verify_S0b.md`.

## VERDICT: PASS

- **Prereg order.** `prereg/S0b.md` was committed in `7e695c1`, alone, before the item's only change commit, and was never edited.
- **The changes match the ruling.** All eight acceptance tests hold against Boris's ruling as recorded in the session transcript:
  - check 1 is the ruling's text word for word, and the agent file and the BUILD_PLAN block are byte-identical in LF and CRLF form, with nothing else in the agent text changed;
  - the changelog cites the 2026-09-14 ceiling entry;
  - CLAUDE.md keeps only the runner-stdlib / `tools/` rule;
  - FPL_PLAN.md gains exactly the one line;
  - the Step 2 auto-sub item and the write guard are where the ruling puts them;
  - this clone's `.git/config` carries the prescribed origin and `sshCommand`, with no key material in the repository.
- **SMOKE2.** The native `backtest-verifier` agent ran the planted-leak smoke test after the amendment was committed and returned FAIL with 1a and 1b failing. I reproduced every figure in its report independently (29,057 of 29,057 rows after the deadline; 0 of 705/790/841 values rebuildable; 1c 1.000000 vs 0.024165, CI −0.002788..0.050639). Its branch exists neither locally nor on the remote.
- **Tests and recording path.** No `.py` file changed. The suite runs 250 tests, green, at the base and at HEAD. The GW7 projection log regenerates byte-identical (sha256 `f95a7228…`) under both codes, from the committed log and from a log stripped of GW7.
- **Mutations and secrets.** The one rule the item leaves standing is enforced by a test that goes red when broken. No secrets were found.
- **Not observable by me.** The final push and the main session's write-guard record come after this verdict. The lack of a test for the agent/BUILD_PLAN identity is noted as a gap, not a failure.
