# verify_runcommit — pre-check of `origin/runcommit-wip` 7f44c65, before its dry run and merge

Verifier: backtest-verifier, model Fable 5.2 (`claude-fable-5-2`), launched at high, not confirmable.
Run: Thu 19 Nov 22:48 UTC to Fri 20 Nov 00:50 UTC, with a power cut in the middle.
After the cut I re-read `.claude/agents/backtest-verifier.md` from disk (it equals my loaded instructions), checked every scratch copy against its commit, and reran what was interrupted: the two last suite runs and every mutant run.

- Code under test: `7f44c65` (one commit on `75cb591`; seven files, +261 −24).
- Before: local `master` `75cb591`. Its commits since `origin/master` are prereg, worklog and state files only.
- Data: copies of `data` at `029bcfd`, made with `git archive` from the shared object store, then `--restore`.
- In `C:\GIT\FPL-data` I ran `git pull --ff-only` (already up to date) and, read-only, `git status`, `git log`, `git rev-parse` and `sha256sum`. Nothing was written there.

## Verdict in short

**WARN.** Every behaviour claim reproduces, on the real data and end to end, and no check fails. Three things stop a PASS:

1. **The tests do not pin the bug as it happened.** Putting back the name lookup on the previous export's side prints "Thomas COV £5.5 -> £4.0 (-1.5)" again on tonight's data, and the whole suite stays green (869 OK). The same holds for the two false new flags and the three false form movers.
2. **Two pinned tests are missing.** The addendum pins "NEW FLAGS / FORM MOVERS follow the ids": no test reads the FORM MOVERS block. The acceptance tests pin all three records "for a real run and a dry run": no test passes `GITHUB_SHA` through `checks.main`, so the status field's wiring can be removed with the suite green.
3. **One count does not reproduce.** `tests/test_runcommit.py` is 12 red on `75cb591`, not 11.

15 of my 32 mutants survive the whole suite. The implementer's eight, as I rebuilt them, are all red.

## Prereg before code

| Commit | Committer time (UTC) | What |
|---|---|---|
| `0be8309` | 3 Nov 21:42:58 | `prereg/runcommit.md` created (the ruling of Tue 3 Nov) |
| `73c4a12` | 19 Nov 22:20:28 | Boris's message of Thu 19 Nov late, verbatim |
| `75cb591` | 19 Nov 22:22:04 | the addendum (price-moves fix, RMSE columns) |
| `7f44c65` | 19 Nov 22:37:01 | the item's only code commit, on any branch |

- **PASS**: the prereg and its addendum were committed before the code.
- The addendum's heading says 22:55 UTC. Its commit is 22:22:04 UTC, and the code commit is 22:37:01 UTC, before the heading's own time. By commit time the order holds.
- Every ruling named in the launch is in the file. Boris's late message matches the launch's quotation word for word.
- `73c4a12`'s note says the design is pinned "after the GW11 deadline". It was pinned and coded on Thu 19 Nov, before the deadline (Sat 21 Nov 11:00 UTC). Only the merge waits. See decision 6.

## Claim 1: the three records

**Reproduced.** `GITHUB_SHA` is the only variable read (`checks.py:659`, `fpl_nightly.py:207`, `fpl_publish.py:178-179`); no `git rev-parse` or other variable anywhere on the runner path. The workflow's master checkout has no `ref:`.

One correction to the claim's wording: `checks.code_commit` serves the status line only. The log line and the commit message each read `GITHUB_SHA` themselves.

**Status line**, `checks.main` on a git copy of the data, fixed clock, explicit environment:

| Run | File | Last field |
|---|---|---|
| real, `GITHUB_SHA` set | `status.txt` | ` \| repo ? MB \| code 7f44c65` |
| real, no `GITHUB_SHA` | `status.txt` | ` \| code ?` |
| real, `GITHUB_SHA` empty and `GIT_COMMIT` set | `status.txt` | ` \| code ?` |
| dry (push to `dry/runcommit`), `GITHUB_SHA` set | `status_dryrun.txt` only | ` \| code 7f44c65` |
| dry dispatch, no `GITHUB_SHA` | `status_dryrun.txt` only | ` \| code ?` |
| `75cb591`'s code, same inputs | `status.txt` | no field |

