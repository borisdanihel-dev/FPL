# verify_S8c_final: the final check of the S8c landing on Boris's real run

**VERDICT: PASS**

Verifier: Fable 5.2 (`claude-fable-5-2`), effort: launched at high, not confirmable.
Run on Mon 16 Nov 2026, 18:18 to 18:36 UTC, straight after the real run.
I read `.claude/agents/backtest-verifier.md` from disk first; it is the same text as my loaded instructions.

The real run 43926712904 ran the code the re-check passed (`4bbb43c`'s runner files, unchanged), went green with 855 tests, and recorded 2,360 GW11 rows that I reproduce exactly on copies of its inputs.
The merge moved no recorded number and no line of the report: pre-S8c code gives the same rows, the same watch file and the same report on the same inputs.

## Decisions for the chat

1. **None blocks the item.** The remaining ruled steps are the main session's: delete `dry/S8c` and `data-dryrun-S8c` (both still on origin, as ruled "after"), then the "S8c done" entry.
2. **Who clicked the run is not provable from GitHub.** The API names the account `borisdanihel-dev` for the dispatch and for every push of the session alike. The state file (pushed 18:11:28 UTC) says "waiting for Boris's real run" and the dispatch came 2 min 55 s later. Boris can confirm it was his click; nothing else depends on it.
3. **Information, not S8c: the Free Hit flag differed between today's two runs.** The 01:23 report printed `GW11 own 30.4 22.2 +8.1 ... FH candidate (gap > 8)`; the 18:16 report prints `28.7 22.2 +6.5` with no flag. Own's 296 recorded values are identical in both runs. The difference is the export CHIPS read (15 Nov at 01:23; the 01:23 export of 16 Nov at 18:16). Pre-S8c code prints the same line on the same inputs. This is W3fix's subject (rulings 2 and 3 of Thu 12 Nov), scheduled Tue 17 Nov.
4. **Information, not S8c: the captain line flipped.** 01:23: Haaland 5.63, Gabriel 5.62. 18:16: Gabriel 5.64, Haaland 5.62. The cause is the new odds snapshot (2,894 prices against 2,482). The section read the 01:23 export with the 18:16 odds, which is the same one-night-behind reading W3fix Ruling 2 fixes.

## The seven claims

| # | Claim | Result |
|---|---|---|
| 1 | The merge, the tag, and the run's head carrying `4bbb43c`'s runner code | PASS |
| 2 | Master gained only `13b07b2` and `dbc6ad0` between the dry run and the merge | PASS |
| 3 | Pushed before 21:00 UTC, outside 30 h of a deadline; dispatch not within 1 h | PASS |
| 4 | The real run: head, times, conclusion, test gate, checks, data commit | PASS |
| 5 | The recorded rows reproduce; six sources equal pre-S8c code row for row | PASS |
| 6 | The suites on `3d5975c`, three ways | PASS, 855 OK each |
| 7 | Nothing in the report, watch file or status broken by the merge | PASS |

### Claim 1: the merge, the tag, the head

- `3d5975c` has two parents: `dbc6ad0` (first) and `4bbb43c` (second). Their merge base is `99c9161`.
- Tag `pre-S8c` is on origin and points at `dbc6ad0` (a lightweight tag). Its push time is not visible in the public API.
- `origin/s8c-wip` and `origin/dry/S8c` are both `4bbb43c`, the head the re-check passed.
- The merged tree differs from `4bbb43c` in exactly 14 files, all docs or worklog:
  - `BUILD_PLAN.md`;
  - `prereg/FJ.md`, `FJ6.md` (new), `FM.md`, `S8c.md`, `W3fix.md`, `runcommit.md`;
  - `worklog/SESSION_STATE_A.md`, `cc_2026-11-12_FJ.md`, `verify_FJ.md` (new), `verify_S8c_landing.md` (new);
  - `worklog/checkpoint_gw10/checkpoint.py`, `checkpoint.txt`, `run.txt`.
- Each of the 14 is byte-identical to `dbc6ad0`'s copy, and the branch touched none of them after `99c9161`. So the merge resolved nothing by hand.
- `worklog/checkpoint_gw10/checkpoint.py` is the only Python file among them. No workflow step, runner module or test on master refers to it.
- After the merge, master gained three commits, all docs:

| Commit | Pushed (UTC) | Files |
|---|---|---|
| `4274955` | 17:45:01 | `prereg/FJ.md`, `prereg/FM.md`, `prereg/W3fix.md` |
| `2af773c` | 18:03:16 | `prereg/W3fix.md` |
| `fc36850` | 18:11:28 | `worklog/SESSION_STATE_A.md` |

- `git diff 4bbb43c fc36850` outside `prereg/`, `worklog/` and `BUILD_PLAN.md` is empty. The run's head carries exactly `4bbb43c`'s runner code.
- Against `dbc6ad0`, the runner path changed in two files only: `fpl_xpv2.py` (+6 −2: `lift=()`, the copy fix `f1f5df2`) and `test_fpl.py` (+4: four signing lines). No runner module imports `tools/` or `analysis/`.
- The runner does read `worklog/gw_pass/` through git (REALISED). Nothing under it changed in the merge or after.

### Claim 2: master between the dry run and the merge

GitHub's push record for `master`:

| Pushed (UTC) | Move | Content |
|---|---|---|
| 12 Nov 23:40:48 | `c7551d8` → `702b834` | master at the dry run |
| 13 Nov 02:16:50 | `702b834` → `13b07b2` | `worklog/SESSION_STATE_A.md` only |
| 16 Nov 17:35:23 | `13b07b2` → `dbc6ad0` | six `prereg/` files (Boris's answers of Mon 16 Nov) |
| 16 Nov 17:44:36 | `dbc6ad0` → `3d5975c` | the merge |

- Dry run 43350236630: push to `dry/S8c`, head `4bbb43c`, 13 Nov 02:10:22 to 02:13:17 UTC, success.
- `data-dryrun-S8c` is `a3d4363`, made 02:13:11 UTC on parent `5de86ab`. Its `reports/status_dryrun.txt` and log say 855 tests green, checks 28/30 (odds skipped on a dry run; the price-date gap of 5 Nov).
- The dry branch was pushed 02:10:20 UTC, after the nightly's data commit `5de86ab` (02:07:43 UTC).

### Claim 3: the windows

- The merge was pushed at 17:44:36 UTC on Mon 16 Nov, before 21:00 UTC and long after the previous nightly's commit (01:23 UTC).
- From `events.deadline_time`: GW10 was 6 Nov 18:30 UTC; GW11 is 21 Nov 11:00 UTC. The push is 113.3 h before GW11, so the 30 h freeze (from Fri 20 Nov 05:00 UTC) is far off.
- The dispatch at 18:14:23 UTC is 112.8 h from the nearest deadline.
- The merge is the day's only runner change; the other four master pushes of 16 Nov are docs.

### Claim 4: the real run

Read from GitHub's public API (JSON downloaded with curl into a new empty folder, read only by `python -I`).

- Run 43926712904: workflow `nightly`, event `workflow_dispatch`, branch `master`, head `fc36850`, attempt 1.
- Created 18:14:23 UTC, completed 18:17:06 UTC, conclusion success. One job, every step success.
- Check runs on `fc36850`: `nightly` success and `gitleaks` success. The secret scan was also green on each of the day's five master pushes. The commit has no legacy statuses.
- Test gate, from the run's own log on `data`: `Ran 855 tests in 103.688s`, `OK (skipped=13)`, `TESTS OK`; status check 28 says "855 tests green". The 855 test ids are the same set as my local runs.
- Data commit `352228e`, by `github-actions[bot]` at 18:16:57 UTC, parent `93916ee`, pushed 18:16:59 UTC. Nine files: the export, `fpl.sql`, `fpl.sqlite`, the log (+2,705 lines, appended; the first 2,527 lines are the 01:23 run's, unchanged), the new odds snapshot, `projection_log.csv` (+2,360 −2,360), the report, `status.txt` and the watch file.
- Status: `STATUS WARN`, checks 29/30. The one WARN is check 17 (no price snapshot on 5 Nov), the same as at 01:23.
- The weekly backup step did nothing, as designed for a manual dispatch without `force_backup`.

### Claim 5: the recorded rows

**What the run recorded.** 2,360 rows, all GW11, made 18:16:46 to 18:16:48 UTC, 112.7 h before the deadline. They are the tail of the log in source order: own 296, xg 274, minutes 274, bottomup 274, fpl_ep 672, bottomup_lambda 274, xp_v2 296. They replaced the 01:23 run's 2,360 same-day rows (the S2 rule). The 62,549 older rows are identical, in order, before and after.

**Reproduction.** Two copies of `data` at `352228e`, `--restore` first, then `--record` for all seven sources. Copy A ran `dbc6ad0`'s code (pre-S8c), copy B ran `3d5975c`'s. The working export in each equals the archived 16 Nov export byte for byte.

| Source | Run | A (pre-S8c) | B (merged) | Rows equal, all columns but `made_at` | Largest difference |
|---|---|---|---|---|---|
| own | 296 | 296 | 296 | yes, both | 0.0 |
| xg | 274 | 274 | 274 | yes, both | 0.0 |
| minutes | 274 | 274 | 274 | yes, both | 0.0 |
| bottomup | 274 | 274 | 274 | yes, both | 0.0 |
| fpl_ep | 672 | 672 | 672 | yes, both | 0.0 |
| bottomup_lambda | 274 | 274 | 274 | yes, both | 0.0 |
| xp_v2 | 296 | 296 | 296 | yes, both | 0.0 |

- With `made_at` set to the run's stamps, both logs equal the committed blob `352228e:projection_log.csv` byte for byte (3,422,789 bytes).
- **xp_v2 at full precision.** The runner's `live_forecast` output (296 values, detail, the ten fixture sources, the snapshot), dumped with `repr` floats, is byte-identical under `dbc6ad0`, `3d5975c` and `fc36850`.
- **xp_v2 against the tool.** `tools/xp_v2_live.live()` at `3d5975c`, on a third copy with the local `historical/` folder, gives the same 296 players and 296 of 296 identical floats (largest difference 0.0). Each recorded value is the tool's value rounded to three places. All ten GW11 fixtures are priced from `odds_2026-11-16T1816Z.json.gz`. The tool counts 481 players keyed by code against the runner's 482, the known difference noted at the W3 final check.
- **Cross-check on the earlier inputs.** Merged code on a copy of `93916ee` reproduces, row for row, all seven sources the 01:23 run recorded with pre-S8c code.
- **What moved between the two runs is data.** own, xg, minutes and bottomup: 0 values changed. fpl_ep: 169 changed (FPL's own `ep_next`). bottomup_lambda: 119, largest 0.040. xp_v2: 230, largest 0.034. The last two follow the new odds snapshot.

### Claim 6: the suites

`git archive` copies, by discovery (`python -m unittest discover -v -p "test*.py"`), Windows, Python 3.14.7, git 2.55.0.

| Tree | Setting | Ran | Result | Skipped | Exit |
|---|---|---|---|---|---|
| `dbc6ad0` (before) | bare | 787 | OK | 11 | 0 |
| `3d5975c` | bare | 855 | OK | 11 | 0 |
| `3d5975c` | `FPL_DATA_DIR` = a copy of `352228e` after `--restore` | 855 | OK | 4 | 0 |
| `3d5975c` | `GIT_CONFIG_GLOBAL` = a file with `[commit] gpgsign = true` | 855 | OK | 11 | 0 |
| `fc36850` on the runner (Linux) | the real run's gate | 855 | OK | 13 | green |
| `13b07b2` on the runner (Linux) | the 01:23 run's gate | 787 | OK | 13 | green |

- Git confirmed it read `commit.gpgsign = true` from the hostile file.
- 68 tests were added and none removed: test_S15 17, test_S8c 20, test_S6e2 6, test_S6f 6, test_S8b 6, test_S10b 5, test_S6e 5, test_S8c_p5 2, test_W3 1.
- The runner's two extra skips are platform skips (Windows file lock, `fpl_run.bat`) in place of my time-zone and real-data skips.
- This matches the implementer's "855 OK three ways" and "master before 787 OK".

### Claim 7: the report, the watch file, the status

- **Sections:** CHIPS 34 lines, LEAGUE 58, CAPTAIN 20, BAN RISK 3, REALISED 5, all OK in both runs. Nothing is SKIPPED or FAILED in the real run's log; `STUCK CHECK OK`, `ARCHIVE OK`.
- **Status:** differs from 01:23 only in the generated time, the price-history count (+0 on a second run the same day), run duration, heartbeat age, the test gate (787 → 855) and the odds snapshot named.
- **Watch file:** differs in its header line only (the export and record times).
- **Report:** 23 lines differ: the STATUS line, ownership percentages, the export CHIPS and CAPTAIN name, the Free Hit line (decision 3) and the captain table (decision 4).
- **Proof it is data, not the merge.** I rebuilt the folder as it stood when the sections ran (data `352228e`, with `exports/fpl_export_gw10_2026-11-16.json.gz` still the 01:23 copy) twice, and ran `--watch`, `--diff` and `fpl_sections.py` from full clones at `dbc6ad0` and at `fc36850`.
  - The two watch files and the two reports are byte-identical to each other.
  - Both equal the real run's, apart from the STATUS line and blank line `checks.py` puts on top. I did not run `checks.py` (it calls the network).

## The verifier's checks

| Check | Result | Evidence |
|---|---|---|
| Prereg before code | PASS | `prereg/S8c.md` first committed `de8ca68` (20 Oct 13:23:54 +02:00); first S8c code `7773a58` (13:27:42 +02:00) |
| 1a Truncation | PASS | GW11 is the only gameweek the run forecasts. Rebuilt from the 16 Nov export (generated 18:16:45 UTC; every history row is round 10 or earlier; GW11's ten fixtures unplayed, first kickoff 21 Nov 12:30 UTC) and the 18:16 UTC odds snapshot: largest difference 0.0 |
| 1b Timestamp audit | PASS | My count: 0 GW11 rows at or after 21 Nov 11:00 UTC, and no row made after the run ended. The run's own check 20: 0 of 64,909 rows at or after their deadline |
| 1c Shift probe | not applicable | The item produces no correlation metric |
| 2 Test counts | PASS | 787 before, 855 after; claim 6 |
| 3 Pre-registered evaluation | not applicable | A landing; the prereg sets no pass/fail metric. The reproduction is claim 5 |
| 4 Rulings on file | PASS | below |
| 5 Recording path | PASS | All seven sources identical under pre-S8c and merged code; claim 5 |
| 6 Mutation spot-check | PASS | 3 of 3 red; below |
| 7 Secrets | PASS | below |

**Check 4, the rulings.**
- "Answers, Mon 16 Nov" point 1 is in `prereg/S8c.md` verbatim as quoted in my launch. It was committed in `dbc6ad0` and pushed at 17:35:23 UTC, 9 minutes before the merge push.
- "Rulings, Thu 12 Nov night" (S8c points 1 to 6 and the Schedule) entered the file in `88c77df` (12 Nov 22:49 UTC), before the branch commits that act on them (22:49 to 23:08 UTC).
- Point 5's pin is `97ded86`, before its code `f5cc8b3`.
- The move from Fri 13 to Mon 16 Nov is covered by point 1 of the Mon 16 answers ("S8c: yes, tonight").
- Done as ruled: master had gained only docs since the dry run; tag `pre-S8c`; merge of `4bbb43c`; pushed before 21:00 UTC; final verifier on the real run. Still to do, as ruled "after": delete the two dry branches.
- I compared nothing with the chat; the verifier never reads transcripts.

**Check 6, mutations** (scratch copies of `3d5975c`; the three guards pass unmutated).

| Mutant | Guard | Result |
|---|---|---|
| `fpl_xpv2.py`: `gate[int(pid)] = True` → `False` | `tests.test_W3.Copies` | red |
| The status gate always open, in `fpl_xpv2.py` and `tools/xp_v2_live.py` together | `tests.test_W3.StatusGateInTheRecord` | red |
| `test_fpl.py` `DataGate.setUp`: the signing line removed, under the hostile global config | `tests.test_S8c_p5` | red |

**Check 7, secrets.**
- The 56 files the merge and the three later commits change: no key value, no URL with `apiKey=` and a value, no Authorization or Bearer value, no bare 32-hex run. The 13 added lines that mention `apiKey` are verifier reports describing their own scans.
- The real run's log, report, status and watch file: no `apiKey=`, Authorization or Bearer text. The run's own check 23 says "7 file(s) to commit, none holds a key pattern or the key value".
- The odds snapshot holds 20 strings of 32 hex characters. They are the Odds API's event ids (one per event, in the `id` field), not keys; none is printed here.
- `ODDS_API_KEY`, `GH_TOKEN` and `GITHUB_TOKEN` were unset in every command I ran.

## Notes for the record (no action)

- `fc36850`'s title says "18:15 UTC"; it was committed at 18:11:26 and pushed at 18:11:28 UTC.
- The local branch `s8c-wip` is the old `d9071b8` (held by an old worktree, as the state file says). `origin/s8c-wip` is `4bbb43c`.
- The comment in `.gitattributes` says `csv.writer` ends every row with CRLF. The record on Windows wrote LF only in my copies. The repository stores LF either way, and my logs match the committed blob.

## How I worked

- Scratch only: `C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vfy_s8c_final` (archive copies, two full clones, the data copies, the suite outputs) and, beside it, `dl_api`, `dl_api2` (downloads) and `scripts` (my readers).
- In `C:\GIT\FPL-data`: `git pull --ff-only` ("Already up to date", `352228e`) and read-only reads. No sync, no record, no nightly there.
- `--record`, `--watch`, `--diff` and `fpl_sections.py` ran on scratch copies only. No network call except the GitHub API downloads and `git fetch` / `ls-remote`.
- Downloads were read only by `python -I` readers kept in a separate folder.
- No push, merge, tag or deletion. At the end `git status` is clean in `C:\GIT\FPL` apart from this file, and clean in `C:\GIT\FPL-data`.

VERDICT: PASS. Master `3d5975c` is a clean two-parent merge of the re-checked head `4bbb43c` into `dbc6ad0` (tag `pre-S8c`), and the run's head `fc36850` adds docs only, so the real run executed exactly the runner code that was verified. It was pushed at 17:44 UTC, 113 hours before the GW11 deadline, and the dispatched run 43926712904 went green on `fc36850` with 855 tests and committed data `352228e`. Its 2,360 GW11 rows were made 112.7 hours before the deadline and reproduce exactly on copies of its inputs: xp_v2 equals the tool's forecast to the last bit, and all seven sources are row for row what pre-S8c code gives, as are the watch file and the whole report. The suites are 855 OK bare, with the data and with commit signing forced on (787 before), three single-line mutants went red, the rulings acted on are on file before the acts, and no file holds a secret. The two differences between today's reports (the Free Hit flag and the captain order) are data effects that pre-S8c code reproduces, and both belong to W3fix.
