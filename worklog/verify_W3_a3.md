# Verifier report: W3 amendment 3 (delta `ee3f75c..43a174f` on `w3-wip`)

Model: Fable 5.1 (claude-fable-5-1), effort high, as `.claude/agents/backtest-verifier.md`
(read from disk first; it matched the loaded instructions). Verified 2026-11-03.

Scope: the one commit `43a174f` over `ee3f75c` (w3-wip with master merged). All building,
mutating and test runs were done on copies made with `git archive` under the session
scratchpad (`...\scratchpad\vfy_w3a3\`); nothing was changed in this worktree,
`C:\GIT\FPL`, `C:\GIT\FPL-b` or `C:\GIT\FPL-data` (`git status` clean in the worktree and
in the data worktree after the run). Only this file was written here.

## Prereg before code

- `prereg/W3.md` section "Amendment 3, Tue 3 Nov night (Boris's message verbatim)" is on
  master as `0be8309`, committer time 2026-11-03T22:42:58+01:00; it is an ancestor of
  `43a174f` (committer time 2026-11-03T22:51:34+01:00), via the merge `ee3f75c`
  (22:43:07+01:00). `git diff 0be8309 43a174f -- prereg/W3.md` is empty: the text the item
  built on is the committed text. PASS.
- Boris's three rulings are in the file verbatim ("Rulings, Tue 3 Nov night. 1. ... 2. ... 3.
  ..."); what W3 takes from them is pinned under it (point 1 test only; point 2 is
  `prereg/runcommit.md`, nothing on w3-wip; point 3 no code, one assertion; the two open
  items from `worklog/verify_W3_a2.md`: the +02:00 test and the `fetch-depth` comment).

## Q1. Tests and one comment only?

`git diff --stat ee3f75c 43a174f`: 4 files, +46/-1:
`.github/workflows/nightly.yml` (1 line), `tests/test_W2.py` (+17), `tests/test_W2fix.py`
(+16), `tests/test_W3.py` (+12). `diff -rq` of the two `git archive` trees lists the same 4
files and no other. The `nightly.yml` change is inside a `#` comment line (shown with
`cat -A`: `      # the deadline (W3 amendment 2)$`). No executable line moved in any
`.py` or in the workflow. `git diff --check` clean. **PASS: tests and a comment only.**

Consequence for the file's checks:
- Check 1 (point-in-time leak) does not apply: the delta produces no forecast, feature or
  metric and changes no executable line. The +02:00 test is itself a timestamp-audit probe
  of amendment 2's code and passes (below).
- Check 3 (re-run the pre-registered evaluation) does not apply: the prereg amendment has
  no metric; the acceptance is the tests listed under "What W3 takes from it".
- Check 5 (recording path): no executable line moved, so the projection log cannot have
  moved; no recompute needed. The two trees' `.py` files are byte-identical outside
  `tests/`. PASS by construction.

## Q2. Each test exercises its prereg line; red for the right reason

Read for myself: `tools/league.py` `load` (l.130-160) and `check_multipliers` (l.210-222);
`fpl_league.py` `load` (l.102-132) and `check_multipliers` (l.182-194), the same text in
both; `fpl_squad.py` `_utc` (l.231) and `bundle_csv` (l.235-262); `fpl_chips.py:274` and
`tools/chips.py:317`.

**(a) A captain with really no `player_gw` row** (`tests/test_W2fix.py::test_captain_with_no_player_gw_row_counts_as_0_minutes`).
`vice_case(tmp, cap_minutes=())` inserts no `player_gw` row for the captain (id 10, GW4); the
test first asserts `count(*) = 0` for that player and event, so the case is "no row", not a
row of 0. `load` builds `minutes = defaultdict(int)` from `player_gw`, and
`check_multipliers` uses `minutes.get((caps[0], ev), 0) == 0` (the `.get` default, not the
defaultdict factory, is what decides for a missing key). The vice at x2 loads in both
modules (`run_case` loops `fpl_league` and `tools/league`); at x1 both stop with
"entry 1003 GW4 player 17: multiplier 1 but the rule says 2". Matches the pinned text.

**(b) A +02:00 committer date read as its instant** (`tests/test_W3.py::BundleGrading::test_a_committer_date_at_plus_02_00_is_read_as_its_instant`).
`git_commit` sets `GIT_COMMITTER_DATE=2026-10-23T19:29:59+02:00`; `bundle_csv` reads
`git log --format=%H %cI` and `_utc` parses the offset-aware ISO string with
`fromisoformat`; GW8's deadline in `toy_realised` is 2026-10-23T17:30:00+00:00. 19:29:59+02:00
= 17:29:59Z < deadline: graded, label `source: GW8 bundle <h[:7]>`. A second commit with
different values at 19:30:00+02:00 = 17:30:00Z hits `>= deadline` and is skipped: the
earlier commit's values and label still hold. Matches the pinned text (a second before
graded, the deadline itself not).

