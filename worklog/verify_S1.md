# Verifier report: S1, final verification (after the migration)

- **Verifier:** backtest-verifier (native). I read `.claude/agents/backtest-verifier.md` from disk first, and it governed this run.
- **Scope:**
  - every check the agent file requires for a data-pipeline item (1, 2, 5, 6, 7, plus the item's own acceptance tests; 3 and 4 are reported too);
  - BUILD_PLAN.md Step 1, points 1–7, as written at `5ad7f4c`;
  - every point of the S1 ruling and of Amendments 1, 2 and 3;
  - the "Re-check after the migration" list of `worklog/verify_S1_pre2.md`;
  - whether what landed on master equals what was pre-checked, and where it differs, whether the difference is tested.
- **Base / head:**
  - Base: `5ad7f4c` (master before S1). The rollback tag `pre-data-branch` is on `26f543a`.
  - Head: GitHub `master` = `81e2efa`, `data` = `e84bee6`.
  - Pre-checked code: `scratch/s1-wip` at `ba8cd36` (second pre-check). The local branch is now at `b738e6d` and was never pushed.
- **Rulings checked:** the verbatim `RULING S1:` block and Amendments 1, 2 and 3 in `prereg/S1.md`.
  - I read no session transcript or chat log.
  - I read `worklog/SESSION_STATE.md` and the earlier reports only as claims to test.
- **Scratch:**
  - All clones, test runs, mutations and rehearsals ran in `C:\Users\Boris\AppData\Local\Temp\s1_final_verify_20188\`. That folder has been deleted.
  - The only push target was a bare repository I created in that folder. Each clone's origin was repointed to it before any push.
  - Nothing was pushed to GitHub, `C:\GIT\FPL` or `C:\GIT\FPL-data`.
- **`C:\GIT\FPL` and `C:\GIT\FPL-data`, before and after this run:** identical.
  - Same refs, tags, worktrees and stash list (none).
  - Same sha256 of `.git/config`, `.git/hooks/pre-push` and `.git/packed-refs`.
  - Same status in both worktrees.
  - `git ls-remote` of GitHub is unchanged: master `81e2efa`, data `e84bee6`, tags `pre-data-branch` → `26f543a` and `backup-2026-10-17` → `e84bee6`.
  - The only new file is this report.
- **Network, all read-only:**
  - `api.github.com`: actions runs and jobs, releases, tags, repository activity and events;
  - `raw.githubusercontent.com`: the data URLs, the gitleaks-action source at the pinned SHA, and the gitleaks v8.24.3 source;
  - `git clone` / `fetch` / `ls-remote` of GitHub.
  - Job logs and artifacts need a sign-in, so I did not read them.
- **Masking:** every key-like string below shows only its first 4 characters, then "...". Commit ids are short ids.

## Prereg order (gate)

PASS.
- **Original ruling:** `3318b08` (18:58:24Z) adds only `prereg/S1.md`, +32 lines.
  - It precedes the first S1 change, Part 0 `53383fd` (18:59:07Z), and the first code commit, `bb8c9b2` (19:09:17Z, on the scratch branch).
  - It is an ancestor of the code commit on master, `dddcb92`.
- **Amendment 1** `a2bd8ef`, **Amendment 2** `12fa064` and **Amendment 3** `6fc54b8` (22:23:47Z) are each append-only: 0 removed lines in `prereg/S1.md`.
  - Amendment 3 precedes its change, `81e2efa` (22:41:26Z), which descends from it.
  - The only commits between the scan findings and Amendment 3 are `7e4bb0c` and `4661808`, both SESSION_STATE only.
- `prereg/S1.md` at `81e2efa` is byte-identical to `6fc54b8`. Nothing was edited after Amendment 3.

## Check 1: point-in-time leak check

PASS (not applicable; the evidence is that nothing is produced).
- The item produces no forecast, feature or evaluation metric.
- `git diff 5ad7f4c 81e2efa` is empty for `fpl_edge.py`, `p1_eval.py`, `fpl_ship.py`, `fpl_hist.py`, `watchlist.txt` and `requirements.txt`.
- So 1a and 1b have no input to rebuild, and 1c has no correlation to probe. Check 5 shows the recorded forecasts are unchanged.

## Check 2: clean-checkout test run

PASS. Every run used a fresh clone of GitHub and `python test_fpl.py` (Python 3.14.7).

| checkout | tests | result |
|---|---|---|
| `5ad7f4c` (before S1) | 253 | OK (skipped=2) |
| `pre-data-branch` = `26f543a` (before the code) | 253 | OK (skipped=2) |
| `dddcb92` code commit (data still on master) | 307 | OK (skipped=2) |
| `81e2efa` head, CRLF checkout | **308** | OK (skipped=3) |
| `81e2efa` head, LF checkout (`core.autocrlf=false`, `core.eol=lf`) | 308 | OK (skipped=3) |
| `81e2efa` with `FPL_DATA_DIR` = a `data` worktree after `--restore` | 308 | **OK, 0 skips** |
| proof dispatch on the runner (`eb3ef1e` code; read from `logs/run_2026-10-17.log` on `data`) | 307 | OK (skipped=11, the Windows-only tests) |

- **The skips at head:** the third skip is `test_the_real_database_has_only_expected_tables`, because master no longer holds `fpl.sqlite`. With the data folder set, nothing skips.
- **Count history:** 253 → 304 at the second pre-check → +3 in `b738e6d` → +1 in `81e2efa` = 308.
- **Test output is clean:** the four full runs (CRLF, LF, data, `dddcb92`) have 0 key-pattern lines, 0 hex strings of 32+ characters and 0 Authorization or Bearer lines.

## Check 3 and check 4

- **Check 3:** not applicable. The prereg has no evaluation, metric, bootstrap or threshold.
- **Check 4:** PASS.
  - Every template row is n/a, as allowed by `prereg/README.md` for a ruling-only data-pipeline item. Nothing was promoted or re-tuned.
  - All four rulings are present verbatim in `prereg/S1.md`, appended only.
  - Fidelity is judged point by point below.

## Check 5: recording path

PASS.
- **Frozen time.** A scratch `sitecustomize.py` replaced `datetime.datetime.now`, freezing time at 2026-10-18T12:00:00Z. That is before the GW8 deadline, 2026-10-23T17:30:00Z, read from `events.deadline_time` in the `data` copy of `fpl.sqlite`.
- **Same inputs, two layouts.** Both runs used the same data: `data` at `e84bee6`, with the working exports written by `--restore`.
  - (A) base code `26f543a` in one folder with the data;
  - (B) head code `81e2efa` run from its own folder, with the data folder as the working directory, exactly as `fpl_nightly.py` calls it.
- **Result.** Both gave RECORD OK own 275 / xg 260 / minutes 260 / bottomup 260.
  - Both logs have 4680 lines with sha256 `69d3f73b…`, and `cmp` finds them **byte-identical**. 1055 rows carry the frozen stamp.
  - The watch files are byte-identical too.
- **Cross-check with the real dispatch.** The regenerated log against the `e84bee6` log on GitHub:
  - the same 4679 keys;
  - all 3624 non-GW8 rows identical, `made_at` included;
  - GW8 maximum |Δ predicted| = 0.0, and 0 GW8 rows differ outside `made_at`.

## Check 6: mutation spot-check

PASS. 24 one-line mutations were made in an LF scratch clone at `81e2efa`.
- **All 24 went red.**
- Each file was restored and its sha256 verified, and `git status` was clean afterwards.
- The suite at that tree is the green 308 run above.

| # | file | mutation | red test |
|---|---|---|---|
| N1 | fpl_nightly | same-date tie: the plain `.json` beats the `.gz` | `test_on_one_date_the_gzipped_export_wins` |
| N2 | fpl_nightly | tie key dropped (listing order decides) | same |
| N3 | tools/migrate_data_branch | `*.sqlite binary` → `fpl.sqlite binary` | `test_the_migration_writes_the_data_branch_attributes` |
| N4 | fpl_gate | `check_log` loops over the last commit's gameweeks only | `test_a_new_block_for_a_past_gameweek_is_rejected` |
| N5 | nightly.yml | `runs-on: ubuntu-latest` | `test_schedule_runner_and_steps` |
| N6 | nightly.yml | `runs-on: ubuntu-22.04` | same |
| N7 | secret-scan.yml | cron minute 0 (a round minute) | `test_secret_scan_runs_the_pinned_gitleaks_action` |
| N8 | secret-scan.yml | cron on Mondays | same |
| N9 | secret-scan.yml | `fetch-depth: 1` | same |
| N10 | secret-scan.yml | a `ref:` re-added to the checkout | same |
| N11 | .gitleaksignore | the commit dropped (a file-wide fingerprint) | `test_gitleaksignore_holds_exact_fingerprints_only` |
| N12 | .gitleaksignore | a second fingerprint added | same |
| N13 | secret-scan.yml | weekly schedule removed | `test_secret_scan_runs_the_pinned_gitleaks_action` |
| N14 | fpl_gate | integrity result ignored | `test_a_database_that_reads_but_fails_integrity_check_is_rejected` |
| N15 | fpl_gate | `.gz` not decompressed | `test_a_key_inside_a_gzipped_export_fails_the_commit` +1 |
| N16 | fpl_publish | gate exit ignored | `test_a_failed_gate_commits_and_pushes_nothing` |
| N17 | fpl_prepush | deletions on master rejected | `test_a_code_push_and_the_migration_delete_pass` |
| N18 | nightly.yml | `force_backup` default true | `test_a_dispatch_can_force_the_backup` |
| N19 | fpl_nightly | gzip mtime not zeroed | `test_the_gzipped_archive_is_byte_stable` |
| N20 | fpl_gate | deadline comparison inverted | 5 DataGate log tests |
| N21 | fpl_gate | `GROW_ONLY = ("price_history",)` | `test_emptying_any_grow_only_table_is_rejected` +1 |
| N22 | fpl_gate | dump written with CRLF | `test_the_dump_rebuilds_the_database_row_for_row` |
| N23 | fpl_publish | `RETRIES = 0` | the rebase-and-land and rebase-conflict tests |
| N24 | nightly.yml | `cancel-in-progress: true` | `test_push_safety_and_least_privilege` |

- **Failure output of the mutations:**
  - no key pattern;
  - the only 32+ hex strings are commit ids echoed in assertion messages: the pinned action SHA (N5, N6, N9, N10, N13) and the `ea7acaa…` fingerprint commit (N11, N12).
- **Both survivors of the second pre-check (MA15, MA20) are now covered:** N3 and N4 went red.

## Check 7: secrets

PASS, with one ruled exception noted.
- **Files scanned.** The 20 files S1 adds or changes on master (`git diff --diff-filter=ACMR 5ad7f4c 81e2efa`), plus the `data` files the item created or changed:
  - `.gitattributes`, `.gitignore`;
  - `fpl.sql`;
  - the `.json.gz`, raw and decompressed;
  - the run log, the watch file and `projection_log.csv` at `e84bee6`.
- **Patterns:**
  - `api[_-]?key[=:]` and `?apikey=` in any case;
  - Authorization headers and Bearer values;
  - GitHub token shapes;
  - hex strings of 32+ characters.
- **Hits:**
  - `secret-scan.yml`: the pinned gitleaks-action commit SHA (`e0c4...`).
  - `.gitleaksignore` and `test_fpl.py`: the commit id `ea7acaa…` of the accepted fingerprint.
  - `worklog/verify_S1_pre.md` (the first pre-check report, added by S1 in `ea7acaa`):
    - lines 140, 141, 145, 251, 254 and 281 quote that report's dummy test fixtures;
    - these are URLs with a dummy key query whose values are "abc" or a dummy string (`ZZZ1...`), and the hand-written 32-hex test dummy (`f00d...`).
- **No real key value, no URL carrying a real key, and no Authorization header value** is in any scanned file. Every data file is clean, including the decompressed export.
- **The ruled exception.** Read literally, the old report holds "a URL with apiKey=". Those strings are dummies. The second pre-check listed them exactly (its O8). Amendment 3, point 1 then ruled that the report stays unedited and that only the line-281 finding is allowlisted.
  - `git diff ea7acaa 81e2efa -- worklog/verify_S1_pre.md` is empty, as ruled.
  - `worklog/SESSION_STATE.md` no longer quotes any fixture (0 hits).
- **A3.1, provenance of the line-281 string.** The 32-hex string at `ea7acaa:worklog/verify_S1_pre.md:281` is a literal in `test_the_key_value_fails_the_commit_and_is_never_printed`. That is line 4722 of `test_fpl.py` at `84a1bb0`, and the literal is also present at `bb8c9b2`, both local WIP commits. It is a hand-written fixture, not the key.
  - `ODDS_API_KEY` is not set in this shell, so a value comparison was not possible.

## What landed on master compared with what was pre-checked

- **The code commit is the scratch head, blob for blob.** `dddcb92` (single parent `26f543a`, no merge anywhere in `26f543a..81e2efa`) holds 12 files. All 12 blobs equal `scratch/s1-wip` `b738e6d`. `git diff b738e6d dddcb92` touches only the 6 data files of the "nightly 2026-10-17" commit.
- **`ba8cd36` → `b738e6d`** (the second pre-check's observations, made after its PASS):

  | file | change | tested by |
  |---|---|---|
  | `fpl_nightly.py` | `restore_exports` picks the newest date, and on one date the `.gz` beats the plain `.json` (O2) | new test; N1 and N2 red; seen live: `--restore` on a fresh `data` worktree took `fpl_export_gw7_2026-10-17.json.gz` over the same-date `.json` |
  | `test_fpl.py` | test for a new past-deadline block (O4/MA20), test for the data-branch attributes (O3/MA15), env tuple order (O9) | N3 and N4 red; O9 is behaviour-neutral |
  | `fpl_publish.py` | docstring only (O6) | none needed |
  | `CLAUDE.md` | secret-scan wording (O1) | docs |

- **`81e2efa`** (Amendment 3):

  | file | change | tested by |
  |---|---|---|
  | `nightly.yml` | `runs-on: ubuntu-24.04` | N5, N6 |
  | `secret-scan.yml` | the `branch` input and the checkout `ref` dropped; `schedule: "23 4 * * 0"` added | N7–N10, N13 |
  | `.gitleaksignore` | new: one exact fingerprint | N11, N12 |
  | `test_fpl.py` | pins all of the above | — |
  | `CLAUDE.md` | masking rule; secret-scan wording | docs |
  | `BUILD_PLAN.md` | Step 3 item 5 (action versions) | docs |

- **Unchanged since the pre-check** (`ba8cd36` = `81e2efa`, blob for blob): `fpl_gate.py`, `fpl_prepush.py`, `fpl_sync.py`, `tools/migrate_data_branch.py` and `.gitignore`. The second pre-check's real-data rehearsals of the gate and the hook therefore apply unchanged. I repeated the key ones below.

## Timeline (17 Oct, UTC)

Sources: GitHub's repository activity API, the actions runs and jobs API, and the local reflogs of `C:\GIT\FPL` (read-only).

| time | event |
|---|---|
| 21:57:05–21:57:45 | scheduled nightly run 39073052152 (old layout); bot push `e100932` → `26f543a` at 21:57:41 |
| 21:58:02 | local `git fetch` fast-forwards origin/master to `26f543a` ("nightly 2026-10-17") |
| 21:58:43 | `git pull --ff-only` to `26f543a`; the annotated tag `pre-data-branch` is created (tagger time 21:58:43) on `26f543a` |
| 21:58:44 | code commit `dddcb92` |
| 21:58:49 / 21:58:57 | `eeeede6` committed / GitHub `branch_creation` of `data` at `eeeede6` |
| 21:59:02 | migration commit `57abbf1`; `.git/hooks/pre-push` written at 21:59:02.6 |
| 21:59:37 | GitHub push of master `26f543a` → `57abbf1` (code and migration together, fast-forward) |
| 22:03:36–22:04:18 | proof dispatch 39073502058 at `eb3ef1e`; bot push of data `eeeede6` → `e84bee6` at 22:04:09; release published at 22:04:13 |
| 22:09:06, 22:09:43 | full-history secret-scan dispatches 39073872326 and 39073916594: failure (the O8 finding) |
| 22:42:00 | GitHub push of master → `81e2efa` (Amendment 3; runner path) |
| 22:46:00–22:46:17 | full-history secret-scan dispatch 39076383774 at `81e2efa`: **success** |

- **No force push:** the activity API records none.
- **No bot commit on master** after `26f543a`.
- **Unobservable:** the push time of the tag itself. Tag pushes are not in the activity API and have no reflog. The tag object predates both the code commit and the migration commit, and the tag is on GitHub at the right commit.

## Migration integrity (ruling point 4): before and after, side by side

Measured from the git objects on GitHub, by my own script and by `tools/migrate_data_branch.py measure` + `compare` (exit 0). Both agree.

| | before (master `dddcb92`) | after (first `data` commit `eeeede6`) |
|---|---|---|
| chips / entries / entry_gw / events | 12 / 7 / 49 / 38 | 12 / 7 / 49 / 38 |
| fixtures / picks / player_gw / player_history | 380 / 735 / 4550 / 1927 | 380 / 735 / 4550 / 1927 |
| players / price_history / standings / teams / transfers | 667 / 25214 / 42 / 20 / 67 | 667 / 25214 / 42 / 20 / 67 |
| projection_log.csv data rows | 4679 | 4679 |
| PRAGMA integrity_check | ok | ok |
| files: same (mode, blob) / same sha256 of stored bytes / same sha256 on disk | 103 | 103 / 103 / 103 |
| fpl.sqlite sha256 | `e33e6023…` | `e33e6023…` |
| projection_log.csv sha256 (stored / checked out) | `75fcf23c…` / `458e8452…` | `75fcf23c…` / `458e8452…` |

- **The first `data` commit is parentless.** Its 103 data paths equal exactly the 103 deletions of `57abbf1`, plus `.gitignore` and `.gitattributes`.
  - `.gitattributes` holds `*.sqlite binary`, `*.gz binary`, `fpl.sql -text` and `projection_log.csv text eol=crlf`.
  - `.gitignore` holds `/fpl_export_gw*.json`.
- **The migration commit `57abbf1` holds 103 deletions and nothing else.** GitHub master at `81e2efa` holds 0 data paths.
- **Boris's worktree.** In `C:\GIT\FPL-data` (read-only), the 99 files the dispatch did not touch are byte-identical on disk to a checkout of `dddcb92` with the same `autocrlf`. The 6 touched files equal the `e84bee6` blobs: identical for the binaries, and identical after CRLF normalisation for the text files.

## Proof dispatch (BUILD_PLAN 1.4 "Prove it"; ruling point 5; A2.8)

- **Run 39073502058** (workflow_dispatch, `eb3ef1e`): conclusion success, and every step success, including "Commit outputs to the data branch" and "Weekly backup".
  - The backup step ran on a Saturday (`date -u +%u` = 6). By the step's own condition, that is only possible with `force_backup` ticked.
- **Exactly one new `data` commit,** `e84bee6`, by github-actions[bot], with parent `eeeede6`:
  - added: `fpl.sql` and `exports/fpl_export_gw7_2026-10-17.json.gz`;
  - modified: `fpl.sqlite`, `logs/run_2026-10-17.log`, `projection_log.csv` and `reports/watch_2026-10-17.txt`.
- **The run log on `data`:**
  - "data dir: …/data";
  - 5 exports restored;
  - 307 tests OK;
  - RECORD OK 275 / 260 / 260 / 260;
  - ARCHIVE OK `.json.gz`;
  - "Done".
- **`fpl.sql`:** 2,148,759 bytes with 0 CR. A database rebuilt from it equals `fpl.sqlite` row for row in all 13 tables, and integrity is ok.
- **The `.json.gz`:** gzip flags 0 and mtime 0; it decompresses to a valid export.
- **No duplicate forecasts (ruling point 5):**
  - `projection_log.csv` has 4679 rows before and after, with 0 duplicate (source, event, player_id) keys;
  - per-gameweek counts are unchanged (GW4 527, GW5 1046, GW6 1001, GW7 1050, GW8 1055);
  - all 3624 past-deadline rows are identical, `made_at` included;
  - GW8 has the same 1055 keys, with |Δ predicted| = 0.0 and only `made_at` new.
  - The gate line "frozen forecasts unchanged" is in the job log, which I cannot read. The property it states is verified directly here.
- **`master` unchanged by the run:** no bot push to master after 21:57:41.

## Backup release (BUILD_PLAN 1.3; A2.8)

- **Release `backup-2026-10-17`** (target `data`, tag at `e84bee6`) holds 2 assets:
  - `fpl.sqlite`, 1,781,760 bytes, sha256 `51c906ab…`;
  - `fpl.sql`, 2,148,759 bytes, sha256 `7be2bac9…`.
  - Both digests equal the `e84bee6` blobs.
  - It is dated the 17th, not the 18th as the earlier re-check list expected, because the dispatch ran on Saturday with `force_backup`.
- **Step simulation.** I extracted the landed step's shell text and ran it with stub `gh` and `date`:

  | case | result |
  |---|---|
  | scheduled Saturday | skipped, 0 `gh` calls |
  | dispatch Saturday, unticked | skipped |
  | dispatch Saturday, **ticked** | `release create backup-2026-10-17 data/fpl.sqlite data/fpl.sql --target data`, then the 2 oldest of 10 listed backups deleted (newest 8 kept) |
  | scheduled Sunday | created |
  | dispatch Sunday, unticked | created |

## Raw URLs (ruling point 7)

Both return **HTTP 200 over plain HTTPS with no sign-in**, and the bytes equal the `e84bee6` blobs:
- `https://raw.githubusercontent.com/borisdanihel-dev/FPL/data/reports/watch_2026-10-17.txt` (6,277 bytes);
- `https://raw.githubusercontent.com/borisdanihel-dev/FPL/data/reports/fpl_2026-10-17.txt` (29,842 bytes).

The patterns `…/data/reports/watch_<date>.txt` and `…/data/reports/fpl_<date>.txt` are in CLAUDE.md. The old master URL now returns 404.

## Secret-scan runs (A1.6; Amendment 3)

- **Push-triggered runs, all success:** `57abbf1` (the migration push, covering `dddcb92` and `57abbf1`; O9 was not flagged), `eb3ef1e`, `7e4bb0c`, `4661808`, `6fc54b8` and `81e2efa`.
- **Full-history dispatches at `eb3ef1e`:** 2 failures, which SESSION_STATE attributes to one finding, `generic-api-key` at `ea7acaa:worklog/verify_S1_pre.md:281`. I cannot read the logs.
  - The fingerprint matches the gitleaks-action fingerprint format: commit:file:rule:line, the commit given in full.
- **Full-history dispatch at `81e2efa`** (39076383774): success. This is the single re-run Amendment 3, point 5 asks for.
- **Why a full scan covers every branch.** This comes from the source, not the logs:
  - at the pinned SHA (`e0c4...`, = tags `v3` and `v3.0.0` by `ls-remote`), `src/index.js` sends `workflow_dispatch` and `schedule` to `Scan` with no `--log-opts`;
  - gitleaks v8.24.3, the action's default version, then runs `git log -p -U0 --full-history --all` (`sources/git.go`);
  - `actions/checkout` with `fetch-depth: 0` fetches every branch and tag.
  - So `data` is in scope, and the green run covers it.
- **Not yet proven live:** the weekly schedule. Its first run is Sun 18 Oct 04:23 UTC.

## Rollback rehearsal (ruling point 6; F-B)

This ran in a clone of GitHub's state, with a bare origin I created and the hook installed by `python fpl_prepush.py --install`.
- **The hook.** A commit force-adding `reports/watch_2099-01-01.txt` was rejected with "PRE-PUSH REJECTED … data belongs on the data branch". A code-only commit was accepted.
- **The two-commit revert now conflicts.** The drafted text in `worklog/cc_2026-10-17_S1.md` reverts "the migration commit and the code commit". With `81e2efa` on top, `git revert 57abbf1 dddcb92` stops on conflicts:
  - modify/delete in `secret-scan.yml`;
  - content in `CLAUDE.md` and `test_fpl.py`.
- **A revert that works:** `git revert --no-edit 81e2efa 57abbf1 dddcb92`, newest first.
  - The resulting tree equals `pre-data-branch` in every code and data path. Only `prereg/S1.md`, `worklog/SESSION_STATE.md` and `worklog/verify_S1_pre2.md` differ.
  - A plain `git push` is refused: the hook execs `fpl_prepush.py`, which the revert removed ("can't open file").
  - `git push --no-verify origin master` landed, and origin master then equals the tag's tree outside prereg/worklog.

## Acceptance tests: BUILD_PLAN.md Step 1 (as at `5ad7f4c`, with the amendments)

| point | verdict | evidence |
|---|---|---|
| 1 integrity gate; commit nothing and exit ≠ 0; *test: a planted truncated database is rejected* | PASS | Unit test, and N14/N20/N21. On the real `e84bee6` data with landed code: a half-truncated `fpl.sqlite` → "GATE FAIL … not a readable database", publish exit 1, 0 staged, origin `data` unchanged. Table list per A1.2 |
| 2 nightly text dump `fpl.sql` (A1.3), iterdump, committed alongside; *test: rebuild, row counts match* | PASS | The real `fpl.sql` in `e84bee6` rebuilds every row of all 13 tables; N22. A clean gate on a fresh clone rewrote `fpl.sql` byte-identically |
| 3 weekly backup: Sundays, `backup-<date>`, keep 8 | PASS | Release with 2 matching assets (forced, Saturday); step simulation; N18. The first real Sunday is 18 Oct |
| 4 data branch: orphan; layout; byte-identical first commit; one master commit removes; `.gitignore`; runner layout; one `DATA_DIR` (A1.5); local worktree; prove it; raw URL | PASS | Migration table; `.gitignore` anchors every data path; nightly.yml checks out `data` into `./data` with `FPL_DATA_DIR: data`; only `fpl_nightly.py` among the scripts reads `FPL_DATA_DIR`; proof dispatch; raw URLs. Local pattern rehearsed (below) |
| 5 push safety: concurrency; fetch + rebase + push, 3 retries with jitter; `*.sqlite binary`; pre-push hook + installer | PASS | `concurrency: nightly-data`, `cancel-in-progress: false` (N24). `push()` pushes `HEAD:refs/heads/data` only, never forced, with `random.uniform(2,8)` jitter (N23). `data:.gitattributes`. Hook rehearsal; hook installed in `C:\GIT\FPL` before the migration push |
| 6 secret hygiene: key value / `apiKey=` in staged files fail the commit; no full URLs logged; `contents: write` on the pushing job only; triggers schedule + dispatch; full-history gitleaks, findings without values (A1.6) | PASS | On real data with landed code, through `fpl_publish.py`: a staged `.json.gz` holding a URL with the key pattern, and separately one holding a random 32-hex value with `ODDS_API_KEY` set to it, each gave "SECRET FAIL … NOTHING COMMITTED TONIGHT", exit 1, 0 staged, origin unchanged, value never printed. `fpl_sync.py` prints the path only. `permissions: {}` at the top with one `contents: write`. Gitleaks: one finding, a dummy, allowlisted, re-scan green |
| 7 verifier → report → commit → push | in progress | This report. The implementer's report, changelog and push follow |

## Acceptance tests: RULING S1, points 1–8

| # | verdict | evidence |
|---|---|---|
| 1 9d source = `fpl.sqlite events.deadline_time` | PASS | CLAUDE.md line 69 |
| 2 "One item at a time…" in CLAUDE.md and the BUILD_PLAN.md standing rules | PASS | CLAUDE.md line 35, BUILD_PLAN.md line 15; "One step per session" is in neither |
| 3 ruling-only prereg rule in `prereg/README.md` | PASS | the two sentences, verbatim |
| 4 counts and sha256 before and after; byte-identical first data commit; side by side in the report | PASS (data); the side-by-side table is for the report | migration table above |
| 5 the dispatch does not duplicate forecasts | PASS | 0 duplicate keys; past-deadline rows identical |
| 6 tag `pre-data-branch` on master before the migration, pushed; the report says how to revert | PASS for the tag; **revert text pending, and it must change** | Tag object 21:58:43Z on `26f543a`, on GitHub. Its push time is unobservable. The drafted two-commit revert now conflicts; see the rollback rehearsal |
| 7 raw URL pattern; one fetches without sign-in | PASS | both fetch, HTTP 200 |
| 8 (as replaced by A2.7) nothing half-migrated, timing | PASS | `data` was created 40 s before the master push, with no run in between; master got the code and the migration in one push |

## Acceptance tests: Amendment 1

| # | verdict | evidence |
|---|---|---|
| 1 value check where `ODDS_API_KEY` is set; pattern check always (`apiKey=`, `api_key=`, `apikey=`, any case); no key to the runner before Step 5 | PASS | `KEY_PATTERNS` matched on lowercased bytes, with the value from the environment; real-data probes above. nightly.yml has no `secrets.` reference |
| 2 gate fails on a missing table, a failed integrity check, or a shrinking grow-only table; `EXPECTED_TABLES` in `fpl_gate.py`; no override flag | PASS | argparse has only `data_dir` and `--secrets`; N14, N21; projection-log part per A2.3 |
| 3 `fpl.sql`; no `prices.sql` in BUILD_PLAN.md, CLAUDE.md or the workflow | PASS | grep: 0 hits in BUILD_PLAN.md, CLAUDE.md, `.github/`, the scripts and the tests |
| 4 hook allows deletions on master, rejects adds and changes | PASS | N17; rehearsal |
| 5 `FPL_DATA_DIR` read by `fpl_nightly.py` only; local pattern documented | PASS | Only `fpl_nightly.py` and `test_fpl.py` (to find data, as documented) mention it. CLAUDE.md lines 90–109 |
| 6 `secret-scan.yml`, official action pinned to a full SHA; push to master and data plus dispatch; README read; no licence for a personal account | PASS | `push: branches: [master, data]`, dispatch, and the A3 schedule. Green runs without a licence |
| 7 that night's plan | superseded by A2's order | — |

## Acceptance tests: Amendment 2

| # | verdict | evidence |
|---|---|---|
| 1 the secret scan decompresses `.gz` | PASS | N15; real-data gz probes |
| 2 `--restore` writes only the untracked working exports, commits nothing; CLAUDE.md local commands start with it; no gzip loader in `fpl_edge.py`; `p1_eval.py` frozen | PASS | Rehearsed on a fresh `data` worktree with upstream `origin/data`: `git pull` "Already up to date"; `--section calibration` failed before restore; `--restore` wrote 5 ignored exports with status clean, and a second run wrote 0; then `--section calibration`, `--diff` and frozen `p1_eval.py fpl_export_gw3.json fpl_export_gw5.json` exited 0 with status still clean; tests with `FPL_DATA_DIR` 308 OK, 0 skips. `fpl_edge.py` has no `gzip`; `p1_eval.py` is unchanged since `5ad7f4c` |
| 3 gate fails on missing or changed past-deadline rows vs the previous data commit; grow-only only where `fpl_sync.py` never deletes, with evidence | PASS; the per-table listing is for the report | On real data, one GW7 row removed → "GW7 is past its deadline and its rows changed (1 missing or changed, 0 added)", nothing committed. A GW8 change (open) published to my bare `data` only. N4 and N20. Grow-only evidence below |
| 4 fake keys built at runtime; no key-like literal in files or test output; a block fails loudly | PASS, with the ruled O8 exception | Check 7. `::error` annotation pinned by a test; no `continue-on-error` |
| 5 9d runner path = "anything the nightly workflow runs or imports" | PASS | CLAUDE.md line 69 |
| 6 one byte-identical commit, never a merge; tag on the pulled master before it; `*.sqlite binary` | PASS | `dddcb92` = `b738e6d` blobs, single parent, no merges; tag 21:58:43Z, before `dddcb92` at 21:58:44Z, on the pulled `26f543a`; `data:.gitattributes` |
| 7 runner-path pushes never between 21:00 UTC and the end of that night's nightly, never within 30 h of a deadline | PASS | The nightly ended 21:57:45Z; runner-path pushes at 21:59:37Z and 22:42:00Z. GW8 deadline 2026-10-23T17:30Z, so the window opens 2026-10-22T11:30Z |
| 8 `force_backup` boolean, default false, backs up regardless of weekday; used by the proof dispatch | PASS | nightly.yml lines 19–23 and 83–85; N18; Saturday release |
| 9 every other pre-check finding fixed as recommended, each listed in the report | PASS for the fixes; **the listing is for the report** | table below |
| Order: no migration before fetch shows "nightly 2026-10-17"; then pull, tag, code commit, migrate, push; dispatch with `force_backup`; final verifier | PASS | timeline |

**Grow-only evidence (A2.3), checked at `81e2efa`.**
- **No deletes.** `fpl_sync.py` has no DELETE, DROP, TRUNCATE or VACUUM, and no UNIQUE constraint. It has 13 `CREATE TABLE` statements.
- **Writes.** Every write is `INSERT OR REPLACE`:
  - `teams` l.175;
  - `price_history` l.202;
  - `players` l.204;
  - `events` l.208;
  - `fixtures` l.222;
  - `player_gw` l.249;
  - `player_history` l.280;
  - `entries` l.294;
  - `standings` l.296;
  - `chips` l.308;
  - `transfers` l.312;
  - `entry_gw` l.325;
  - `picks` l.329.
- **The list follows.** `GROW_ONLY = tuple(sorted(EXPECTED_TABLES))` (all 13).
- **One reading, recorded in a `fpl_gate.py` comment.** The rule says "never deletes", which the implementer reads as "the count can never fall": `INSERT OR REPLACE` deletes only the one row it then replaces. The report should state this reading.

## Acceptance tests: Amendment 3

| # | verdict | evidence |
|---|---|---|
| 1 confirm the line-281 string is not the key; `.gitleaksignore` with exactly that fingerprint; old report unedited | PASS | Check 7 provenance; `ea7acaa…:worklog/verify_S1_pre.md:generic-api-key:281` is the only non-comment line; test-pinned (N11, N12); old report unchanged |
| 2 masking rule in CLAUDE.md now; the verifier block gets it in the closing ruling | PASS (CLAUDE.md lines 56–57); the verifier-block part is for the closing ruling | the agent file is unchanged in S1, as expected |
| 3 `branch` input dropped; weekly Sunday schedule at a non-round minute, UTC, full history of all branches | PASS | `cron: "23 4 * * 0"`; no `inputs` and no `ref:`; `fetch-depth: 0`; scope from source (above) |
| 4 nightly `runs-on` pinned to the image the runs used; action bumps become a Step 3 item | PASS | `runs-on: ubuntu-24.04`, matching the image Boris read (ubuntu-24.04, 20261012.334.1). The jobs API shows the 17 Oct runs requested `ubuntu-latest`; the image version is in the signed-in log only. BUILD_PLAN.md Step 3, item 5 |
| 5 9d timing; one full-history re-run, green; then final verifier | PASS | `81e2efa` pushed at 22:42:00Z, after the nightly; run 39076383774 success |

## Re-check list of the second pre-check

| # | status |
|---|---|
| 1 before/after counts, `compare` exit 0, parentless first commit with the same blobs, `*.sqlite binary` | done, PASS |
| 2 tag on the fetched "nightly 2026-10-17"; code commit's only parent; 12 blobs vs the pre-check; no merge | PASS; the blobs equal `b738e6d`, and the delta from `ba8cd36` is listed and tested above |
| 3 migration deletions only; hook installed; no data path on GitHub master; timing | PASS (hook file written 35 s before the push) |
| 4 F-A: `data` tracks `origin/data`; `pull`, `--restore`, calibration | PASS: `git -C C:\GIT\FPL rev-parse --abbrev-ref data@{upstream}` = `origin/data`; the pattern was rehearsed in a clone |
| 5 proof dispatch: green, one data commit with `fpl.sql` and the `.json.gz`, master unchanged, 0 duplicates, frozen forecasts unchanged | PASS (the gate line itself is unreadable; the property is verified) |
| 6 backup with 2 assets | PASS (`backup-2026-10-17`) |
| 7 raw URL | PASS |
| 8 secret scans | PASS after Amendment 3 |
| 9 report contents | pending; see below |

**The second pre-check's findings and observations:**
- F-A: fixed.
- F-B: still open for the report text.
- O1: answered by the A3 weekly scan.
- O2, O3, O4: fixed and tested.
- O5: unchanged (documentation only).
- O6: fixed.
- O7: the report is still to be written.
- O8: ruled by A3.1.
- O9: the scan was green.

## What the implementer's report must carry (not yet written; it comes after this verifier)

1. **The before/after table** (ruling point 4). The one above may be used.
2. **The revert text (ruling point 6), corrected:**
   - revert every S1 commit on master that touches code, newest first. Today that is `git revert --no-edit 81e2efa 57abbf1 dddcb92`;
   - push with `git push --no-verify origin master`, or delete `.git\hooks\pre-push` first;
   - copy back by hand any data the runner committed to `data` after `26f543a`, before the next nightly.
   - The drafted two-commit revert now conflicts.
3. **The A2.9 list** of every first-pre-check finding and how it was handled. Also the A2.3 per-table grow-only evidence, with the "count never falls" reading.
4. **The gitleaks findings, without values** (Step 1.6): one finding (`generic-api-key`, `ea7acaa`, `worklog/verify_S1_pre.md:281`), a test dummy, allowlisted by A3.1; the re-scan is green.
5. **The raw URL patterns,** and the `fpl.sql` name throughout. The old plan text in `cc_2026-10-17_S1.md` still says `prices.sql` and has the old step order (O7).

## Observations (none decides the verdict)

- **P1. The `ubuntu-24.04` pin has not run yet.** The proof dispatch ran before `81e2efa`, as A3.4 allows. The first run on the pinned label is tonight's scheduled nightly (18 Oct 21:40 UTC). Check that it is green.
- **P2. The weekly secret scan has not run yet** (first: 18 Oct 04:23 UTC). Its code path is the same `Scan` call as the green dispatch. `secret-scan.yml` still uses `runs-on: ubuntu-latest`; only the nightly was ruled to be pinned.
- **P3. Changes after the PASS.** The second pre-check's observation fixes (`b738e6d`, +60/−9 in 4 files) were made after that PASS and landed without another pre-check. They are verified here: every behavioural line has a mutation that goes red.
- **P4. BUILD_PLAN.md Step 1.6 still says "Run gitleaks once locally".** A1.6 replaced this with the workflow. CLAUDE.md line 9 still says the nightly output is "committed back" without naming `data`. Both are docs only.
- **P5. The Sunday-only path** (scheduled run, `%u` = 7) is proven by simulation only. The real release came from the forced Saturday dispatch. The first real Sunday is 18 Oct.

VERDICT: PASS

S1 is done as ruled on everything a verifier can check before the implementer's report. The prereg and its three amendments were each committed before the code they govern, and all are append-only. The code reached master as one non-merge commit, `dddcb92`, blob-identical to `b738e6d` and parented on the fetched "nightly 2026-10-17" (`26f543a`), which the rollback tag marks. The orphan `data` commit holds all 103 data files with identical blobs, row counts and sha256, and the master migration commit holds deletions only. The proof dispatch was green, added exactly one `data` commit holding `fpl.sql` and the `.json.gz`, left master untouched, duplicated no forecast and changed no past-deadline row. The forced backup holds both files, with digests equal to that commit. Both raw URLs serve without sign-in. The full-history secret scan is green after the exact `.gitleaksignore` entry. The suite went from 253 to 308 tests, green in CRLF, LF and against real data with 0 skips, and all 24 one-line mutations went red, including every change made after the second pre-check. Forecasts regenerated at a frozen time are byte-identical between the old and new layouts and match the dispatch's rows. Every runner-path push fell outside the 9d windows. Two things remain for the implementer's report, not the code: the side-by-side table, and a corrected revert procedure. That procedure must revert `81e2efa 57abbf1 dddcb92` newest first and push with `--no-verify`; the drafted two-commit revert now conflicts.
