# Verifier report: S1, pre-check (before the migration)

- **Verifier:** backtest-verifier (native). `.claude/agents/backtest-verifier.md`
  was read from disk first and governed this run.
- **Scope:** what can be checked before the migration. The following happen
  on Sun 18 Oct and are **out of scope**, not counted as failures here:
  - the real tag;
  - the `data` branch on GitHub;
  - the migration commit on `master`;
  - the proof dispatch;
  - the Sunday backup release;
  - the raw URL on `data`;
  - the gitleaks workflow run.
- **Base / head:**
  - Base is `a2bd8ef` (master, pushed).
  - Head is `scratch/s1-wip` = `84a1bb0`, local only.
  - Item code commits: `bb8c9b2`, `1d1ce09`, `f9fb17b`, `ca8821c`, the merge `ff81c57`, then `c93b327` and `84a1bb0`.
- **Rulings checked:** the verbatim `RULING S1:` block and `Amendment 1` in
  `prereg/S1.md`. No session transcript or chat log was read. The worklog
  reports were read only to learn what the implementer claimed.
- **Scratch:** every clone, test run, mutation and rehearsal ran in
  `C:\Users\Boris\AppData\Local\Temp\s1_pre_verify_883\`, which was deleted
  afterwards. The rehearsal's origin was a bare repository in that folder,
  and every clone's push URL was repointed before any push.
  - Nothing was pushed to GitHub or to `C:\GIT\FPL`.
  - `C:\GIT\FPL` refs, worktrees, stashes, hooks and `.git/config` (sha256
    `f8ba8a87…`) were checked unchanged at the end.
- **Network, read-only:**
  - the public FPL API, through the rehearsal nightly;
  - `git ls-remote` over HTTPS for borisdanihel-dev/FPL and gitleaks/gitleaks-action;
  - `raw.githubusercontent.com` for the action's README, `action.yml` and `src/index.js` at the pinned SHA, and for the master watch file;
  - `api.github.com/users/borisdanihel-dev`.

## Prereg order (gate)

PASS.
- `3318b08` holds only `prereg/S1.md` (+32 lines) and is dated 20:58:24. It is an ancestor of
  `bb8c9b2`, the first code commit (21:09:17), and of Part 0 (`53383fd`, 20:59:07).
- Amendment 1 is `a2bd8ef` (21:37:36): +12 lines appended, 0 lines of the original ruling changed.
  - It answers decisions raised in `6f272df` (21:22:53).
  - No S1 code commit lies between those two.
  - It is an ancestor of `c93b327` and `84a1bb0` (via the merge `ff81c57`).
- `git diff a2bd8ef 84a1bb0 -- prereg/` is empty.

## Check 1: point-in-time leak check

PASS (not applicable; the evidence is that nothing is produced).
- The item produces no forecast, feature or evaluation metric.
- `fpl_edge.py`, `fpl_ship.py`, `fpl_hist.py` and `p1_eval.py` are unchanged (`git diff --quiet`).
- What changed in the recording path is the orchestration only: the working folder and the data folder. Check 5 shows the forecasts are unchanged.
- 1a and 1b have no input to rebuild. 1c has no correlation metric to probe.

## Check 2: clean-checkout test run

PASS. Each run used a fresh clone and `python test_fpl.py` (Python 3.14.7).

| checkout | tests | result |
|---|---|---|
| `a2bd8ef` (before) | 253 | OK (skipped=2) |
| `84a1bb0` (after), CRLF checkout | 288 | OK (skipped=2) |
| `84a1bb0`, LF checkout (`core.autocrlf=false`, `core.eol=lf`, as on the runner) | 288 | OK (skipped=2) |
| `84a1bb0` LF, `FPL_DATA_DIR` = rehearsal data worktree (working exports restored by the nightly) | 288 | OK (0 skips) |
| inside the rehearsal nightly (code from the branch, data from the worktree) | 288 | OK |

- **Added: 37 tests.** `DataGate` 15, `NightlyWorkflow` 6, `PrePush` 6, `Publish` 6, `NightlyRunner` 3, `SyncNetwork` 1.
- **Removed: 2 tests.** Both asserted the old layout and were replaced:
  - `test_outputs_are_committed_back_even_from_a_red_run`;
  - `test_ignore_and_attribute_rules_fit_two_writers` ("fpl.sqlite must be committed" on master).
- The 2 skips are the real-export tests ("no real export in this folder"), the same before and after.

## Check 3 and check 4

- **Check 3:** not applicable. The prereg has no evaluation, metric, bootstrap or threshold.
- **Check 4:** nothing was promoted or re-tuned.
- Ruling fidelity is judged per point under "Acceptance tests" below. One point (A1.2) is not implemented as ruled.

## Check 5: recording path

PASS.
- **Frozen-time regeneration.**
  - `datetime.now` was frozen at 2026-10-17T21:00:00Z by a scratch wrapper, before the GW8 deadline of 2026-10-23T17:30Z.
  - All four sources were regenerated from the same export (`exports/fpl_export_gw7_2026-10-17.json`) and the same starting log, in two layouts:
    - (a) base `a2bd8ef`, code and data in one folder;
    - (b) head code in one folder, run from a separate data folder, as `fpl_nightly.py` now does.
  - Both layouts gave RECORD OK own 275, xg 260, minutes 260, bottomup 260.
  - Both logs are 4680 lines with sha256 `8c045aab…0509737`. `cmp` finds them **byte-identical**.
- **Cross-check with a real nightly.** The rehearsal ran the base-code nightly ("simulated overnight nightly", committed as `4690a10`).
  - The regenerated GW8 rows match it: the same 1055 keys and 0 predicted values differing by more than 1e-9.
  - All 3624 non-GW8 rows are identical, including `made_at`.
  - The head nightly in the data-branch layout (below) gave the same 1055 keys and values.
  - Its watch file differs only in the two timestamps on line 1.

## Check 6: mutation spot-check

PASS. 28 one-line mutations were made in a scratch clone at `84a1bb0`.
- Every one turned its test class red.
- Each was restored (sha256 identical) and went green again.
- The full suite after restoring: 288 OK (skipped=2).

| # | file | mutation | red test |
|---|---|---|---|
| M1 | fpl_gate | integrity result ignored | `test_a_database_that_reads_but_fails_integrity_check_is_rejected` |
| M2 | fpl_gate | price-row fall tolerated (−10) | `test_fewer_price_rows_than_the_last_commit_is_rejected` |
| M3 | fpl_gate | `api_key=` pattern dropped | `test_api_key_and_apikey_in_any_case_fail_the_commit` |
| M4 | fpl_gate | unexpected-table check removed | `test_a_new_table_outside_the_expected_list_is_rejected` |
| M5 | fpl_gate | dump written with CRLF | `test_the_dump_rebuilds_the_database_row_for_row` |
| M6 | fpl_gate | pattern match case-sensitive | 3 secret tests |
| M7b | fpl_gate | key value printed in the FAIL line | `test_the_key_value_fails_the_commit_and_is_never_printed` |
| M27 | fpl_gate | key-value match removed | same |
| M24 | fpl_gate | `transfers` dropped from EXPECTED_TABLES | `test_the_expected_list_is_exactly_the_sync_schema` +2 |
| M25 | fpl_gate | "no DB in last commit" passes | `test_no_database_in_the_last_commit_is_rejected` |
| M8 | fpl_prepush | deletions rejected | `test_a_code_push_and_the_migration_delete_pass` |
| M9 | fpl_prepush | every branch checked | `test_data_may_go_to_the_data_branch` +1 |
| M10 | fpl_prepush | hook calls a relative script | 5 PrePush tests |
| M11 | fpl_publish | `--force` push | rebase and conflict tests |
| M12 | fpl_publish | `RETRIES = 0` | same |
| M13 | fpl_publish | rebase skipped | same |
| M14 | fpl_publish | no unstage after a secret hit | `test_a_staged_secret_commits_nothing_and_unstages` |
| M15 | fpl_nightly | archive as plain `.json` | 3 NightlyRunner tests |
| M16 | fpl_nightly | gzip mtime not zeroed | `test_the_gzipped_archive_is_byte_stable` |
| M17 | fpl_nightly | `FPL_DATA_DIR` ignored | `test_the_data_dir_comes_from_fpl_data_dir` |
| M18 | fpl_nightly | steps run in the code folder | `test_code_and_data_live_apart` |
| M26 | fpl_nightly | gz exports not restored | `test_fresh_checkout_restores_the_newest_dated_export_per_gameweek` |
| M19 | fpl_sync | full URL logged | `test_the_log_names_the_path_never_the_full_url` |
| M20 | nightly.yml | `cancel-in-progress: true` | `test_push_safety_and_least_privilege` |
| M21 | nightly.yml | keep 9 backups | `test_weekly_backup_on_sundays_keeps_the_last_eight` |
| M22 | secret-scan.yml | action pinned to tag `v3` | `test_secret_scan_runs_the_pinned_gitleaks_action` |
| M23 | .gitignore | `/projection_log.csv` removed | `test_master_ignores_every_data_path` |

`tools/migrate_data_branch.py` has no unit tests. It is a one-time local tool, verified here by the rehearsal:
- `compare` exits 1 and flags a changed row count and a changed sha256;
- a second `build` refuses ("refs/heads/data already exists").

## Check 7: secrets

PASS, with a literal-match note.
- **Files scanned:** the 12 files the item adds or changes against `a2bd8ef`, plus every added line of the diff.
- **Patterns:** `apikey=` / `api_key=` in any case; `authorization`, `bearer`, `x-api-key`, `token=`; tokens of 24+ hex or 40+ characters.
- **Hits, apart from rule prose:**
  - Test fixtures carrying the dummy value `abc`: `"GET https://api.example/odds?ApiKey=abc"`, `"GET /odds?apiKey=abc"`, `"export API_KEY=abc"`, `"url?apikey=abc"`, `"Api_Key=abc"`.
  - The 32-hex dummy key `f00dfacecafe1234567890abcdef0000` in `test_the_key_value_fails_the_commit_and_is_never_printed`.
  - The gitleaks-action commit SHA.
  - `${{ github.token }}` references, which are not secret values.
- **No real key, and no URL carrying one, in any file.**
- **Literal-match note:** the fixture `https://api.example/odds?ApiKey=abc` is, word for word, "a URL with apiKey=" (case-insensitive). It is a dummy needed to test the scanner. If Boris wants the literal rule, build the string at runtime.
- `ODDS_API_KEY` is not set in this shell, so a key-value scan was not possible.
- See finding F4 on gitleaks and the 32-hex fixture.