- Against `75cb591`'s status file on the same inputs, only the first line differs; all 31 check lines are identical.
- `status_time` reads 22:00:00 from the longer line. So do check 26 (heartbeat) and `fpl_nightly.backup_due`.
- `fpl_publish.checks_failed` on the longer line: unchanged since HEAD gives `[]`, a FAIL night gives the FAIL line, a WARN night gives `[]`, for both `status.txt` and `status_dryrun.txt`.
- The dry-run gate reads the data branch's commit time, not its message. Nothing parses the message.

**Commit message**, `fpl_publish.main` on the same copy, pushing to a local bare remote in the scratch folder only:

| Run | Message |
|---|---|
| real, `GITHUB_SHA` set | `nightly 2026-11-19 7f44c65 [skip ci]` |
| real, no `GITHUB_SHA` | `nightly 2026-11-19 [skip ci]` |
| real, `GITHUB_SHA` empty and `GIT_COMMIT` set | `nightly 2026-11-19 [skip ci]` |
| local run, no `GITHUB_*` at all | `nightly 2026-11-19 [skip ci]` |
| dry push, new code | `dry run 2026-11-19 dry/runcommit 7f44c65 [skip ci]` |
| dry push, `75cb591`'s code | the same message, byte for byte |
| dry dispatch, no `GITHUB_SHA`, no ref name | `dry run 2026-11-19 [skip ci]` |

**Log line.** I did not run `fpl_nightly.py` end to end (it would call `fpl_sync.py`). The evidence is the two-line change read in place after `using:`, the item's two `LogLine` tests (green on the branch, red on `75cb591`), and mutants V01, V02, V05 and I01, all red.

## Claim 2: the price-moves fix

**Reproduced.** The nightly's `--diff` report on two copies of the data, `75cb591`'s code against the branch's: 504 lines against 501, and nine lines differ, all in the three blocks.

Each removed line, by id in the two exports (`fpl_export_gw9.json` of 6 Nov, `fpl_export_gw10.json` of 19 Nov):

| Master printed | By id | Whose value it was |
|---|---|---|
| Thomas COV £5.5 -> £4.0 (-1.5) | COV Thomas is id 173: £4.0 in both exports | HUL Thomas, id 642, £5.5 |
| !! Thomas COV d 50% | id 173 was `d` in both: not new | HUL Thomas was `a` |
| !! James CHE i 0% | CHE James, id 142, was `i` in both: not new | LEE James, id 343, was `a` |
| Kamara AVL L4 15 (+15) | id 47: 15 -> 15, +0 | HUL Kamara, id 293, 0 |
| Palacios IPS L4 15 (+12) | id 619: 12 -> 15, +3 | FUL Palacios, id 570, 3 |
| Fofana CHE L4 12 (+10) | id 145: 11 -> 12, +1 | SUN Fofana, id 646, 2 |

- The branch prints 4 price moves (Barry, Gabriel, Groß, Verbruggen), 4 new flags (Gvardiol, Guéhi, Manzambi, Thiago) and 10 form movers. My own rebuild by id, with no project code, gives the same lines in the same order. B.Fernandes, J.Murphy and Trafford take the three freed places.
- Ids are integers in `all_players` and in `squads.player_id` in both exports; no duplicate ids; 18 names are shared by two players.
- One squads row without `player_id`, or with `None`, or all rows without: one line, "not comparable: squads rows without player_id". No block is printed; TABLE and CHIPS PLAYED SINCE stay.
- Over all seven consecutive export pairs the branch raises no exception. Master's report carried the false Thomas line in every pair from GW5 -> GW6 on.
- A behaviour change to know: exports of GW3-6 have no `player_id` in `squads`. A diff with one of them as the current export now prints the one line where the old code printed the blocks. The runner's current export has had `player_id` since GW7.

