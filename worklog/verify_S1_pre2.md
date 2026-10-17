# Verifier report: S1, second pre-check (before the migration)

- **Verifier:** backtest-verifier (native). I read `.claude/agents/backtest-verifier.md` from disk first, and it governed this run.
- **Scope:** everything that can be verified before the migration. That covers every point of Amendment 2 and every finding of the first pre-check (`worklog/verify_S1_pre.md`, left unchanged).
  - **Out of scope, not counted as failures:** the real tag, the `data` branch and the migration commit on GitHub, the proof dispatch, the backup release, the `data` raw URL, and the secret-scan workflow runs. They are listed under "Re-check after the migration".
- **Base / head:**
  - Base is master `e100932` (pushed).
  - Head is `scratch/s1-wip` = `ba8cd36`, local only.
  - The Amendment 2 work is `0e391cc` and `ba8cd36`, made after the merge of `e100932` (`4029cb0`).
- **Rulings checked:** the verbatim `RULING S1:` block, `Amendment 1` and `Amendment 2` in `prereg/S1.md`. I read no session transcript or chat log. I read the worklog and SESSION_STATE only to learn the implementer's migration plan.
- **Scratch:** all work ran in `C:\Users\Boris\AppData\Local\Temp\s1_pre2_verify_24463\`, which was deleted afterwards.
  - The rehearsal's origin was a bare repository I created in that folder.
  - Every clone's origin was repointed before any fetch or push.
  - Nothing was pushed to GitHub or to `C:\GIT\FPL`.
- **`C:\GIT\FPL` before and after:** checked unchanged.
  - refs: master `e100932`, `scratch/s1-wip` `ba8cd36`, origin/master `e100932`;
  - `.git/config` sha256 `f8ba8a87…` both times;
  - no hook installed, one worktree, no stash, clean status.
  - The only new file is this report.
- **Network, all read-only:**
  - the public FPL API, through the two rehearsal nightlies;
  - `git ls-remote` of borisdanihel-dev/FPL and gitleaks/gitleaks-action.

## Prereg order (gate)

PASS.
- **The original ruling.** `3318b08` (20:58:24) precedes the first code commit `bb8c9b2` (21:09:17). This was checked in the first pre-check and is unchanged.
- **Amendment 1.** `a2bd8ef` (21:37:36) precedes `c93b327`.
- **Amendment 2** is `12fa064`, dated 22:57:48 (author and committer dates equal).
  - It holds only `prereg/S1.md`, +16 lines appended, with 0 lines of the earlier text removed.
  - No branch commit lies between `84a1bb0` (21:49:06) and the merge `4029cb0` (22:58:22), which brought `12fa064` and `e100932` into the branch.
  - The Amendment 2 code commits `0e391cc` (23:04:31) and `ba8cd36` (23:10:12) both descend from `12fa064`.
  - The `scratch/s1-wip` reflog shows the branch moved `84a1bb0` → `ba8cd36` at 23:10:13, after the amendment.
- `git diff e100932 ba8cd36 -- prereg/` is empty.

## Check 1: point-in-time leak check

PASS (not applicable; nothing is produced).
- The item produces no forecast, feature or evaluation metric.
- `fpl_edge.py`, `p1_eval.py`, `fpl_ship.py` and `fpl_hist.py` are unchanged (`git diff --quiet e100932 ba8cd36`).
- So 1a and 1b have no input to rebuild, and 1c has no correlation to probe. Check 5 shows the forecasts are unchanged.

## Check 2: clean-checkout test run

PASS. Each run used a fresh clone and `python test_fpl.py` (Python 3.14.7).

| checkout | tests | result |
|---|---|---|
| `e100932` master (before) | 253 | OK (skipped=2) |
| `ba8cd36` (after), CRLF checkout | 304 | OK (skipped=2) |
| `ba8cd36`, LF checkout (`core.autocrlf=false`, `core.eol=lf`, as on the runner) | 304 | OK (skipped=2) |
| rehearsal code commit on master (CRLF) | 304 | OK (skipped=2) |
| inside the rehearsal nightly (new layout) | 304 | OK |
| `FPL_DATA_DIR` = rehearsal data worktree, after `--restore` | 304 | **OK, 0 skips** (the first pre-check saw 2 skips here: F2) |

- **Added: 53 tests.** `DataGate` 26, `NightlyRunner` 7, `NightlyWorkflow` 7, `PrePush` 6, `Publish` 6, `SyncNetwork` 1.
- **Removed: 2 tests,** the old-layout ones: `test_ignore_and_attribute_rules_fit_two_writers` and `test_outputs_are_committed_back_even_from_a_red_run`.
- 253 + 53 − 2 = 304.

## Check 3 and check 4

- **Check 3:** not applicable. The prereg has no evaluation, metric, bootstrap or threshold.
- **Check 4:** PASS.
  - Every prereg row is n/a, and nothing was promoted or re-tuned.
  - All three rulings are present verbatim in `prereg/S1.md`, appended only.
  - Ruling fidelity is judged per point below.

## Check 5: recording path

PASS.
- **Frozen-time regeneration.** Time was frozen at 2026-10-17T21:00:00Z by a scratch `sitecustomize.py` that replaces `datetime.datetime.now`. This is before the GW8 deadline of 2026-10-23T17:30Z.
- **Same input, two layouts.** All four sources were recorded from the same export (`fpl_export_gw7.json` of the simulated overnight nightly) and the same starting log and database:
  - (A) base code `e100932`, code and data in one folder;
  - (B) head code run from the code folder, with the data folder as the working directory, exactly as `fpl_nightly.py` now calls it.
- Both gave 275 / 260 / 260 / 260 rows for GW8.
- Both logs have 4680 lines and sha256 `8c045aab…`. `cmp` finds them **byte-identical**, with 1055 rows carrying the frozen stamp. This is the same hash as the first pre-check.
- **Cross-check with a real nightly.** The head nightly in the new layout (rehearsal step 8) recorded the same 1055 GW8 keys, with a maximum difference in `predicted` of 0.0. All 3624 non-GW8 rows were identical, including `made_at`.

## Check 6: mutation spot-check

PASS. I made 22 one-line mutations in a scratch clone at `ba8cd36` (LF checkout), each targeting the Amendment 2 logic.
- 20 went red.
- Each file was restored and its sha256 verified identical.
- Two survived; both are test gaps, not code defects.

| # | file | mutation | red test |
|---|---|---|---|
| MA1 | fpl_gate | .gz not decompressed | `test_a_key_inside_a_gzipped_export_fails_the_commit`, `test_a_gz_that_cannot_be_read_fails_the_commit` |
| MA2 | fpl_gate | unreadable .gz is not a hit | `test_a_gz_that_cannot_be_read_fails_the_commit` |
| MA19 | fpl_gate | `.gz` suffix matched case-sensitively as `.GZ` | both gz tests |
| MA3 | fpl_gate | `GROW_ONLY = ("price_history",)` | `test_emptying_any_grow_only_table_is_rejected`, `test_grow_only_holds_exactly_…` |
| MA4 | fpl_gate | deadline comparison inverted | 3 log tests |
| MA5 | fpl_gate | log compared by row count only | `test_a_changed_frozen_forecast_is_rejected` |
| MA6 | fpl_gate | log check skipped | 3 log tests |
| MA7 | fpl_gate | gameweek without a deadline passes | `test_a_logged_gameweek_without_a_deadline_is_rejected` |
| MA8 | fpl_gate | no `::error` annotation | `test_a_secret_hit_fails_loudly_on_the_runner` |
| MA16 | fpl_gate | the api_key pattern dropped | `test_every_key_pattern_in_any_case_fails_the_commit` +1 |
| MA17 | fpl_gate | key value printed in the FAIL line | `test_the_key_value_fails_the_commit_and_is_never_printed` +1 |
| MA9 | fpl_nightly | `--restore` without refresh | `test_restore_replaces_a_stale_working_export_and_then_does_nothing` |
| MA18 | fpl_nightly | refresh always rewrites | same |
| MA10 | fpl_nightly | code-folder refusal removed | `test_restore_refuses_the_code_folder_and_a_folder_without_exports` |
| MA11 | fpl_nightly | `--restore` uses the code folder | `test_restore_takes_fpl_data_dir_else_the_current_folder` |
| MA21 | fpl_publish | gate exit 1 ignored | `test_a_failed_gate_commits_and_pushes_nothing` |
| MA12 | nightly.yml | `force_backup` default true | `test_a_dispatch_can_force_the_backup` |
| MA13 | nightly.yml | `FORCE_BACKUP` condition removed | `test_weekly_backup_on_sundays_keeps_the_last_eight` |
| MA22 | nightly.yml | `FORCE_BACKUP` hard-wired to true | same |
| MA14 | secret-scan.yml | checkout ref ignores the `branch` input | `test_secret_scan_runs_the_pinned_gitleaks_action` |
| MA15 | tools/migrate_data_branch.py | `*.sqlite binary` → `fpl.sqlite binary` | **survived**: the tool has no unit tests (O3) |
| MA20 | fpl_gate | `check_log` loops over the last commit's gameweeks only | **survived** (O4) |

- **MA20.** The real code is correct: on real data, a new GW3 block absent from the last commit gave "GW3 is past its deadline and its rows changed (0 missing or changed, 1 added)", exit 1. No test pins it.
- **F8, failure output.** I scanned the failing-test output of all 22 mutations:
  - 0 lines with a key pattern;
  - one 24+ hex string, which is the pinned action SHA echoed in MA14's assertion message, not a key.

## Check 7: secrets

PASS for the code to land, with a literal-match note on two S1 worklog files that are already on master.
- **The 12 files the code commit adds or changes** (`git diff --name-only e100932 ba8cd36`) hold:
  - no key value;
  - no URL carrying a key;
  - no Authorization header value;
  - no 24+ hex literal apart from the gitleaks-action SHA in `secret-scan.yml`.
- **Every key-pattern hit is rule text without a value:**
  - the `KEY_PATTERNS` constant and the docstring in `fpl_gate.py`;
  - a comment in `nightly.yml`;
  - prose in `BUILD_PLAN.md`.
- `test_fpl.py` now builds every fake key at runtime: `secrets.token_hex`, word pieces joined at runtime, and subtests labelled by index.
- **Test output is clean.** The full green runs (CRLF and LF) have 0 key-pattern lines and 0 hex strings of 32+ characters.
- **An approximate gitleaks `generic-api-key` check** (its regex with the 3.5 entropy floor; gitleaks itself was not run, per A1.6) flags:
  - `test_fpl.py:4898`. The "value" is an environment-variable name (letters and underscores, no digits) next to `ODDS_API_KEY`, entropy 3.52. Real gitleaks may drop it through its allowlist, but this is unverified (O9).
  - `worklog/verify_S1_pre.md:281`. This is the first pre-check's quoted 32-hex dummy key in an assignment form, entropy 3.63 (O8).
- **Literal-match note (O8):**
  - `worklog/verify_S1_pre.md` (added by S1 commit `ea7acaa`, already on GitHub) quotes the old test fixtures. These are dummy key-name/value pairs, a fixture URL with a dummy query key, and the 32-hex dummy. `worklog/SESSION_STATE.md` quotes one of the same pairs.
  - These are not secrets.
  - They do mean A2.4's aim ("no key-like literal is in any file") holds for the code, the tests and the test output, but not for those two worklog files.
  - History cannot be cleaned without a rewrite, which 9e forbids.

## Rehearsal (throwaway clones, my own bare origin)

The order follows Amendment 2 point 6 and its "Order tonight" paragraph.

1. **Origin.** A bare `origin.git` received `master` = `e100932` only.
2. **Simulated "nightly 2026-10-17".** A runner clone (LF settings) ran the **old** `fpl_nightly.py` against the live API.
   - Exit 0 in 30 s.
   - 253 tests OK.
   - RECORD OK own 275 / xg 260 / minutes 260 / bottomup 260 for GW8.
   - `ARCHIVE OK … fpl_export_gw7_2026-10-17.json`.
   - It was committed exactly as the old workflow's step does (`git add projection_log.csv fpl.sqlite exports logs reports`, message `nightly <date> [skip ci]`) and pushed to origin `master`: `080a724`.
3. **Local clone like `C:\GIT\FPL`.** A clone of `C:\GIT\FPL` with master `e100932` and a local `scratch/s1-wip` at `ba8cd36`.
   - Its origin was repointed to the bare repository.
   - `git fetch --prune` showed `e100932..080a724 master` with subject "nightly 2026-10-17 [skip ci]", which is the ruling's precondition.
4. **Pull, tag, code commit.**
   - `git pull --ff-only` brought master to `080a724`.
   - Tag `pre-data-branch` went on `080a724`, the pulled master, **before** the code commit (A2.6, F6).
   - `git checkout scratch/s1-wip -- <the 12 files>` then one commit gave `d20da7b`, with a single parent `080a724`. No merge commit exists in `pre-data-branch..HEAD`.
   - All 12 blobs equal `ba8cd36`'s.
   - `git diff ba8cd36 d20da7b` touches only the 6 data files of the overnight nightly; outside data paths it is empty.
   - Tests: 304 OK.
5. **Measure, build, byte check.**
   - `measure` at `d20da7b`.
   - `build` gave `66d4adb`: **no parent**, 103 data files + `.gitignore` + `.gitattributes`, "blobs identical: True".
   - The data `.gitattributes` says `*.sqlite binary` (A2.6, F7).
   - **Independent byte check:** the 103 (path, blob) pairs of `data` equal master's at `d20da7b` (`diff` empty).
6. **Push, worktree, compare.** Tag and `data` pushed to the bare origin, then `git worktree add FPL-data data`, `measure`, `compare`: exit 0. Before and after, side by side (ruling point 4):

   | | before (master `d20da7b`) | after (data worktree) |
   |---|---|---|
   | chips / entries / entry_gw / events | 12 / 7 / 49 / 38 | 12 / 7 / 49 / 38 |
   | fixtures / picks / player_gw / player_history | 380 / 735 / 4550 / 1927 | identical |
   | players / price_history / standings / teams / transfers | 667 / 25214 / 42 / 20 / 67 | identical |
   | projection_log.csv data rows | 4679 | 4679 |
   | integrity_check | ok | ok |
   | files: same blob / same sha256 stored / same sha256 on disk | 103 | 103 / 103 / 103 |

   - My own row-count script agreed.
   - My own `sha256sum` over all 103 checked-out files matched; fpl.sqlite `c0c4a757…` and projection_log.csv `ff668d39…` on both sides.
7. **Migration commit and hook.**
   - Migration commit `7fda075`: 103 deletions, nothing else.
   - `python fpl_prepush.py --install` wrote a hook that calls the script by its full path.
   - `git push origin master` (code + migration together) was accepted.
   - Origin `master` then holds 0 data paths.
   - A follow-up commit force-adding `reports/watch_2099-01-01.txt` was **rejected** ("PRE-PUSH REJECTED … data belongs on the data branch"). Origin stayed at `7fda075`.
8. **New-layout nightly and publish (A2: "the nightly and publish in the new layout").**
   - A runner clone of origin `master` (LF), with `data` cloned into `./data`, ran `FPL_DATA_DIR=data python fpl_nightly.py` against the live API.
     - Exit 0 in 50 s.
     - "data dir: …\data"; 5 exports restored; 304 tests OK.
     - RECORD OK 275 / 260 / 260 / 260; `ARCHIVE OK … fpl_export_gw7_2026-10-17.json.gz`.
     - The code folder had no new file apart from the ignored `data/`.
   - `python fpl_publish.py data` printed: `GATE OK … 13 tables, price_history 25214 rows, frozen forecasts unchanged; fpl.sql written`, `SECRETS OK`, `PUSH OK origin data`. Exit 0.
   - **Result:** one new `data` commit `bc769b2` with parent `66d4adb`.
     - It adds `fpl.sql` and the `.json.gz`, and modifies `fpl.sqlite`, the log, `projection_log.csv` and the watch file.
     - **Origin `master` was unchanged** (`7fda075`).
   - `fpl.sql` is 2,148,763 bytes with 0 CR. A database rebuilt from it has every row equal in all 13 tables.
   - The `.json.gz` has gzip flags 0 and mtime 0, and decompresses to the working export byte for byte.
   - Rerunning the gate on a clean clone rewrote `fpl.sql` byte-identically (no git change).
9. **Ruling point 5 (no duplicate forecasts).**
   - The same-day re-record left 4679 rows with 0 duplicate (source, event, player_id) keys.
   - GW8 has 1055 rows before and after, equal apart from `made_at`.
   - The 3624 other rows are identical.
10. **`--restore` on the data worktree (A2.2, F2).**
    - On the fresh worktree, `fpl_edge.py --section calibration` first failed ("No fpl_export_gw*.json found here").
    - `python <code>\fpl_nightly.py --restore` wrote the 5 working exports and nothing else:
      - HEAD was unchanged;
      - `git status` was clean (the exports are ignored);
      - a second run wrote 0.
    - Then from the worktree:
      - `fpl_edge.py --section calibration`: exit 0;
      - `fpl_edge.py --diff`: exit 0, diffing GW7 against GW6;
      - the frozen `p1_eval.py fpl_export_gw3.json fpl_export_gw5.json`: exit 0, 255 players graded, no file written;
      - the suite with `FPL_DATA_DIR` set: 304 OK with 0 skips.
11. **Gate on real data (A2.3, F3, F11).**
    - **Database:** deleting one row from **each** of the 13 tables failed the gate, for example "picks rows fell from 735 to 734".
    - **Frozen forecasts:**

      | change | result |
      |---|---|
      | one GW4 value changed | FAIL "(1 missing or changed, 1 added)" |
      | all GW5 rows deleted | FAIL "(1046 missing or changed, 0 added)" |
      | log reduced to its header | FAIL |
      | a GW7 row added after its deadline | FAIL |
      | a new GW3 block | FAIL |
      | log deleted | FAIL "projection_log.csv is missing" |
      | a GW8 value changed (deadline open) | passes, as ruled |
      | half of GW8 dropped (deadline open) | passes, as ruled |
      | rows reordered | passes |

12. **Secret scan through publish on real data (A2.1, F1).**
    - **Pattern case:** a staged `exports/fpl_export_gw9_2026-10-18.json.gz` holding the real export plus a URL with the camel-case key pattern and a random value.
    - **Value case:** the same file holding a random 32-hex value, with `ODDS_API_KEY` set to that value.
    - Each gave `SECRET FAIL  exports/fpl_export_gw9_2026-10-18.json.gz`, then "NOTHING COMMITTED TONIGHT".
    - In both cases: publish exit 1, 0 files left staged, HEAD and origin `data` unchanged at `bc769b2`, and the value never printed.
    - The first pre-check had `SECRETS OK` for the same case.
13. **Rollback.**
    - `git revert` of the migration and code commits gives a tree identical to `pre-data-branch` (`git diff` empty).
    - **But the push is refused:** the installed hook execs `…\FPL\fpl_prepush.py`, which the revert removed ("can't open file"). Even before that, the migration revert re-adds data paths, which the hook rejects.
    - `git push --no-verify` landed, and origin `master` equalled the tag's tree (F-B).

## Acceptance tests: Amendment 2

| # | verdict | evidence |
|---|---|---|
| 1 F1: secret scan decompresses .gz | PASS | `staged_secrets` reads each `.gz` decompressed as well as raw; an unreadable `.gz` counts as a hit. Tests MA1/MA2/MA19; rehearsal 12 |
| 2 F2: `fpl_nightly.py --restore` reuses the restore step, writes only the untracked working exports, commits nothing; CLAUDE.md local commands start with it; no gzip loader in fpl_edge.py; p1_eval.py frozen | PASS (note F-A) | `restore_only` calls `restore_exports(…, refresh=True)`, refuses the code folder, and needs dated exports. CLAUDE.md block: `cd`, `git pull`, `--restore`, calibration, diff. fpl_edge.py and p1_eval.py are unchanged. Rehearsal 10. The documented `git pull` fails on the worktree as the migration plan creates it (F-A) |
| 3 F3: gate fails on missing or changed rows of past-deadline gameweeks vs the data branch's previous commit; a table is grow-only only if fpl_sync.py never deletes from it, each listed with code evidence | PASS; the per-table listing is due in the implementer's report | `check_log` compares whole rows per gameweek with `git show HEAD:projection_log.csv`, using deadlines from `events.deadline_time`. The table evidence is below. Rehearsal 11 |
| 4 F4/F8: fake keys built at runtime, no key-like literal in any file or test output; a secret block fails loudly; losing the night is accepted | PASS for tests and test output; **note O8** for two worklog files | Check 7; mutation outputs. A hit prints the `::error` annotation on the runner (MA8) and exits 1, and the publish step has no `continue-on-error` |
| 5 F9: 9d runner path = "anything the nightly workflow runs or imports" | PASS | CLAUDE.md line 67 (`e100932`); no other copy of the old list remains |
| 6 one byte-identical commit, never a merge; tag on the pulled master before it; `*.sqlite binary` | PASS in rehearsal; the real run is out of scope | rehearsal 3–5 |
| 7 9d timing: never between 21:00 UTC and the end of that night's run, never within 30 h of a deadline; CLAUDE.md updated | PASS | CLAUDE.md line 67. GW8 deadline 2026-10-23T17:30Z, so the window opens 2026-10-22T11:30Z |
| 8 `force_backup` input (boolean, default false) runs the backup regardless of weekday | PASS | nightly.yml lines 18–23 and 80–82; tests MA12/MA13/MA22. See the backup-step simulation below |
| 9 every other pre-check finding fixed as recommended, each listed in the report | PASS for the code; **the listing is due in the implementer's report** | see "First pre-check findings" |
| Order: amendment commit → fixes → this pre-check; no migration before "nightly 2026-10-17" is on origin/master | PASS so far | `12fa064` → `0e391cc`, `ba8cd36` → this pre-check. At 21:31 UTC, `git ls-remote` of GitHub shows only `master` = `e100932`: no `data`, no tag, no scratch branch, and tonight's nightly not yet run |

**Backup-step simulation (A2.8).** The step's shell text, extracted from nightly.yml, was run with stub `gh` and `date` on PATH:

| run | result |
|---|---|
| scheduled Saturday (empty input) | "BACKUP skipped: not Sunday", 0 `gh` calls |
| dispatch Saturday, unticked | skipped |
| dispatch Saturday, **ticked** | `release create backup-2026-10-17`, then the 2 oldest of 10 listed backups deleted |
| scheduled Sunday | created |
| dispatch Sunday, unticked | created |

**Grow-only tables: code evidence (A2.3).**
- **No deletes.** `fpl_sync.py` at `ba8cd36` has no DELETE, DROP, TRUNCATE or VACUUM. Its only DDL besides `CREATE TABLE IF NOT EXISTS` is `ALTER TABLE … ADD COLUMN` in `migrate()`.
- **Constraints.** No `CREATE TABLE` body holds UNIQUE. The real `fpl.sqlite` has 8 automatic indexes (the composite primary keys) and no others.
- **Writes.** Every write is `INSERT OR REPLACE`, which on a primary-key-only table replaces at most the one row it collides with. So no table's count can fall. The writes:
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
- **No other writer.** Nothing else in the nightly writes `fpl.sqlite`: `fpl_edge.py` never connects to it, and the gate opens it read-only.
- **The implementer's reading.** The ruling says "never deletes"; an `INSERT OR REPLACE` deletes the colliding row before inserting. The implementer read the rule as "the count can never fall". That reading fits the purpose of a grow-only list, and it is stated in a `fpl_gate.py` comment. The report should state it too.

## First pre-check findings

| finding | status | evidence |
|---|---|---|
| F1 gz unscanned | **fixed** | A2.1 above |
| F2 local pattern fails on the worktree | **fixed**; new caveat F-A | rehearsal 10 |
| F3 projection log not gated | **fixed** as ruled | rehearsal 11 |
| F4 32-hex fixture in tests | **fixed** in tests; residual copy in `worklog/verify_S1_pre.md` (O8) | check 7 |
| F5 merge rejected by the hook | **avoided**: single commit, no merge | rehearsal 4 |
| F6 tag position and rollback wording | **fixed**: tag on the pulled master before the code commit; the revert restores the tag's tree. New caveat F-B | rehearsal 4, 13 |
| F7 `*.sqlite binary` | **fixed** in the tool (not test-pinned, O3) | rehearsal 5 |
| F8 fixture strings in failure output; night lost on a hit | **fixed**; the night loss is accepted by A2.4 | check 6 |
| F9 9d runner-path list | **fixed** | CLAUDE.md line 67 |
| F10 a Sunday dispatch makes the scheduled run skip the backup | **documented** in the nightly.yml comment; the first pre-check recommended no change | nightly.yml lines 72–75 |
| F11 deleting picks passes | **fixed**: all 13 tables grow-only | rehearsal 11 |

## Findings

**F-A: the documented `git pull` in `C:\GIT\FPL-data` fails after the planned migration steps.** Not counted as a failure: it arises in the out-of-scope `data`-branch creation, and it is a must-fix for that step.
- **Cause:**
  - `tools/migrate_data_branch.py build` creates a local `data` branch;
  - the plan pushes it with a plain push (`cc_2026-10-17_S1.md`, plan step 5);
  - `git worktree add C:\GIT\FPL-data data` then checks out a branch with no upstream.
- **What I saw:** in the rehearsal worktree, `git pull` printed "There is no tracking information for the current branch" and pulled nothing.
- **Risk:** this is the second command of the CLAUDE.md block. The `--restore` and calibration commands that follow it would run on stale data.
- **Fix:** push with `git push -u origin data`, or run `git branch --set-upstream-to=origin/data data` after the push.
  - With the upstream set, `git pull` brought `bc769b2` into the worktree.
  - Re-check after the migration: `git -C C:\GIT\FPL rev-parse --abbrev-ref data@{upstream}` gives `origin/data`.

**F-B: the drafted rollback ("revert the migration commit and the code commit … and push") is refused by the installed pre-push hook.** Not counted as a failure: the revert instructions belong to the out-of-scope final report (ruling point 6).
- **Cause:** the revert removes `fpl_prepush.py`, which the hook execs by full path. Even before that, the migration revert re-adds data paths, which the hook rejects.
- **Fix:** the report's revert text must add one step: push with `--no-verify`, or delete `.git\hooks\pre-push` first. Rehearsal 13 shows that this lands and restores the tag's tree.

**Observations (none decides the verdict):**
- **O1. Nothing scans `data` automatically.** `secret-scan.yml` lists `data` under `push`, as A1.6 rules, but a push to `data` cannot start it:
  - the `data` branch holds no workflow file;
  - the nightly pushes with the workflow token, which starts no workflow.
  - So `data` is gitleaks-scanned only by a manual dispatch with `branch: data`. Every data commit is still scanned before it is made by `fpl_gate.py --secrets`.
  - The implementer documented this in the workflow comment, but it changes how A1.6 works in practice, so it should be put to Boris in the report.
  - CLAUDE.md's "runs the gitleaks action on every push to `master` or `data`" is inaccurate for `data`.
- **O2. Same-date tie in `restore_exports`.** When a plain `fpl_export_gwN_<date>.json` and a `….json.gz` share a date, the first glob match wins:
  - NTFS lists names alphabetically, so the plain file wins there;
  - on Linux the order is arbitrary.
  - In rehearsal 10, after the pull, the working GW7 export stayed the older plain copy while `--restore` reported "already current".
  - This only happens when an old-layout and a new-layout run archive the same gameweek on the same UTC date. A proof dispatch on Sun 18 Oct, after a Sat 17 Oct old nightly, does not trigger it.
  - Prefer `.gz` on equal dates if this matters.
- **O3. The migration tool has no unit tests** (MA15 survived). Its `.gitattributes` content was verified only by this rehearsal. Re-check `git show data:.gitattributes` after the migration.
- **O4. MA20 survived:** no test covers a past-deadline gameweek that is new in the log. The code handles it (GW3 probe above).
- **O5. A manual dispatch that straddles a deadline** (record before it, gate after it) fails the gate and commits nothing that night. The 21:40 UTC schedule cannot straddle one: this season's latest deadline is 18:30 UTC.
- **O6. Stale docstring.** `fpl_publish.py` still describes the gate as "integrity, price-history rows, table list".
- **O7. Old plan text.** `worklog/cc_2026-10-17_S1.md` (plan step 8) still says `prices.sql`, and its step order tags after the code commit. SESSION_STATE has the corrected order. The final report must use `fpl.sql` and the A2.6 order.
- **O8. Two S1 worklog files on master quote key-like dummy fixtures:** `worklog/verify_S1_pre.md` lines 140–141, 251, 254, 281 and 285, and `worklog/SESSION_STATE.md` line 44.
  - A full-history gitleaks dispatch may flag the 32-hex dummy at line 281.
  - Boris should rule on whether to accept or allowlist it.
  - Future worklog text should describe fixtures instead of quoting them. SESSION_STATE can drop its quote in its next update.
- **O9. A possible gitleaks false positive.** The approximate check flags `test_fpl.py:4898`, a tuple of two environment-variable names. If real gitleaks flags it, the push-triggered scan of the migration push goes red. Watch the first run.

## Re-check after the migration

1. **Before/after counts.** `measure` on master just before the migration, and on `C:\GIT\FPL-data` after it; `compare` exit 0, side by side.
   - The first `data` commit is parentless with the same blob ids as master.
   - `git show data:.gitattributes` holds `*.sqlite binary` (O3).
2. **Tag position.** `pre-data-branch` on GitHub equals the commit that `git fetch` showed as "nightly 2026-10-17" on origin/master, and the code commit's only parent is that commit.
   - The code commit's 12 blobs equal `ba8cd36`'s, and no merge commit exists.
3. **Migration push.**
   - The migration commit is deletions only.
   - The push went through the installed hook.
   - GitHub `master` holds no data path.
   - The push happened outside 21:00 UTC → end of that night's nightly, and before 2026-10-22T11:30Z (A2.7).
4. **F-A:** `data` tracks `origin/data`, and `git -C C:\GIT\FPL-data pull` works. Then `--restore` and `--section calibration` run from the worktree.
5. **Proof dispatch with `force_backup` ticked:**
   - green;
   - exactly one new `data` commit holding `fpl.sql` and that day's `.json.gz`;
   - GitHub `master` unchanged;
   - 0 duplicate (source, event, player_id) rows in `projection_log.csv`;
   - the gate line says "frozen forecasts unchanged".
6. **Backup:** release `backup-2026-10-18` with 2 assets (`fpl.sqlite`, `fpl.sql`).
7. **Raw URL:** `https://raw.githubusercontent.com/borisdanihel-dev/FPL/data/reports/watch_<date>.txt` returns HTTP 200 without sign-in.
8. **Secret scan:** the push-triggered run on the migration push (watch O9), and the manual full-history dispatches on `master` and on `data` (watch O8). Report findings without values.
9. **The report:**
   - the A2.9 list of each finding;
   - the per-table grow-only evidence (A2.3);
   - the revert text, with the hook step (F-B);
   - O1 put to Boris.