## Rehearsal (throwaway clone, own bare origin)

1. **Setup.**
   - A bare repository `origin.git` received `master` = `a2bd8ef` only.
   - A clone `mig` had its origin repointed to it and stale remote-tracking refs pruned.
2. **Simulated overnight nightly.** The **base** `fpl_nightly.py` ran against the live API (exit 0; RECORD OK 275/260/260/260). It was committed as the old workflow does and pushed to origin `master` (`4690a10`, 6 data files).
3. **Code onto master.** In `mig`, `git pull`, then a byte-identical copy of the 12 changed files from `84a1bb0` as one commit (`e7e549f`).
   - Outside data paths, `git diff 84a1bb0 e7e549f` is empty.
   - Tests: 288 OK.
4. **Measure before, tag, build.**
   - `measure` before at `e7e549f`.
   - Tag `pre-data-branch`, pushed to origin.
   - `tools/migrate_data_branch.py build` gave `8299fe1`: **no parent** (orphan), 103 data files + `.gitignore` + `.gitattributes`, "blobs identical: True".
   - `data` pushed.
5. **Independent byte check.** I did not rely on the tool for this:
   - All 103 (path, blob id) pairs of `data` equal those of `master` at `e7e549f` (`diff` empty).
   - Master keeps only code, docs, `watchlist.txt`, `prereg/`, `worklog/`, `CHANGELOG.md` and the agent file.