**(c) The CHIPS first line names the dated export, both modules**
(`tests/test_W2.py::ReportSections::test_the_chips_section_names_the_export_and_its_date`).
Runs `tools.chips.live` and `fpl_chips.live` on `toy_data` + `toy_export` (one export,
`exports/fpl_export_gw7_2026-10-18.json.gz`) and asserts `lines[0]` matches
`^CHIP CALCULATOR  export fpl_export_gw\d+_\d{4}-\d{2}-\d{2}\.json\.gz `. Both modules print
`os.path.basename(path)` of `newest_export(data_dir)`. Matches the pinned "one assertion
to hold it".

**My own mutations** (`scratchpad\vfy_w3a3\my_mut.py`, each on a fresh copy of `43a174f`,
ODDS_API_KEY and FPL_DATA_DIR unset; the implementer's 6 in `mut_w3a3.py` were not relied on):

| # | Mutation | Result | Which test, why |
|---|---|---|---|
| V1 | `tools/league.py`: `minutes.get(..., 0)` -> `.get(..., 1)` | RED | only the new no-row test (FAIL: vice x2 raised "rule says 1"); the three older W2fix tests stay green, so this test is the one that holds the no-row case |
| V2 | same in `fpl_league.py` | RED | same |
| V3 | `tools/league.py`: promote only when a row exists (`(caps[0], ev) in minutes and ...`) | RED | new no-row test |
| V4 | same in `fpl_league.py` | RED | new no-row test |
| V5 | `fpl_squad._utc`: `.replace(tzinfo=timezone.utc)` (wall clock as UTC; the prereg's mutation) | RED | only the new +02:00 test (ERROR: `g8["xp_v2"]` missing, i.e. "not recorded": 19:29:59 read as UTC is after 17:30Z). The 8 older BundleGrading tests all use +00:00 and stay green, which is exactly the gap the a2 verifier reported |
| V6 | `_utc`: offset dropped (`text[:19]`, labelled UTC) | RED | new +02:00 test, same reason |
| V7 | `bundle_csv`: `>= deadline` -> `> deadline` | RED | new +02:00 test (AssertionError 47.0 != 52.0: the deadline commit's values taken) and the older `test_only_at_or_after_the_deadline_is_not_recorded` |
| V8 | `fpl_chips.py`: header `export latest` | RED | new CHIPS test and `test_byte_identical_to_the_tools` |
| V9 | `tools/chips.py`: same | RED | same two |
| V11 | `fpl_chips.py`: date dropped from the name | RED | new CHIPS test and byte-identical |
| V10 | `fpl_chips.py`: a well-formed but WRONG name `fpl_export_gw1_2000-01-01.json.gz` | RED, but only via `test_byte_identical_to_the_tools` | the new regex test stays green |
| V10b | V10 applied to BOTH modules | **GREEN** (ReportSections 6/6 OK) | nothing in the suite holds that the name printed is the export actually read |

All 6 of the implementer's mutations correspond to V1, V2, V5, V7, V8, V9 and are red here
too. Each new test fails for its own reason (vice not promoted; the +02:00 instant
misread; the export name missing), and the older tests do not cover V1-V6. **PASS**, with
the V10b finding recorded under Q8 (non-blocking; see there).

## Q3. Hermetic under CLAUDE.md (S3 amendment 1)

The three new tests run on a `git archive` copy, unset ODDS_API_KEY/FPL_DATA_DIR:
- TZ = `JST-9`, `PST8PDT`, `UTC0`, `NZST-12NZDT`, `EST5EDT`: 3/3 OK each. The +02:00 test
  compares aware datetimes throughout, and `%cI` carries git's stored offset, so the
  machine zone cannot enter.
- `HOME`/`USERPROFILE` = empty folder, `GIT_CONFIG_GLOBAL` = nonexistent file,
  `GIT_CONFIG_NOSYSTEM=1`, `LC_ALL=C`, `LANG=C`: 3/3 OK (identity and `core.autocrlf` are
  given per command in `git_commit`).
- `PYTHONUTF8=0`: 3/3 OK.
- Files: `test_W2fix` and `test_W2` build everything in `tempfile.mkdtemp()`; `test_W3`
  passes `repo=self.repo` (a temp git repo) to `realised`, so the real repository is not
  read. `tools/chips.py` only defaults `--data` to `..\FPL-data` for its CLI; `live(a, ...)`
  is called with the temp folder. No file outside the temp folders is read.
- Hostile global config probe: `[commit] gpgsign = true` makes `git_commit` fail (exit 128,
  no signing key) and the +02:00 test ERRORs; `core.autocrlf=true`, `init.defaultBranch`,
  `log.date=local`, `core.hooksPath` each OK. This is the amendment-2 helper (`git_commit`,
  shared by all 9 BundleGrading tests), not this delta; `tests/test_S3.py` l.1028 already
  isolates HOME/GIT_CONFIG_GLOBAL for its git runs, so the suite has the pattern. This
  machine's global config has no `gpgsign` (keys: filter.lfs.*, user.name, user.email).
**PASS** for the delta; the inherited `gpgsign` exposure is a recommendation under Q8.

## Q4. Ruling point 3: does the real report name the export's date?

`C:\GIT\FPL-data\reports\fpl_2026-11-03.txt` line 507 (data `39578fe`, "nightly 2026-11-03",
committed 2026-11-03T20:17:19Z):
`CHIP CALCULATOR  export fpl_export_gw9_2026-11-02.json.gz (GW9 played), next GW10, chips left: BB, FH; budget £99.8m = bank + selling prices`.
It names the dated archive it read (the previous night's, as the ruling accepts). The code
that prints it (`os.path.basename(path)` at `fpl_chips.py:274` and `tools/chips.py:317`)
predates the delta and is unchanged. **"No code needed" is right. PASS.**

## Q5. `nightly.yml`

The only change is the comment on the `fetch-depth: 0` checkout: "(W3 amendment 1, (C))" ->
"(W3 amendment 2)". A comment only (the line starts with `#`; the `uses:` SHA and
`fetch-depth: 0` are untouched). The citation is correct: amendment 2 replaced amendment
1 (C)'s grading rule and says "Kept: `fetch-depth: 0` on the nightly's master checkout",
and its rule is "walk the commits touching that file, newest first ... committer time
strictly before GW8's `events.deadline_time`", which the comment's "at its last commit
before the deadline" describes (the `run.txt` condition is elided, acceptably for a
comment). **PASS.**

## Q6. Clean-checkout suite counts (check 2)

`python -m unittest discover -p "test*.py"` on the `git archive` trees, ODDS_API_KEY unset:

| Tree | bare | with `FPL_DATA_DIR=C:\GIT\FPL-data` |
|---|---|---|
| `ee3f75c` (before) | Ran 784, OK (skipped=11), 318 s | Ran 784, OK (skipped=4), 326 s |
| `43a174f` (after) | Ran 787, OK (skipped=11), 326 s | Ran 787, OK (skipped=4), 325 s |

Matches the implementer's 784 -> 787, 11 and 4 skipped. The three new tests are discovered
(+3). **PASS.**

## Q7. Secrets (check 7)

The added lines of the delta (`git diff ee3f75c 43a174f | grep '^+'`) contain no `apiKey=`,
no `Authorization`/`Bearer`, no 32+ character key-like token. In the four changed files the
only hit is the pre-existing comment in `nightly.yml` line 24 describing the secret scan
itself ("looks for "apiKey=" always"), not a value and not part of the delta. **PASS.**

## Q8. Anything else

Nothing in the delta is outside what the prereg called for: no `runcommit` work on w3-wip,
no change to `fpl_chips.py`/`tools/chips.py`, no edit to frozen files. Two non-blocking
findings for the chat:

1. **The CHIPS assertion holds the shape, not the identity, of the export named.** With
   both modules printing a well-formed wrong name, the suite is green (V10b). The prereg's
   pinned words ("one assertion to hold it", i.e. the line that names the export) are met
   and the live code prints the basename of the very path it loads, so the risk is a future
   regression, not a present defect. A stronger one-liner: assert the line starts with
   `CHIP CALCULATOR  export fpl_export_gw7_2026-10-18.json.gz ` (the toy's only export).
   Not a condition of the verdict; not something to change on this item without a ruling.
2. **`git_commit` in `tests/test_W3.py` relies on the global git config not setting
   `commit.gpgsign=true`** (amendment 2's helper; all 9 BundleGrading tests, the new one
   included). Adding `-c commit.gpgsign=false` (or the `test_S3` isolation env) would close
   it. Pre-existing, not introduced here.

## Checks of the agent file, summarised

| Check | Result |
|---|---|
| Prereg before code | PASS (`0be8309` < `43a174f`, ancestor; text identical) |
| 1 Point-in-time | N/A: no forecast, feature or metric; no executable line moved |
| 2 Clean-checkout counts | PASS: 784 -> 787 OK, bare (11 skipped) and with data (4 skipped) |
| 3 Re-run the evaluation | N/A: no metric in the amendment; acceptance tests verified in Q2 |
| 4 Prereg metric/threshold | N/A for a metric; the ruling is verbatim in the prereg; the delta does what is pinned and nothing more |
| 5 Recording path | PASS by construction: no executable line changed |
| 6 Mutation spot-check | PASS: 10 of my 11 mutations red on the intended test; V10b green is a test-strength note |
| 7 Secrets | PASS |

**VERDICT: PASS.** The delta is exactly what the pinned amendment calls for and nothing
else: three tests and one comment, committed after the verbatim prereg `0be8309`, with no
executable line moved (so the recording path and point-in-time checks cannot have moved).
Each new test exercises its ruling line on the real code paths (a genuinely absent
`player_gw` row promotes the vice in both league modules; a +02:00 committer date is
compared as its instant with the second-before/at-deadline boundary; the CHIPS first line
names the dated archive in both modules), and each goes red for its own reason under my
mutations, which the older tests do not catch. The tests pass under five other time zones,
with no git config, and in the C locale; the suite goes 784 -> 787 OK on clean copies, bare
and with the data; the real 3 Nov report already names the export's date so "no code
needed" holds; the `nightly.yml` edit is a comment that now cites the right amendment; no
secrets. Two non-blocking recommendations are recorded: the CHIPS regex does not pin the
name to the export actually read, and the inherited `git_commit` helper is exposed to a
global `commit.gpgsign=true`.

---

# Follow-up: the two recommendations (delta `784919f..aa07818`, w3-wip head)

Model: Fable 5.1 (claude-fable-5-1), effort high. `.claude/agents/backtest-verifier.md`
re-read from disk first; unchanged. The first verdict above stands as written. Same rule:
only this file written in this worktree; all building, mutating and runs on fresh
`git archive` copies under `...\scratchpad\vfy_w3a3\` (`head`, `base784`, `head_mut`,
`head_gpg`); `C:\GIT\FPL`, `C:\GIT\FPL-b` and `C:\GIT\FPL-data` untouched.

## Prereg note before the code

Master `16aa4ed` (committer 2026-11-03T23:05:18+01:00) appends 14 lines to `prereg/W3.md`,
"Added after the verifier's report on `43a174f`, before the follow-up", and nothing else
(`git diff --stat 16aa4ed~1 16aa4ed`: 1 file, +14). The merge `784919f` (23:05:22+01:00)
brings it to w3-wip; the follow-up commit `aa07818` (23:06:03+01:00) is after it and
`16aa4ed` is its ancestor. The tree at `784919f` differs from `43a174f` only in
`prereg/W3.md` (verified with `diff -rq`). PASS.

One wording slip in the note, which I own: it says a global `commit.gpgsign = true`
"stopped all 9 `BundleGrading` tests", carrying my own phrase from Q3 above. The measured
count is 8 of 9 (below); the ninth, `test_the_nightly_checks_out_the_history`, makes no
commit. The implementer's commit message has the right count. A note's wording, not a
condition of anything.

## 1. Tests only?

`git diff --stat 784919f HEAD`: `tests/test_W2.py` (+2/-2), `tests/test_W3.py` (+1/-1); no
other file; `git diff --check` clean; `diff -rq` of the `784919f` and HEAD trees lists the
same two files only. The changes: the unused `import re` dropped and the `assertRegex`
replaced by `assertTrue(lines[0].startswith("CHIP CALCULATOR  export
fpl_export_gw7_2026-10-18.json.gz "), lines[0])`; `git_commit`'s `base` gains
`"-c", "commit.gpgsign=false"`. No executable non-test line moved, so checks 1, 3 and 5 of
the agent file do not apply here either (no forecast, feature or metric; the recording path
cannot have moved). **PASS.**

## 2. V10b now red? (my own mutations, `my_mut2.py`, fresh copies of HEAD)

| # | Mutation | Result | Which test |
|---|---|---|---|
| F1 | both chips modules print the well-formed WRONG name `fpl_export_gw1_2000-01-01.json.gz` (my V10b) | **RED** | the CHIPS test itself: `AssertionError: False is not true : CHIP CALCULATOR  export fpl_export_gw1_2000-01-01.json.gz (GW7 played), ...` (byte-identical stays green, as both modules agree) |
| F2 | both: right gw, the date one day off (`2026-10-19`) | RED | CHIPS test |
| F3 | both: the date dropped (`fpl_export_gw7.json.gz`) | RED | CHIPS test |
| F4 | `fpl_chips.py` only: wrong name | RED | CHIPS test and byte-identical |
| F5 | `tools/chips.py` only: wrong name | RED | CHIPS test and byte-identical |

The new assertion holds the identity of the export named, in both modules, and fails with
the offending line in the message. **PASS.**

## 3. Hermetic, and tied only to the toy

The name asserted, `fpl_export_gw7_2026-10-18.json.gz`, is the one file `toy_export`
writes (`tests/test_S7.py` l.89, under `tmp/exports/`; `grep -c json.gz` = 1), into the
test's own `tempfile.mkdtemp()`; `live(a, ...)` reads only that folder. Nothing from
`C:\GIT\FPL-data` or the repo enters. The two changed tests pass under TZ `JST-9`, `PST8PDT`,
`UTC0`; with empty HOME/USERPROFILE, a nonexistent `GIT_CONFIG_GLOBAL`,
`GIT_CONFIG_NOSYSTEM=1`, `LC_ALL=C`, `PYTHONUTF8=0`; and under my hostile global config
(gpgsign + autocrlf=true + defaultBranch + log.date=local + hooksPath), which broke the
+02:00 test before. **PASS.**

## 4. `GIT_CONFIG_GLOBAL` with `commit.gpgsign = true`: BundleGrading

`python -m unittest -v tests.test_W3.BundleGrading`, `GIT_CONFIG_NOSYSTEM=1`, ODDS_API_KEY
and FPL_DATA_DIR unset:

| Tree | Result |
|---|---|
| `784919f` (before) | Ran 9, FAILED (errors=8); the one `ok` is `test_the_nightly_checks_out_the_history`, which only reads `nightly.yml` and makes no commit |
| HEAD `aa07818` | Ran 9, OK |

The implementer's "8 of 9 before, the ninth commits nothing, all 9 after" is exactly
what I measure. **PASS.**

## 5. The same exposure elsewhere in the suite (information only, outside this delta)

Full discovery at HEAD on a fresh copy under the same `gpgsign = true` global config:
`Ran 787, FAILED (failures=9, errors=59, skipped=10)`, exit 1. The 68 failing tests by
class: `test_fpl.DataGate` 28, `test_fpl.Publish` 11, `test_fpl.PrePush` 6,
`test_fpl.NightlyRunner` 2, `tests.test_W1b` 13, `tests.test_S3` 4, `tests.test_W1` 4;
none in `BundleGrading`. (`tests/test_S3.py` l.1028 isolates HOME/GIT_CONFIG_GLOBAL for
one of its runs; the other `git commit` call sites in those files pass `-c
core.autocrlf=false` or nothing.) Not a condition of this verdict; recorded for the chat as
the suite-wide count of tests that rely on the global git config not setting
`commit.gpgsign`. (The skipped count 10, not 11, is one data-less skip that turned into an
error under the hostile config; same 787 discovered.)

## 6. Suite counts at HEAD (clean `git archive` copies, ODDS_API_KEY unset)

| | bare | with `FPL_DATA_DIR=C:\GIT\FPL-data` |
|---|---|---|
| HEAD `aa07818` | Ran 787, OK (skipped=11), 302 s | Ran 787, OK (skipped=4), 305 s |

Unchanged from `43a174f` (787/787), as expected for two edited tests. **PASS.**

## 7. Secrets on the delta

Added lines of `git diff 784919f HEAD`: no `apiKey=`, `Authorization`/`Bearer` or
32+-character token. **PASS.**

**VERDICT (follow-up): PASS.** The delta is the two recommended test changes and nothing
else, committed after the prereg note `16aa4ed` that pinned them; no executable line moved.
The CHIPS assertion now holds the identity of the export named (my V10b and four further
header mutations go red on that test, in both modules) and it is tied only to the toy's
one file in a temporary folder; `git_commit` with `-c commit.gpgsign=false` turns
BundleGrading from 8 errors of 9 to 9 OK under a global `commit.gpgsign = true`, matching
the implementer's count (the prereg note's "all 9" is a wording slip traceable to my own
Q3 phrase). The suite stays at 787 OK bare and with the data; no secrets. The 68 other
tests in the suite that still depend on the global git config are reported as information,
outside this delta.