VERDICT: PASS (pre-check scope)

The Amendment 2 code is correct and ready to migrate. Amendment 2 was committed before any further S1 code, and the suite grew from 253 to 304 tests, green in CRLF, in LF, and against real data with 0 skips. Forecasts regenerated at a frozen time are byte-identical between the old one-folder layout and the new code/data split. Twenty of 22 one-line mutations of the new logic went red; the two survivors are test gaps whose behaviour I verified directly. Every point of Amendment 2 holds in my own rehearsal against my own bare origin:
- a gzipped export holding a key pattern or the key value is blocked, and nothing is committed;
- `--restore` writes only the ignored working exports, and the documented calibration, diff and frozen `p1_eval.py` then work from the data worktree;
- the gate rejects a one-row deletion in every one of the 13 tables, and any change to past-deadline forecasts, while allowing open gameweeks to be re-recorded;
- the code reaches master as one blob-identical, non-merge commit on top of the simulated "nightly 2026-10-17", with the tag on the pulled master before it;
- the migration keeps all 103 files and every row count identical;
- the new-layout nightly and publish commit only to `data` and leave `master` untouched;
- `force_backup` behaves as ruled.

All first-pre-check findings are fixed or documented. Two procedure defects remain in out-of-scope steps and must be fixed when they are carried out:
- F-A: push `data` with an upstream, or the documented `git pull` in the worktree fails;
- F-B: the rollback push must bypass the hook.

Two items should go to Boris: the dummy key strings that remain in two worklog files already on master (O8), and the fact that the `data` branch is gitleaks-scanned only by manual dispatch (O1).