6. **Worktree and compare.** `git worktree add FPL-data data`, `measure` after, `compare` exit 0. Before and after, side by side (ruling point 4):

   | | before (master `e7e549f`) | after (data worktree) |
   |---|---|---|
   | chips / entries / entry_gw / events | 12 / 7 / 49 / 38 | 12 / 7 / 49 / 38 |
   | fixtures / picks / player_gw / player_history | 380 / 735 / 4550 / 1927 | identical |
   | players / **price_history** / standings / teams / transfers | 667 / **25214** / 42 / 20 / 67 | identical |
   | projection_log.csv data rows | 4679 | 4679 |
   | integrity_check | ok | ok |
   | files: same blob / same sha256 stored / same sha256 on disk | 103 | 103 / 103 / 103 |

   - My own row-count script gave the same counts.
   - My own `sha256sum` over the 103 checked-out files matched: fpl.sqlite `ae634137…`, projection_log.csv `92a01096…`.
7. **Migration commit and hook.**
   - Migration commit on `master`: 103 deletions only.
   - `python fpl_prepush.py --install`, then push `master` (code + migration together): accepted.
   - A follow-up commit force-adding `reports/watch_2099-01-01.txt` to master was **rejected** by the hook ("PRE-PUSH REJECTED … data belongs on the data branch").
