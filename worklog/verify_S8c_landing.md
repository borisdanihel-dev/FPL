# verify_S8c_landing: the verifier's pre-check of the S8c landing

**VERDICT: PASS** for the new head `4bbb43c` (the re-check of Thu 12 Nov night, the last section of this file).

The pre-check of `f1f5df2` was **FAIL** (two things to settle before the dry run; every measured claim reproduces). Both are settled on `4bbb43c`. The pre-check's text below stands as written, its own verdict included.

- Verifier: Fable 5.2 (`claude-fable-5-2`), launched at high, not confirmable.
- `.claude/agents/backtest-verifier.md` was read from disk first. It is the same text as my loaded instructions.
- Checked: `origin/s8c-wip` = `s8c-land` = `f1f5df2`, against master `273100b`. Data: `C:\GIT\FPL-data` at `6f9ecb8`, read through my own copies (not pulled by me).
- Thu 12 Nov 2026, about 21:40 to 22:10 UTC.

## Why FAIL

Nothing in the branch is technically wrong: the merge lost nothing from its two parents, the twelve lines and the guard do what the pin says, the copy fix moves no recorded value, and the suite is green in all four settings. The verdict is FAIL for two reasons outside the numbers.

1. **The landing leaves out the final commits of three of its own items.** `s8c-wip` carries the code of S6f, S6e2 and S8b but branched off each of them before its "done" commit. Missing from the branch: two test lines that close the S6f verifier's finding, the CHANGELOG entries for S6f and S6e2 (two measured results, both "the test FAILS"), three reports and three verifier reports. One of those is the PASS that clears S6e2's WARN; the branch holds only the WARN. The launch text says their verifier reports are on the branch; for these three they are not. Fixing this changes the head, so `f1f5df2` cannot be the commit that lands.
2. **`f1f5df2` changes a runner file and no ruling for it is in `prereg/S8c.md`.** The main session says so itself (pending Boris's OK). By the verifier file's rule that is a FAIL of check 4 until the ruling is pasted there.

## Decisions for the chat

1. **Bring the three tips into `s8c-wip` before the dry run?** They are `origin/s6f-wip` `0b16969`, `origin/s6e2-wip` `d87f8aa` and `origin/s8b-wip` `cfa7a36`. Together they add 2 lines to `tests/test_S6f.py`, 2 CHANGELOG entries (115 becomes 117) and 6 worklog files; no tool or runner file. I recommend yes, then the suite again and a short re-check of the new head, so the dry run proves the tree that merges.
2. **Boris's OK for `f1f5df2`** (the runner's `forecast` takes the tool's text again, with `lift=()`). On its merits it is right and it is needed: without it the suite is red at `tests.test_W3.Copies`. If OK, the ruling goes verbatim into `prereg/S8c.md` before the merge.
3. **A test that the record keeps the status gate.** With `f1f5df2` the runner module can lift the gate, and no test would notice if its one caller did. I made `live_forecast` pass `lift` for every player: the whole suite stayed green (854 OK), and on the real data the forecast grew from 299 players to 327. The W3 toy has no flagged player (all 30 are status 'a'). Suggested: one W3 test on the toy with a status 'd' player, asserting the runner gives him no xp_v2. Tests only. With the landing, or after?
4. **The twelfth line** (`tests/test_S3.py` `ChecksMain.setUp`). Leaving it out turns nothing red, as claimed. The pin allows "red, or shown covered by another line"; this line is neither. Accept it as the one unguarded line, or make that `setUp` check its commit's exit code so the guard can cover it?
5. **Operating mode (d).** `s8c-wip`, with the runner-file commit, was pushed at 21:36 UTC. It went to a work branch and starts no workflow, and tonight's ruling names master only. Mode (d) says "never pushed between 21:00 UTC and the end of that night's nightly run" without naming a branch. Say which reading holds.
6. **Docs still to come.** The branch has no CHANGELOG entry or report yet for point 5 and the copy fix. Adding them moves the head again (docs only). Also, master's CHANGELOG already holds the entry "W2 amendment 2: any exception inside a section ends SKIPPED" twice (entries 80 and 95, identical text); the landing keeps both. Not this landing's doing.

## The five claims

| # | Claim | Result |
|---|---|---|
| 1 | Outside `tools/`, `tests/`, `prereg/`, `worklog/` and `CHANGELOG.md` the branch differs from master only in `fpl_xpv2.py` | Holds in substance. As worded it misses `test_fpl.py`, which is at the root and also differs (4 of the twelve lines). The only non-test file is `fpl_xpv2.py`. |
| 2 | Suite counts | Reproduced exactly; table below. |
| 3 | Each of the twelve lines left out: guard red for 11, green for `ChecksMain` | Reproduced exactly; table below. |
| 4 | The copy fix moves nothing recorded: the same 299 GW11 xp_v2 rows | Reproduced, and more: all seven sources identical, and identical to the nightly's own rows. |
| 5 | The nightly imports nothing under `tools/` or `analysis/`; tests stay hermetic | Confirmed by my own import trace and by the existing tests passing. |

### Claim 2: the suite

All on `git archive` copies, `python -E -s -B -m unittest discover -v -p "test*.py"`, `ODDS_API_KEY` unset. The signing config is a `GIT_CONFIG_GLOBAL` file holding only `[commit] gpgsign = true`.

| Tree | Setting | Ran | Result | Skipped |
|---|---|---|---|---|
| master `273100b` | plain | 787 | OK | 11 |
| merge `33304d8` | signing on | 852 | 69 not passing (59 errors, 10 failures) | 10 |
| `f1f5df2` | plain | 854 | OK | 11 |
| `f1f5df2` | signing on | 854 | OK | 11 |
| `f1f5df2` | `FPL_DATA_DIR` = my data copy, after `--restore` | 854 | OK | 4 |
| `f1f5df2` plus master's three newer files (the tree a merge would give) | plain | 854 | OK | 11 |

The 69 on `33304d8`, by class, match the claim line for line:

| File | Class | Count |
|---|---|---|
| `test_fpl` | DataGate | 28 |
| `test_fpl` | Publish | 11 |
| `test_fpl` | PrePush | 6 |
| `test_fpl` | NightlyRunner | 2 |
| `test_S3` | PublishOnAFail | 4 |
| `test_W1` | OddsAppendOnly | 3 |
| `test_W1` | OddsNeverCostsTheNight | 1 |
| `test_W1b` | DueGate | 9 |
| `test_W1b` | Hook | 2 |
| `test_W1b` | PushRunPublishes | 2 |
| `test_W3` | Copies | 1 (the merge break, not signing) |

- Every one of master's 787 test ids is still on the branch. The 67 new ones: `test_S15` 17, `test_S8c` 20, `test_S6e2` 6, `test_S6f` 6, `test_S8b` 6, `test_S10b` 5, `test_S6e` 5, `test_S8c_p5` 2.
- The data run changed nothing in my data copy except the working export that `--restore` wrote.

### Claim 3: the twelve lines

Twelve scratch copies of `f1f5df2`, each with one line left out, then `tests.test_S8c_p5`. The unchanged copy is green (2 tests, about 9.5 s).

| Line left out | Guard | The test that went red inside it |
|---|---|---|
| `test_fpl.py` NightlyRunner `_data_repo` | red | NightlyRunner restore test |
| `test_fpl.py` DataGate.setUp | red | DataGate changed-frozen-forecast test |
| `test_fpl.py` Publish._ident | red | Publish dry-run-on-master test |
| `test_fpl.py` PrePush.setUp | red | PrePush code-push test |
| `tests/test_S3.py` ChecksMain.setUp | **green** | none: the helper does not check the commit's exit code |
| `tests/test_S3.py` PublishOnAFail seed | red | PublishOnAFail dry-run test |
| `tests/test_S3.py` PublishOnAFail run clone | red | the same test |
| `tests/test_W1.py` OddsAppendOnly.setUp | red | OddsAppendOnly deleted-file test |
| `tests/test_W1.py` OddsNeverCostsTheNight seed | red | crashing-collector test |
| `tests/test_W1.py` OddsNeverCostsTheNight data clone | red | the same test |
| `tests/test_W1b.py` DueGate.setUp | red | DueGate manual-dry-run test |
| `tests/test_W1b.py` Hook.setUp | red | Hook dry-pushes test |

Each red is the intended site's own test and no other.

### Claim 4: the record

Two fresh copies of the data, `--restore` first, then `--record` for all seven sources: copy A with master's code, copy B with `f1f5df2`'s.

- **xp_v2:** 299 GW11 rows in each; (event, player, value) identical; largest difference 0.0.
- **The other six sources:** identical between A and B, row for row.
- **Against the nightly:** both equal the rows the 12 Nov nightly recorded, in order, for all seven sources. Only `made_at` differs.
- **Older rows:** the 53,043 rows not made today are identical in order in A, B and the untouched log.
- **Full precision:** the runner's `live_forecast` output (xp, detail, sources, snapshot), dumped with `repr` floats, is byte-identical under the two codes.
- **Report path:** the watch file and the whole report, added sections included (CAPTAIN is the other caller of the forecast), are byte-identical between A and B.
- Only the 12 Nov export carries player codes, so GW11 is the only gameweek the runner path can forecast today; the other 52 dated exports are refused by both codes with the same message.

## The other checks asked for

### The merge `33304d8`

- Parents `3a72ddb` (s8c side) and `99c9161` (master); base `271eecc`. The s8c side changed 38 files, master 58; only `CHANGELOG.md` was changed on both.
- Every file other than `CHANGELOG.md` equals one parent exactly: the 38 equal the s8c side, the 58 equal master.
- `CHANGELOG.md`: base 101 entries, each side 108, merge 115. Compared entry by entry (separators aside), the merge is exactly the union of the two sides, every entry's text unchanged, each side's order kept, no conflict markers. 101 + 7 + 7 = 115 holds. One of master's seven is the duplicate noted in decision 6.
- The earlier merge on the branch, `3a72ddb`, passes the same audit (100 and 101 entries give 108).
- **Not in the merge, and the reason for the verdict:**

| Item | Tip not in the landing | What the landing lacks |
|---|---|---|
| S6f | `origin/s6f-wip` `0b16969` (2 commits) | `tests/test_S6f.py` +2 lines (the verifier's one green mutation closed); the CHANGELOG entry "S6f (F-D): ... the test FAILS"; `cc_2026-10-19_S6f.md`; `verify_S6f.md` (PASS) |
| S6e2 | `origin/s6e2-wip` `d87f8aa` (1 commit) | the CHANGELOG entry "S6e2: ... the test FAILS; the line closes"; `cc_2026-10-19_S6e2.md`; `verify_S6e2_a1.md` (PASS). The branch holds only `verify_S6e2.md`, verdict WARN |
| S8b | `origin/s8b-wip` `cfa7a36` (1 commit) | `cc_2026-10-20_S8b.md`; `verify_S8b.md` (PASS). Its CHANGELOG entry is already there, identical |

  - The tools of all three are identical between the landing and their tips, so no behaviour differs.
  - S6f's final test file passes on the landing's tools (6 tests OK).
  - Master's CHANGELOG mentions neither S6f nor S6e2 today, and would not after this landing.
  - S10b, S6e, S15 and S8c (through amendment 4) are complete: their tips are ancestors of the branch.

### Point 5 against the pin

- The pin `97ded86` (21:20:19 UTC) precedes the code `f5cc8b3` (21:24:02 UTC) in git. The gap is 3 min 43 s; git order is what the rule asks and I cannot see earlier working-tree states.
- The merge `33304d8` (21:15:37 UTC) precedes the pin but follows amendment 5 (`a4cb2df`, 21:01:10 UTC), which carries the ruling to make `s8c-wip` ready to land.
- Exactly twelve `commit.gpgsign false` lines, at the twelve sites the pin names, each right after its init or clone. `f5cc8b3` touches only the four test files and adds `tests/test_S8c_p5.py`.
- The guard's two tests are as pinned: a hostile global config breaks an unprotected commit and the per-repo setting cures it; one test per site passes in a child process under that config.
- The existing hermetic test (`tests.test_S3.Hermetic`) now also runs the guard class in its empty-home child (15 git-using classes, 14 on master) and passes.
- No non-test file changes in `f5cc8b3`.

### The copy fix `f1f5df2`

- `fpl_xpv2.forecast` equals `tools/xp_v2_live.forecast` by syntax tree and by source text. All 8 copied definitions of `fpl_xpv2.py` match the tool. On `33304d8` and `f5cc8b3` only `forecast` differed.
- Against master's `forecast`: the new one, minus the `lift` argument, the docstring and the two-line loop over `lift`, is identical by syntax tree. Every other top-level statement of the file is identical. `lift` is used once, in that loop.
- The runner never passes `lift`. The only call is `fpl_xpv2.live_forecast`, with six positional arguments; `fpl_squad.captain` and `fpl_xpv2.record` go through it. The only caller that passes `lift` is `tools/gw_pass.py`.
- Control: `forecast(..., lift=())` equals the call without it; lifting one flagged player moves that player only. So the gate is live code and the empty default is what keeps the record still.
- The fix is consistent with `prereg/W3.md`, which pins the runner's `forecast` as the tool's function "copied verbatim by AST". The clash is between two pinned designs (W3's copy rule, and amendment 4's "tools only" change to the tool), so it needed a decision whichever way it went.

### Would the dry run or Friday's run go red?

Nothing I could run says so.

- **Runner steps on the data copy with `f1f5df2`'s code:** `--restore`, seven records, watch, report, sections and `--stuck` all exit 0, with the same outputs as master's code. `fpl_sync.py` and `fpl_odds.py` were not run.
- **Imports:** the 25 root modules reachable from the workflow and `fpl_nightly.py` import nothing under `tools/` or `analysis/` and nothing outside the standard library. No test or tool file imports a third-party package. `requirements.txt`, the workflow and `fpl_nightly.py` are unchanged.
- **Time:** the suite took 324 s on master and 365 to 385 s on the branch here, with other suites running alongside. The runner's master suite took about 145 s on 12 Nov, so expect about 170 s against a 30-minute job limit.
- **Test gate:** the guard captures its child's output, so no second "Ran N tests" line reaches the run log that check 28 reads.
- **Not provable here:** the 67 new tests, the guard included, have not run on the Linux runner. I found nothing platform-specific in them; the dry run is the proof.
- **Order:** if decision 1 is yes, push `dry/S8c` only after the three tips are in. Otherwise the dry run proves a tree that will not be the one merged.

## The verifier's checks

| Check | Result | Evidence |
|---|---|---|
| Prereg before code | PASS for point 5 | pin `97ded86` before `f5cc8b3`; amendment 5 before the merge |
| 1a truncation | PASS | GW11 rebuilt from the 12 Nov export and the 17:45 UTC odds snapshot: 0 difference from the nightly's rows, under both codes. One gameweek only is recordable (see claim 4) |
| 1b timestamps | PASS | export generated 2026-11-12 17:45 UTC; newest history row GW10; last result 8 Nov; no odds snapshot after the GW11 deadline (21 Nov 11:00 UTC) |
| 1c shift probe | not applicable | no correlation metric in this item |
| 2 tests before and after | PASS | 787 OK before, 854 OK after |
| 3 re-run the measurements | PASS | claims 2, 3 and 4 reproduced exactly |
| 4 prereg matches the work | **FAIL as it stands** | `f1f5df2` has no ruling in `prereg/S8c.md`; point 5's pin says "no runner file changes". Also the pin's rule for the twelve lines is met by 11, not 12 |
| 5 recording path | PASS | all seven sources and the report byte-identical apart from `made_at` |
| 6 mutation | PASS, with one gap | point 5: 11 of 12 red. Copy fix: changing one line of the runner's `forecast` turns `Copies` red. Gap: the gate-lifting caller survives the whole suite (decision 3) |
| 7 secrets | PASS | 46 changed files scanned; the three hits are calls to a fake-key helper in `tests/test_W1.py`, on lines the landing does not change |

## How I worked

- Read-only in `C:\GIT\FPL`: `git archive`, `show`, `diff`, `log`, `reflog`, nothing that writes. `git status` is clean apart from this file. `C:\GIT\FPL-data` is byte-identical to the copy I took at the start, and `C:\GIT\FPL-b` was not touched.
- All runs on copies under `C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vfy_s8c` (scripts in `scripts`, outputs in `logs`). Data files were opened by Python with `-I`, or by the repo's own scripts with `-E -s`.
- Not done: no fetch or pull, no Linux run, no network step, no re-verification of the offline items' own results. For the three side tips I read their file lists and verdict lines, not their full reports.

VERDICT: FAIL. Every measured claim reproduces and nothing in the branch would move a recorded number or, as far as can be shown off the runner, turn a run red. But the branch is not yet the right thing to land: it leaves out the final commits of S6f, S6e2 and S8b (two test lines, two CHANGELOG entries of measured results, three reports, three verifier reports including the PASS that clears S6e2's WARN), and its one runner-file commit, `f1f5df2`, has no ruling in the prereg. Both are cheap to settle: merge the three tips and rerun the suite, and paste Boris's OK into `prereg/S8c.md`. Then a short re-check of the new head, and the dry run.

## Re-check of the new head, Thu 12 Nov night

**RE-CHECK VERDICT: PASS** for `4bbb43c`. Both reasons for the pre-check's FAIL are settled, points 1, 3, 4 and 6 are done as ruled and pinned, point 2 is on file, and every claim I was given reproduces.

- Verifier: Fable 5.2 (`claude-fable-5-2`), launched at high, not confirmable.
- `.claude/agents/backtest-verifier.md` was read from disk first. It is the same text as my loaded instructions.
- Checked: `origin/s8c-wip` = `s8c-land` = `4bbb43c`, against master `66db35e`. The remote was read with `git ls-remote` at 23:15 and 23:23 UTC: `s8c-wip` is `4bbb43c`, and there is no `dry/S8c` yet.
- Data: `C:\GIT\FPL-data` at `6f9ecb8`, read through my own copy (not pulled by me).
- Thu 12 Nov 2026, about 23:08 to 23:35 UTC. The pre-check's other findings were not redone.

### The two reasons for the pre-check's FAIL

1. **The three final commits are in.** `0b16969`, `d87f8aa` and `cfa7a36` are ancestors of `4bbb43c`. Everything the pre-check listed as missing is there: S6f's two test lines, the S6f and S6e2 CHANGELOG entries, three reports and three verifier reports (`verify_S6f.md` PASS, `verify_S6e2_a1.md` PASS, `verify_S8b.md` PASS).
2. **The ruling for `f1f5df2` is on file.** `prereg/S8c.md` on master holds point 2 verbatim ("Boris's OK for f1f5df2 ..."), committed in `88c77df` before the three merges. The same 3,608-character ruling block is identical in all six prereg files that carry it.

### The six points

| Point | Ruled | Found |
|---|---|---|
| 1 | Bring the three tips in; the full suite; a short re-check before the dry run | Done: three merges, suite green four ways (below), this re-check; no `dry/S8c` on the remote yet |
| 2 | Boris's OK, verbatim in `prereg/S8c.md` before the merge | On file: `88c77df` at 22:49:09 UTC, the first merge at 22:49:55 UTC |
| 3 | A W3 test on the toy: a status 'd' player gets no xp_v2 from the runner's record (tests only) | Done as pinned; red under four of my five mutations (below) |
| 4 | `ChecksMain.setUp` checks its commit's exit code, so the guard covers the twelfth line | Done; 12 of 12 lines now turn the guard red. The pin's wording differs in one word (note 1) |
| 5 | Mode (d) covers master and `dry/*` | A rule, not work. It is in `prereg/S8c.md` and the report's notes; `CLAUDE.md` is unchanged (decision 2) |
| 6 | CHANGELOG entry and report for point 5 and the copy fix, docs only; the duplicate W2 entry left and noted | Done: `4bbb43c` changes `CHANGELOG.md` and adds the report, nothing else; the duplicate is still entries 80 and 95, and the report notes it |

- **Prereg before code:** the pin `88c77df` (22:49:09 UTC, master) precedes the merges (22:49:55 to 22:50:20 UTC), the tests `4245b80` (22:51:29 UTC) and the docs `4bbb43c` (23:08:04 UTC). The gaps are seconds to minutes, so the work was prepared before the pin was committed; git order is what the rule asks, as in the pre-check.
- `4245b80` changes three test files only. `4bbb43c` changes two docs files only.

### The three merges

| Merge | Tip | Files that arrive (each byte-identical to the tip) | CHANGELOG entries |
|---|---|---|---|
| `ad34c9b` | `origin/s6f-wip` `0b16969` | `tests/test_S6f.py` (+2 lines), `cc_2026-10-19_S6f.md`, `verify_S6f.md` | 115 + 1 = 116 |
| `3405e94` | `origin/s6e2-wip` `d87f8aa` | `cc_2026-10-19_S6e2.md`, `verify_S6e2_a1.md` | 116 + 1 = 117 |
| `f917dd1` | `origin/s8b-wip` `cfa7a36` | `cc_2026-10-20_S8b.md`, `verify_S8b.md` | 117; the tip's one entry was already there, identical |

- **Each merge against its first parent** changes only the files in the table, plus `CHANGELOG.md` for the first two. `CHANGELOG.md` was the only file changed on both sides of any of the three.
- **Tools:** no file under `tools/` changes in any merge, nor between `f1f5df2` and `4bbb43c`.
- **CHANGELOG, entry by entry** (separators aside):
  - Each merge is exactly the union of its two parents. No entry is lost from either side, none is in the merge that is in neither parent, no entry's text changes, each side's order is kept, and there are no conflict markers.
  - 117 entries at `f917dd1` and `4245b80`, as claimed: 116 distinct, the one repeat being the W2 amendment 2 entry (80 and 95), which master already holds.
  - `4bbb43c` adds its own entry, so the head holds 118.
  - `f1f5df2` to `4bbb43c` is one hunk at the end of the file: 74 lines added, none removed or changed. The two arriving entries sit at the end (116 and 117), after the W3 entry of 12 Nov, although they are dated 19 and 20 Oct.
- **The two S6f test lines work.** Three changes to the tool's per-gameweek columns (diff, own_proxy, v2-prx) each turn `tests.test_S6f` red; with the test file as it was on `f1f5df2`, the v2-prx change stayed green.
- **A local amend, for the record:** the reflog shows the third merge was first made as `c8b6593` and amended 23 seconds later to `f917dd1`. The amend removes two stray separator blocks from `CHANGELOG.md` (6 lines), which is why this merge changes no CHANGELOG line. `f1f5df2` is an ancestor of `4bbb43c`, so the branch moved forward only.

### The two new tests and their mutations

All on scratch copies of `4bbb43c`. The unchanged copy is green: `tests.test_W3` 31 tests, `tests.test_S8c_p5` 2 tests.

**Point 3, `tests.test_W3.StatusGateInTheRecord`.**

- It is as pinned. It records xp_v2 through `fpl_edge.record_status` (the runner's record) on the W3 toy, takes the first of our 15 that has a row at status 'a', sets him to status 'd' with chance 50, and records again. He has no row, and every other row is unchanged (30 rows become 29).
- It uses the same helpers and the same call as the existing `Forecast` class, which already runs in the nightly.

| Mutation in `fpl_xpv2.py` | `tests.test_W3` | Red tests |
|---|---|---|
| `live_forecast` lifts the gate for every player (the pre-check's probe; the claim) | red | `StatusGateInTheRecord` |
| `live_forecast` lifts it for status 'd' players only | red | `StatusGateInTheRecord` |
| `forecast`: the gate lets 'a' or 'd' through | red | `StatusGateInTheRecord`, `Copies` |
| `forecast`: the gate lets anyone with chance 50 or more through | red | `StatusGateInTheRecord`, `Copies` |
| `live_forecast` lifts it only for 'd' players with chance 75 or more | **green** | none |

- The first row is the claim, and it holds: red at `assertNotIn`, with the flagged player (id 1) in the record.
- The survivor is contrived and needs no action: the pin fixes the toy player's chance at 50, so a lift that starts above 50 is not seen. I report it so the test's reach is known.

**Point 4, `ChecksMain.setUp` and the guard.**

| Change | Run | Result |
|---|---|---|
| ChecksMain's `commit.gpgsign false` line left out (the claim) | the guard | **red**: `setUp` stops at line 579, "gpg failed to sign the data" |
| The same, with the exit-code check also removed (the old helper) | the guard | green: the gap the pre-check found |
| The line left out, the check kept, ChecksMain's entry removed from the guard's sites | the guard | green: the new entry is needed |
| The line left out | `tests.test_S3.ChecksMain`, no signing config | green: the line matters only under signing |
| The line left out | `tests.test_S3.ChecksMain`, `GIT_CONFIG_GLOBAL` with `gpgsign = true` | red, all 3 tests |

All twelve lines again, since the guard file changed (each left out in turn, then the guard):

| Line left out | Guard | The test that went red inside it |
|---|---|---|
| `test_fpl.py` NightlyRunner `_data_repo` | red | NightlyRunner restore test |
| `test_fpl.py` DataGate.setUp | red | DataGate changed-frozen-forecast test |
| `test_fpl.py` Publish._ident | red | Publish dry-run-on-master test |
| `test_fpl.py` PrePush.setUp | red | PrePush code-push test |
| `tests/test_S3.py` ChecksMain.setUp | **red** (was green) | ChecksMain real-run test |
| `tests/test_S3.py` PublishOnAFail seed | red | PublishOnAFail dry-run test |
| `tests/test_S3.py` PublishOnAFail run clone | red | the same test |
| `tests/test_W1.py` OddsAppendOnly.setUp | red | OddsAppendOnly deleted-file test |
| `tests/test_W1.py` OddsNeverCostsTheNight seed | red | crashing-collector test |
| `tests/test_W1.py` OddsNeverCostsTheNight data clone | red | the same test |
| `tests/test_W1b.py` DueGate.setUp | red | DueGate manual-dry-run test |
| `tests/test_W1b.py` Hook.setUp | red | Hook dry-pushes test |

12 of 12, each red at the intended site's own test and no other. The guard now names ten sites for the twelve lines (two sites hold two lines each).

### The suites

All by discovery on `git archive` copies of `4bbb43c`: `python -E -s -B -m unittest discover -v -p "test*.py"`, `ODDS_API_KEY` unset. `4bbb43c` differs from `4245b80`, the commit the claim names, in the two docs files only.

| Tree | Setting | Ran | Result | Skipped | Claimed |
|---|---|---|---|---|---|
| `4bbb43c` | plain | 855 | OK | 11 | 855 OK, 11 skipped |
| `4bbb43c` | signing on (`GIT_CONFIG_GLOBAL` file with `[commit] gpgsign = true`; git confirmed it read `true`) | 855 | OK | 11 | 855 OK, 11 skipped |
| `4bbb43c` | `FPL_DATA_DIR` = my data copy, after `--restore` | 855 | OK | 4 | 855 OK, 4 skipped |
| `4bbb43c` plus master's 13 newer files (the tree the merge would give) | plain | 855 | OK | 11 | not claimed |

- **Test ids:** all 854 ids of `f1f5df2` are still there. The one new id is `tests.test_W3.StatusGateInTheRecord.test_a_d_player_gets_no_xp_v2_row`. Point 4 adds a site to an existing test, not a test.
- **The data run** changed nothing in my data copy (same hash of its 247 files before and after the suite). `--restore` had replaced one working export, `fpl_export_gw10.json`, in the copy only.
- **The merged tree:** since the merge base `99c9161`, master and the branch have changed no file in common, so the merge has no conflict. Master's 13 files are prereg, worklog and `BUILD_PLAN.md`; none is a runner, tool or test file.
- **Time:** 372 to 386 s each here, two suites at a time.

### The report and the CHANGELOG entry against the facts

Every figure in `worklog/cc_2026-11-13_S8c_landing.md` and in the entry "S8c landing, ready on `s8c-wip`" that I could check is right.

- 117 entries after the merges; ten sites; 855 OK in all three settings; 12 of 12; the status-gate test red with the gate lifted.
- The three verifier files' verdicts are as the report says.
- The duplicate W2 entry is at 80 and 95.
- Outside `tools/`, `tests/`, `test_fpl.py`, `prereg/`, `worklog/` and `CHANGELOG.md` the branch changes only `fpl_xpv2.py`. The pre-check's remark on claim 1 (`test_fpl.py` left out of the wording) is fixed in the report.
- The commits the entry's heading names exist and are what it says.
- The older figures (787 on master, 852 and 69 before, the 299 rows) are the pre-check's and were not re-run.
- Both say the re-check is "to follow". That was true when written (decision 1).

Three small things, none wrong enough to change the verdict:

1. **The pin says `check=True`; the code asserts on the return code.** `prereg/S8c.md` pins point 4 as "checks its commit's exit code (`check=True`)". The code is `self.assertEqual(r.returncode, 0, r.stdout)`. The effect the pin names is the same (a failed commit stops the test), it is what Boris's ruling asks, and the failure message carries git's output. The report does not mention the difference.
2. **The head holds 118 entries, not 117.** The report's "117 entries" is the count after the merges, before its own entry. Correct as placed; only worth knowing when counting on the head.
3. **The entry is dated 2026-11-12 and the report file 2026-11-13.** The commit was made at 23:08 UTC on 12 Nov, 00:08 on 13 Nov in Prague. Both are true.

### Nothing else changed since `f1f5df2`, and the dry run

- **Twelve files differ** between `f1f5df2` and `4bbb43c`: `CHANGELOG.md`, four test files (`test_S3`, `test_S6f`, `test_S8c_p5`, `test_W3`) and seven worklog files. No runner file, no tool, no workflow, no `requirements.txt`, no prior file.
- **So the pre-check's runner findings carry over unchanged:** the record and the report byte-identical to master's, the import trace, and the runner steps on the data copy. I did not redo them.
- **`ChecksMain` with an empty home:** the existing `tests.test_S3.Hermetic` test runs `ChecksMain` in a child with an empty home and no global config, and it passes with the new exit-code check. That is the nearest thing here to the Linux runner.
- **Not provable here, as before:** the 68 tests the branch adds over master have not run on the Linux runner. I found nothing platform-specific in the new one. The dry run is the proof.
- **When to push `dry/S8c`:** at 23:23 UTC the remote `data` head was still `6f9ecb8`, committed at 17:46 UTC. The scheduled run of 12 Nov (21:40 UTC) had not committed. The three data commits before it were made at 03:49 (10 Nov), 01:29 (11 Nov) and 02:32 UTC (12 Nov), so a commit several hours after 21:40 is usual. A `dry/S8c` pushed before tonight's commit is skipped green and proves nothing, so check `data` first, as the pin says.
- **Secrets:** the 12 changed files were scanned. One hit, a `grep` pattern quoted in `verify_S6e2_a1.md` ("apik..." inside a regular expression); it is not a key.

### The verifier's checks

| Check | Result | Evidence |
|---|---|---|
| Prereg before code | PASS | `88c77df` before `ad34c9b`, `4245b80` and `4bbb43c` in git |
| 1 point-in-time | carried over | no forecast code changed since `f1f5df2`; the pre-check's 1a and 1b stand |
| 2 tests before and after | PASS | 854 OK on `f1f5df2`; 855 OK on `4bbb43c`, four ways |
| 3 re-run the measurements | PASS | the three claimed suites and both claimed mutations reproduce exactly |
| 4 prereg matches the work | PASS | points 1, 3, 4, 6 as pinned; point 2 on file; one word of the pin differs (note 1) |
| 5 recording path | carried over | no runner file changed since `f1f5df2` |
| 6 mutation | PASS | 12 of 12 lines red; the gate test red under four of five mutations; S6f's two lines red under three |
| 7 secrets | PASS | 12 files, no key |

### Decisions for the chat

1. **No further commit on `s8c-wip` before the dry run?** The branch's report and CHANGELOG entry say the re-check is "to follow". I recommend leaving them and recording this verdict in the "S8c done" entry after the landing. Then `dry/S8c` is `4bbb43c`, the commit this re-check covers. A docs commit first would be harmless but moves the head past what was checked.
2. **Mode (d) in `CLAUDE.md`.** Point 5 (the window covers master and `dry/*`; other work branches at any time) is in `prereg/S8c.md` only. A fresh session reads `CLAUDE.md`, whose mode (d) still names no branch. Add the ruling's sentence there? Docs only, on Boris's word.
3. **`check=True` in the pin against `assertEqual` in the code** (note 1). I count the pin as met. Say so if the literal form is wanted.

### How I worked

- Read-only in `C:\GIT\FPL`: `git archive`, `show`, `diff`, `log`, `reflog`, `merge-base` and `ls-remote`, nothing that writes; no fetch. `git status` is clean apart from this file.
- `C:\GIT\FPL-data` has the same hash over its 247 files at the end as at the start. `C:\GIT\FPL-b` was not touched.
- All runs on copies under `C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vfy_s8c2` (scripts in `scripts`, outputs in `logs`, mutations in `mut`). Data files were opened by Python with `-I`, or by the repo's own scripts with `-E -s`.
- Not done: no Linux run, no workflow run, none of the pre-check's record and report comparisons again, and no reading of the three items' reports beyond their verdict lines.

VERDICT: PASS. The new head `4bbb43c` settles both reasons for the pre-check's FAIL: the final commits of S6f, S6e2 and S8b are merged in with nothing lost or duplicated (the CHANGELOG is the exact union, 117 entries, 118 with the landing's own), and Boris's OK for `f1f5df2` is verbatim in `prereg/S8c.md` before the merges. The two new pieces of test work do what was ruled: the status-gate test goes red when the runner's record lifts the gate, and with `ChecksMain.setUp` checking its commit all twelve signing lines are guarded. The suite is 855 OK plain, with signing on, with the data, and on the tree the merge would give. Nothing but tests, docs and worklog files changed since `f1f5df2`, so the pre-check's findings on the record and the runner path stand. What is left is not provable here: the Linux run, which the dry run gives, and it should be pushed only after tonight's nightly has committed.