## Claim 3: the calibration RMSE columns

**Reproduced.** `--section calibration` on the same data, both codes:

- The branch's output, with the two columns and the "RMSE x vs constant y" clause cut out, equals `75cb591`'s byte for byte.
- All 31 per-gameweek verdicts and all six "real signal" verdicts are identical.
- The six `minutes` rows print `-` in both new columns.
- `p1_eval.py` is identical in both trees.
- The calibration section is not part of the nightly report; it is the local `--section calibration` only.

Independent rebuild from `projection_log.csv` and `fpl.sqlite` alone (no project code): all 31 table rows equal the printed MAE, const, RMSE and rconst.

| Source | n | MAE | constant | RMSE | constant |
|---|---|---|---|---|---|
| own, GW4-10 | 1,963 | 2.081998 | 2.307939 | 3.098465 | 3.062284 |
| xg, GW4-10 | 1,821 | 2.445404 | 2.335912 | 3.118961 | 3.100172 |
| bottomup, GW5-10 | 1,566 | 2.227784 | 2.292110 | 2.991762 | 3.042921 |
| bottomup_lambda, GW9-10 | 549 | 2.019153 | 2.179568 | 2.783492 | 2.912739 |
| fpl_ep, GW8-10 | 2,007 | 1.138814 | 1.665301 | 2.193720 | 2.430732 |

- The claim's figures for own (2.082, 2.308, 3.098, 3.062) match.
- `rconst` uses the pool's mean realised points, the MAE's constant; it equals the population standard deviation of realised points.
- What the column shows: own beats the constant on MAE in every gameweek but loses on RMSE over GW4-10 and in each of GW7-10 (bias −0.96 to −1.53 in those weeks). Report only, by the ruling.
- Not pinned, not done: the section's DEFINITIONS block does not define RMSE or rconst, and the minutes note still reads "its MAE, const and bias are undefined". See decision 4.

## Claim 4: tests and mutants

**Counts.** `tests/test_runcommit.py` has 14 tests. On `75cb591` with only that file added: **12 red** (9 failures, 3 errors), 2 green. The claim says 11.

- Green on the old code: `test_without_github_sha_the_field_is_left_out` and `test_the_publisher_still_sees_a_failed_night`.
- The two edited old tests (`test_S3`'s exact status line, `test_fpl`'s minutes-row regex) are red on the old code and green on the new.

**The implementer's eight mutants**, as I rebuilt them from their names: 8 of 8 red on `tests.test_runcommit`.

**My 32 mutants.** 17 red, 15 survive. The 15 were confirmed on the whole suite by discovery: 14 together in one tree (869 OK, 11 skipped) and V04 alone (869 OK, 11 skipped).

| Mutant | Result | Effect on tonight's real data |
|---|---|---|
| V03 log line: `GIT_COMMIT` when `GITHUB_SHA` is absent | survives | a substitute outside Actions |
| V04 log line: `git rev-parse HEAD` when `GITHUB_SHA` is absent | survives | a substitute outside Actions |
| V06 `checks.main` no longer passes the commit | survives | the status line always says `code ?` |
| V11 real message: `GIT_COMMIT` when `GITHUB_SHA` is absent | survives | a substitute outside Actions |
| V15 FORM MOVERS matched by name | survives | Kamara, Palacios and Fofana come back |
| V16 `*YOURS*` by name | survives | none tonight |
| V17 NEW FLAGS: previous status by name | survives | Thomas COV and James CHE come back |
| V20 `any` squads row with `player_id`, not `all` | survives | none tonight |
| V21 price moves: previous price by name | survives | "Thomas COV £5.5 -> £4.0 (-1.5)" comes back |
| V22 price-move rows ordered by id | survives | the rows change order |
| V23 "our squad" is the whole league | survives | 22 lines change |
| V24 summary rconst against the MAE value | survives | 5 summary lines change |
| V28 "real signal" also needs RMSE below the constant | survives | own and xg lose "real signal" |
| V29 per-gameweek verdict: beats if MAE or RMSE beats | survives | xg GW4, GW7, GW10 flip to "beats const" |
| V30 summary prints the two RMSE values swapped | survives | 5 summary lines change |