8. **Nightly and publish.** Code from `mig`, data `FPL_DATA_DIR` = the worktree, live API.
   - Exit 0 in 44 s.
   - "data dir:" logged; 5 exports restored; tests 288 OK in the code folder; RECORD OK own 275 / xg 260 / minutes 260 / bottomup 260.
   - `ARCHIVE OK … fpl_export_gw7_2026-10-17.json.gz`.
   - The code folder had no new file, not even an ignored one.
   - `fpl_publish.py`: `GATE OK … 13 tables, price_history 25214 rows; fpl.sql written`, `SECRETS OK`, `PUSH OK origin data`.
   - The data commit `d463c61` has parent `8299fe1` and holds 6 files: the `.json.gz`, `fpl.sql`, `fpl.sqlite`, the log, `projection_log.csv` and the watch file.
   - **origin `master` unchanged** (`2ed6277` before and after).
9. **Dump (Step 1.2) on real data.**
   - The committed `fpl.sql` is 2,148,725 bytes and 33,762 lines, with **0 CR**.
   - A database rebuilt from it has 13 tables, and **every row is equal** to the committed `fpl.sqlite`.
   - The committed `.json.gz` has gzip flags 0 and mtime 0, and decompresses to the working export byte for byte.
10. **Gate on real data.** Every failing case left `fpl.sql` and the remote untouched.
    - A planted half-truncated `fpl.sqlite`: "not a readable database", exit 1, 0 commits, origin `data` unchanged.
    - One price row deleted: FAIL "rows fell from 25214 to 25213".
    - New table `odds_cache`: FAIL "not in EXPECTED_TABLES".
    - `standings` dropped: FAIL "tables missing".
    - All `picks` rows deleted: **passes**. Only `price_history` is protected.
11. **Ruling point 5 (no duplicate forecasts).** The head nightly re-recorded GW8 on a day it was already recorded.
    - Rows went 4679 → 4679, with 0 duplicate (source, event, player_id) keys.
    - Each of the four GW8 blocks kept its count and got the new `made_at`.
    - All 3624 other rows are byte-identical.
    - The record step replaces and does not append, so the dispatch can record normally.
12. **Merge-commit variant.** Code merged into a master that already has the overnight nightly:
    - the hook flags 6 data paths in the merge commit (diffed against the wip parent) and would **reject** that push;
    - the implementer's plan (a byte-identical single commit) passes, as step 7 showed.

## Acceptance tests: BUILD_PLAN.md Step 1 (as at `5ad7f4c`, amended by A1)

| point | verdict | evidence |
|---|---|---|
| 1 integrity gate (integrity ok; price rows never fall; table list per A1.2); fail = commit nothing, exit ≠ 0; test: truncated DB rejected | PASS | `DataGate` tests (M1, M2, M4, M25); rehearsal 10: a real truncated DB is rejected and nothing is committed or pushed |
| 2 nightly text dump (`fpl.sql` per A1.3), iterdump, committed alongside; test: rebuild, row counts match | PASS | unit test + rehearsal 9: every row equal; LF only; committed in the same commit as `fpl.sqlite` |
| 3 weekly backup, Sundays, `backup-<date>`, keep 8 | PASS as built; **proof out of scope** | the workflow step is pinned by a test (M21). It runs only after a successful publish, uploads `data/fpl.sqlite` and `data/fpl.sql`, and deletes `backup-*` beyond the newest 8. First proof is the Sunday dispatch |
| 4 data branch: orphan; what moves where; byte-identical first commit; one master commit removes; `.gitignore`; runner layout; one DATA_DIR (A1.5); local worktree documented; prove it; raw URL | PASS except "Local" (**FAIL, F2**); proof and raw URL **out of scope** | rehearsal 4–8; the `.gitignore` test (M23); the workflow tests. The documented local pattern fails on a data worktree (F2) |
| 5 push safety: concurrency; fetch + rebase + push, 3 retries with jitter; `.gitattributes`; pre-push hook + installer | PASS (note F7) | M11–M13, M20; `Publish` tests with a bare origin; hook rehearsal 7 (accepts the deletes, rejects an add). The data `.gitattributes` says `fpl.sqlite binary`, not the plan's literal `*.sqlite binary` |
| 6 secret hygiene: fail on key value / apiKey= in staged files; never log full URLs; write permission on the pushing job only; triggers schedule + dispatch; gitleaks (A1.6) | **FAIL (F1)** on the staged-file scan; rest PASS; the gitleaks run is out of scope | the scan cannot see inside `.json.gz` (F1). URL logging: M19. `permissions: {}` at the top, one `contents: write`, triggers pinned |
| 7 verifier → report → commit → push | out of scope | this is the pre-check |

## Acceptance tests: RULING S1 points 1–8

| # | verdict | evidence |
|---|---|---|
| 1 9d source | PASS | CLAUDE.md 9d reads "(events.deadline_time in fpl.sqlite)" (`53383fd`) |
| 2 "One item at a time" in CLAUDE.md and BUILD_PLAN.md | PASS | Both carry the exact sentence. "One step per session" no longer appears in either |
| 3 ruling-only prereg rule in prereg/README.md | PASS | The two sentences are verbatim |
| 4 migration integrity, side by side, byte-identical first data commit | PASS (tool and rehearsal); **re-check after migration** | rehearsal 4–6 |
| 5 the dispatch must not duplicate forecasts | PASS | rehearsal 11; `record_status` drops the rows for (source, target) before appending |
| 6 rollback tag pushed; report says how to revert | out of scope; note F6 | |
| 7 raw URL pattern; one fetches over HTTPS without sign-in | pattern documented in CLAUDE.md; **re-check after migration** | today `…/master/reports/watch_2026-10-16.txt` gives HTTP 200 (6,320 bytes). `…/data/…` gives 404, as expected before the migration |
| 8 push before 23:00; nothing half-migrated pushed | PASS for tonight | `git ls-remote https://github.com/borisdanihel-dev/FPL.git` shows only `master` = `a2bd8ef` (no `data`, no scratch branch, no tag). `5ad7f4c..a2bd8ef` touches only docs, prereg and worklog |

## Acceptance tests: Amendment 1