Red (17): V01, V02, V05 (log line); V07, V08, V09, V10 (status field); V12, V13, V14 (messages; V13, the dry-run message, by `test_fpl.Publish` and `test_W1b`); V18, V19 (diff); V25, V26, V31, V32 (RMSE formula and table); V27 (minutes row, by `test_fpl`).

Why the diff mutants survive: the toy puts the other Thomas first in the previous export, so a name-keyed dictionary of previous players returns our own Thomas. That defeats the old code's lookup on the current side only. The real collision was on the previous side (Hull's Thomas is later in the list than Coventry's).

Why V28 and V29 survive: the one verdict test has MAE beating and RMSE losing. No test has the opposite case, and none reads the "real signal" line with RMSE losing.

## Claim 5: the recording path

**Reproduced.** Two copies of the data, `--restore`, then `--record` for all seven sources: copy A with `75cb591`'s code, copy B with the branch's. Both ran 19 Nov 22:55 UTC, 36 h before the GW11 deadline.

| Source | A | B | Equal apart from `made_at` |
|---|---|---|---|
| own | 292 | 292 | yes |
| xg | 271 | 271 | yes |
| minutes | 271 | 271 | yes |
| bottomup | 271 | 271 | yes |
| fpl_ep | 672 | 672 | yes |
| bottomup_lambda | 271 | 271 | yes |
| xp_v2 | 292 | 292 | yes |

- The 69,595 earlier rows are identical and in order in both copies.
- The 2,340 new rows also equal the nightly's own rows of 19 Nov in every column but `made_at`, in order.
- With today's `made_at` masked, the two logs are equal.

## Claim 6: the suites

`git archive` copies, by discovery, Windows, Python 3.14.7, git 2.55.0.

| Tree | Setting | Ran | Result | Skipped |
|---|---|---|---|---|
| `75cb591` | bare | 855 | OK | 11 |
| `7f44c65` | bare | 869 | OK | 11 |
| `7f44c65` | `FPL_DATA_DIR` = a restored copy of `029bcfd` | 869 | OK | 4 |
| `7f44c65` | `GIT_CONFIG_GLOBAL` = a file with `[commit] gpgsign = true` | 869 | OK | 11 |
| `7f44c65` | the runner's variables of a scheduled run (`GITHUB_SHA`, `GITHUB_REF` master, `GITHUB_EVENT_NAME` schedule) | 869 | OK | 11 |
| `7f44c65` | the variables of a push to `dry/runcommit` | 869 | OK | 11 |

- 14 test ids added, all in `tests.test_runcommit`; none removed. The same 869 ids ran in every branch run.
- Git confirmed it read `commit.gpgsign = true` from the hostile file.
- The last two rows are mine, not in the claim: on the runner the suite runs with `GITHUB_SHA` in its environment, and the new tests hold there.
- The first two rows finished before the power cut and their outputs are complete. The others were run after it.

## Claim 7: nothing else moves

**Reproduced**, same data, both codes, run back to back:

| Output | Result |
|---|---|
| nightly report (`--diff --out`) | only the nine lines of claim 2 |
| report after `fpl_sections.py` (CHIPS, LEAGUE, CAPTAIN, BAN RISK, REALISED) | only the same nine lines |
| watch file | identical, and equal to the nightly's `watch_2026-11-19.txt` |
| `reports/status.txt` | only the first line's new field |
| `--stuck`, `--brief`, the plain report | identical |
| `--section` wildcard, backtest, compare, bench_boost | identical |
| `--section calibration` | only the new columns and clause (claim 3) |

## The verifier's checks