| # | verdict | evidence |
|---|---|---|
| 1 value check where `ODDS_API_KEY` is set; pattern check always; no key to the runner before Step 5 | **FAIL (F1)** | Both checks are blind to gzipped content. nightly.yml has no `secrets.` (test-pinned) |
| 2 gate: missing table, integrity, shrinking grow-only tables (price_history, **projection log tables**); EXPECTED_TABLES in fpl_gate.py; schema change updates it; no override | **FAIL (F3)** for the projection-log part; rest PASS | `GROW_ONLY = ("price_history",)`. The projection log is not gated at all. EXPECTED_TABLES equals fpl_sync's 13 `CREATE TABLE`s (test, M24). No override flag exists |
| 3 `fpl.sql`; every `prices.sql` in BUILD_PLAN.md, CLAUDE.md, workflow updated | PASS | `prices.sql` remains only in CHANGELOG history, the prereg ruling text and the earlier worklog report |
| 4 hook allows deletions on master, rejects adds and changes | PASS | M8; rehearsal 7 |
| 5 `FPL_DATA_DIR` read by fpl_nightly.py only; local command pattern documented | documented; **the pattern does not work (F2)** | Among the scripts, only `fpl_nightly.py` reads it. `test_fpl.py` reads it too, as accepted in decision 5 |
| 6 secret-scan.yml, official action pinned to a full SHA; push to master and data + dispatch; README read; licence | PASS as built; **the run is out of scope** | `e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e` = upstream tags `v3` and `v3.0.0` (`ls-remote`). At that SHA the README says "If you are scanning repos that belong to a personal account, then no license key is required", and `src/index.js` skips the licence for user type "User". `api.github.com/users/borisdanihel-dev` gives type "User" |
| 7 tonight: amendment committed (docs only, may be pushed); items 1–6 built locally; rehearsal; pre-check; no runner change on GitHub | PASS | `a2bd8ef` is pushed (docs only). The branch is local only (ls-remote above) |
| accepted as found: sync logs the API path only | PASS | `fpl_sync.get` prints `path` on retry and on failure (M19). `FAILED` still holds URLs but is only counted, never printed |

## Findings

**F1 (FAIL): the staged-secret scan cannot see inside gzipped files, and every new export is now `.json.gz`.**
- **How tested:** in a scratch repository I staged `exports/fpl_export_gw9_2026-10-18.json.gz` containing `…odds?apiKey=ZZZ123dummyvalue`.
- **Result:**
  - `fpl_gate.py --secrets` printed `SECRETS OK`, exit 0;
  - with `ODDS_API_KEY=ZZZ123dummyvalue` set, still `SECRETS OK`, exit 0;
  - the same text in a plain `.json` gave `SECRET FAIL`.
- **Cause:** `staged_secrets` matches the raw (compressed) bytes.
- **Exposure:** none until Step 5 puts a key on the runner. But the one committed copy of each export is unscanned. The repository is public (the raw URL works without sign-in), and gitleaks does not decompress archives by default.
- **Fix:** decompress `*.gz` before matching, plus a test.

**F2 (FAIL): the local command pattern documented in CLAUDE.md (A1.5) does not work on the data worktree.**
- **Default export:** in a fresh checkout of `data` (as `git worktree add C:\GIT\FPL-data data` gives), `python …\fpl_edge.py --section calibration` exits with "No fpl_export_gw*.json found here". Working exports are ignored on `data` and only `fpl_nightly.py` restores them, which CLAUDE.md forbids running locally. `--diff` fails the same way.
- **Explicit export:**
  - `fpl_edge.py exports/fpl_export_gw7_2026-10-17.json.gz` fails with `UnicodeDecodeError` (byte 0x8b): `fpl_edge.py` cannot read `.json.gz`.
  - Frozen `p1_eval.py` takes plain export paths, so the lockdown routine (`--section calibration`, then `p1_eval.py`) has no working input from the first post-migration night.
- **Tests:** the claim "with `$env:FPL_DATA_DIR = "C:\GIT\FPL-data"` it also checks the real export" is false on a fresh worktree. That run gives `OK (skipped=2)`: both real-export tests skip.
- **Needs** a fix or a ruling. Options:
  - commit the working export;
  - keep plain dated copies;
  - add a gz-aware loader — a change to `fpl_edge.py`, the record path.

**F3 (FAIL pending a ruling): A1.2 names "projection log tables" as grow-only, and the projection log is not gated at all.**
- **The implementer's reasoning (code comment only):** `fpl.sqlite` has no projection-log table, and `projection_log.csv` may legitimately shrink, because `--record` replaces each (source, gameweek) block.
- **The fact is right:** `record_status` drops the block and appends the new rows, so a re-record with fewer eligible players lowers the count.
- **But the ruling was re-read silently:**
  - there is no entry in CHANGELOG, the worklog or a question to Boris;
  - a commit that empties or truncates `projection_log.csv` (frozen, past-deadline forecasts) passes the gate today;
  - CLAUDE.md 9e asks to stop and ask in this case.
- **One gateable reading:** rows for gameweeks whose deadline has passed must be present and unchanged.

**Observations (none decides the verdict; listed for tomorrow):**
- **F4.** gitleaks' `generic-api-key` rule may flag the fixture `key = "f00dfacecafe1234567890abcdef0000"`. Its Shannon entropy is 3.63, above the rule's 3.5. The first push-triggered secret-scan run could then go red. gitleaks was not run, per A1.6.
- **F5.** If the code reaches master as a **merge** over the overnight nightly, the pre-push hook rejects the push (rehearsal 12). Use the planned single byte-identical commit.
- **F6.** Rollback wording in `worklog/cc_2026-10-17_S1.md`: the tag is placed after the code commit (plan step 4). But "revert the migration commit and the code commit … restores the old workflow … exactly as tagged at pre-data-branch" holds only if the tag is on the master commit **before** the code commit. Tag that commit, or fix the wording.
- **F7.** `.gitattributes` uses `fpl.sqlite binary`, not the plan's literal `*.sqlite binary`. It is equivalent today (one database).
- **F8.** A secret hit refuses the whole night, including that night's price rows. Fixture strings appear in test failure output: the subTest header printed `(body='export API_KEY=abc\n')` under M3. So if `DataGate`'s secret tests ever fail on the runner, the run log trips the scan, and that night's prices are not committed.
- **F9.** CLAUDE.md 9d lists the runner path as ".github/workflows, fpl_nightly.py, fpl_sync.py, the record step". `fpl_publish.py` and `fpl_gate.py` now run nightly too.
- **F10.** A Sunday dispatch creates `backup-<date>`, so that evening's scheduled run skips the backup ("exists"). That week's backup is the dispatch-time database.
- **F11.** All `picks` rows deleted passes the gate (rehearsal 10). This is consistent with A1.2's list, but only `price_history` is protected.

## Re-check after the migration

1. `measure` on master just before the migration and on `C:\GIT\FPL-data` after it, with `compare` exit 0 shown side by side. Confirm the first `data` commit is parentless and has the same blob ids as master.
2. Tag `pre-data-branch` on GitHub at the intended commit (F6), and the revert instructions in the report.
3. The migration commit is deletions only, the push went through the installed hook, and GitHub `master` holds no data path afterwards.
4. Proof dispatch:
   - green;
   - exactly one new commit on `data`, holding `fpl.sql`;
   - GitHub `master` unchanged;
   - no duplicate (source, event, player_id) rows in `projection_log.csv`.
5. Release `backup-2026-10-18` with 2 assets (`fpl.sqlite`, `fpl.sql`).
6. `https://raw.githubusercontent.com/borisdanihel-dev/FPL/data/reports/watch_<date>.txt` returns HTTP 200 without sign-in.
7. The secret-scan workflow runs on the master push and on a manual full-history dispatch. Its findings, without values; watch for F4.
8. F1, F2 and F3 are fixed or ruled on, with their tests red then green, before the migration is pushed.

VERDICT: FAIL (pre-check scope)

Most of S1 checks out: the prereg and Amendment 1 were committed before their code, and the suite went from 253 to 288 tests, green in both CRLF and LF checkouts. All 28 one-line mutations turned red and went green again when restored, the frozen-time forecasts are byte-identical, and nothing reached GitHub. My own migration rehearsal built an orphan `data` commit with all 103 data files byte-identical, and the nightly and publish run committed only to `data` and left `master` unchanged. Three things fail. (F1) The staged-secret scan of Step 1.6 and Amendment 1 point 1 cannot see inside the `.json.gz` exports this item introduces: a gz holding `apiKey=` or the key value passes. (F2) The local command pattern in CLAUDE.md (A1.5) fails on a data worktree, because it has no working export and `fpl_edge.py` and the frozen `p1_eval.py` cannot read `.json.gz`. (F3) The projection log, named in Amendment 1 point 2 as grow-only, is not gated at all, and that reading of the ruling was never put to Boris. Each needs a fix or a ruling, and the re-checks listed above, before the migration is pushed.