| Check | Result | Evidence |
|---|---|---|
| Prereg before code | PASS | commit times above |
| 1a Truncation | PASS | own at GW4, GW7 and GW10 rebuilt from log rows made before each deadline and from `fpl.sqlite`: RMSE and rconst differ from the item's unrounded values by 0.0 (all 31 source-gameweeks: 0.0) |
| 1b Timestamp audit | PASS | 0 of 71,935 log rows made at or after their deadline; each graded snapshot is 3.1 to 19.6 h before it |
| 1c Shift probe | no WARN | the item adds no correlation metric. For information, own among players with 60+ minutes in g and g+1 (n 941): rho +0.066, shifted +0.047, difference +0.019 |
| 2 Clean-checkout suites | PASS | 855 OK before, 869 OK after (claim 6) |
| 3 and 4 Evaluation, metric | not applicable | no pass/fail metric in the prereg; the RMSE columns are report only and no verdict reads them (claim 3) |
| 5 Recording path | PASS | claim 5 |
| 6 Mutation | PASS for the spot-check, with the WARN | 17 of my 32 red and the implementer's 8 of 8 red; 15 survive |
| 7 Secrets | PASS | no key, no `apiKey=`, no Authorization value in the seven files; the only long hex string is the test's dummy commit `0123...` |
| The item's own acceptance tests | WARN | two pinned tests missing; the dry run and the real run are still to come |

## Write guard

- `C:\GIT\FPL`: `git status` shows only `worklog/gw_pass/gw11/` (there before my run, untouched) and this file. HEAD is `75cb591`. I ran `git fetch origin runcommit-wip` and `git archive` there; nothing else.
- `C:\GIT\FPL-data`: clean, at `029bcfd`.
- No push to GitHub. The publisher runs pushed to a bare repository inside the scratch folder.
- My scratch folders (`base`, `new*`, `mut`, `r_*`, `data*`, `remoteE.git`, `out`, and my files in `scripts`) are left in the session scratch folder. I touched nothing else there.

## Decisions for the chat

1. **Tests for the bug as it happened.** Add tests that put the namesake after our player in the previous export, for all three blocks, so V15, V17 and V21 go red? Until then the suite cannot tell the fix from the bug on tonight's data.
2. **The two pinned tests.** Add the FORM MOVERS assertion the addendum pins, and a test that passes `GITHUB_SHA` through `checks.main` for a real and a dry run (V06)?
3. **The substitute rule.** The pin is "never a substitute" for all three records; only `checks.code_commit` is tested against one (V03, V04, V11 survive). Add a decoy variable to the log and message tests, or route all three through `checks.code_commit`?
4. **The calibration tests and text.** Add value checks for the summary line and the two verdict cases that survive (V24, V28, V29, V30)? And should DEFINITIONS and the minutes note name RMSE and rconst? The prereg pins neither.
5. **The count.** The commit message says 11 red on the old code; I get 12. Which test did the implementer count as green?
6. **"After the GW11 deadline."** The code and its pin were made before the deadline, on a work branch. Confirm that the phrase governs the merge only.
7. **The order of landings.** W3fix lands on Sat 21 Nov and changes the runner. This check is of `7f44c65` on `75cb591`; the head rebased onto W3fix needs a short re-check before its dry run.
8. **Small ones, no action needed unless wanted:** V16, V20, V22 and V23 (row order, `*YOURS*`, `any`/`all`, "our squad"); `checks.py`'s header comment still shows the status line without the code field; the heading time of the addendum (22:55) is later than its commit (22:22).

VERDICT: WARN

The code does what the prereg pins: with `GITHUB_SHA` the log, the status line and a real run's data commit carry its first seven characters, and without it they say `unknown (no GITHUB_SHA)`, `code ?` and nothing; the three diff blocks match by id and remove exactly the six false lines of tonight's report; the RMSE columns equal an independent rebuild and leave every verdict byte-identical; the seven sources record the same rows; the suites are 855 OK before and 869 OK after in six settings; no leak, no secret, nothing written outside this file. It is not a PASS because the tests do not hold the fix in place: the lookup that produced "Thomas COV £5.5 -> £4.0" can be put back with the suite green, two tests the prereg pins are missing (FORM MOVERS by id; the status field through `checks.main` for a real and a dry run), 15 of 32 mutants survive, and the claimed 11 red tests on the old code are 12.
