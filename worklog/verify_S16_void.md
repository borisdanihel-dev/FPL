# Verifier report: S16 part 1 amendment, the void round (2022-23 GW7)

- Verifier: `backtest-verifier`, model Fable 5.1 (`claude-fable-5-1`), effort high as `.claude/agents/backtest-verifier.md` states (read from disk first; it governs). 19 Oct 2026.
- Item: RULING lane A open points 19 Oct, point 1; the delta only. Descriptive: checks 2, 5, 6, 7 and the amendment's acceptance tests (`prereg/S16.md`, section "Part 1 amendment: the void round").
- Code: branch `s16-wip`, single commit `14a8da5` (2026-10-19 11:58:58 +0200), parent `4d3e9b5` (master, 11:32:35). `git diff --name-status 4d3e9b5 14a8da5`: `M tools/blank_double.py` (+28/-5), `M tests/test_S16_part1.py` (+15), nothing else. `git ls-remote origin`: `master` = `4d3e9b5`, `s16-wip` = `14a8da5`, both equal to the local refs.
- Written: this file only. `git status` in `C:\GIT\FPL` before and after: only the pre-existing untracked `worklog/verify_S2b_pre.md` and `verify_W1b_pre.md`; `git for-each-ref` before and after identical (32 refs); `C:\GIT\FPL-data` clean at `9da6ff1` before and after; `C:\GIT\FPL-b` not touched (HEAD `841c4bc`, not entered beyond `git status`); every file under `historical/` has the same SHA-256, size and mtime before and after (15 files, `vv/hist_before.txt` = `vv/hist_after.txt`). No fetch, push, ref, tag, hook or config change; no dispatch, API or download. All work under the scratchpad's `vv/` on `git archive` extractions of `4d3e9b5` (`old`) and `14a8da5` (`new`).
- Downloads-are-data rule: every read under `historical/` was `python -I` with the path as an argument, run from `vv/` (the tool itself, and `vv/hash.py` for the digests). Nothing there was sourced, executed or piped.

## Prereg ordering: PASS

The acceptance tests ("Part 1 amendment: the void round", `prereg/S16.md` lines 148-170) and the ruling text (lines 137-146, verbatim: "1. 2022-23 GW7 (the round postponed after the Queen's death): keep it in the history labelled "void round", excluded from the blank/double base rates and counts, since no cup-schedule predictor can foresee it. Print both counts, with and without it.") are in `5e81c36` (11:31:16 +0200). `git merge-base --is-ancestor 5e81c36 14a8da5` holds; the code commit is 27 minutes later with `4d3e9b5` (which contains `5e81c36`) as its parent. Claim 1 confirmed. The ruling is present verbatim, so nothing to report under check 4.

## The delta, read

`VOID_ROUNDS = {("2022-23", 7): "void round"}` at module level, with a comment citing the ruling. In `history()`: `void` = the season's void rounds from that table only (no inference; `gaps` excludes them, so an unused number is still an unused number); `blanks`/`doubles` are summed from `bd` as before (the void round has no fixtures, so it contributes nothing); the season line prints `notes` only for non-empty lists, then `"; {blanks} team blanks, {doubles} team doubles"` and, when a void round exists, `" (with the void round: {blanks + len(teams) * len(void)} team blanks, {doubles} team doubles)"`; the per-event loop runs over `set(bd) | set(void)`, prints the void line and `continue`s before anything touches `table`; a closing line lists `voids` after the cross-season table. The `VOID_ROUNDS` value string is not read (the label is written out in the print lines); it names the round as the prereg asks. Two cosmetic notes, no effect: line 148 has a run of 13 spaces inside one expression; the void line's doubles count in the with-count is the same as the base count by construction (a void round creates no double), which is correct.

## Acceptance tests of the amendment

1. **The void round in one table, no guessing.** `VOID_ROUNDS` is the only source (grep: lines 36-41, 143); `gaps` is computed from the fixtures and only subtracts the named void rounds. On the real 2019-20 file the line still reads `numbered above 38: [39, ..., 47]; unused numbers: [30, ..., 38]` (unchanged from `4d3e9b5`, see check 3). Mutation V7 (every gap in 1..38 guessed as void) is red. PASS.
2. **The history line.** Real output: `2022-23: 20 teams, 37 events (void round GW7 (no fixtures)); 22 team blanks, 42 team doubles (with the void round: 42 team blanks, 42 team doubles)`. Base count 22 / 42 as before; with-count 42 / 42. PASS.
3. **The cross-season table.** Table row `GW7: blank 0 / 0; double 1 / 2` is unchanged (its one double season is 2023-24, `GW7: double 2: team 6, team 12`); the void round never enters `table` (the `continue` precedes the `table[e]` updates; mutation V5 pushing it in is red; the test asserts `7 not in table`). Closing line: `void rounds, outside the base rates: 2022-23 GW7 (20 team blanks)`. PASS.
4. **The reproduction test unchanged.** `python -I <tree>/tools/blank_double.py test --hist C:/GIT/FPL/historical` from both trees: four lines identical (`REPRODUCE 2024-25: 760 team-events ... every count equal`, `2025-26` likewise, secondary 750 equal, `REPRODUCTION PASS`), exit 0 both. `test()` is untouched by the diff. PASS.
5. **Tests.** One new test (`test_the_void_round_is_labelled_and_kept_outside_the_base_rates`): toy 2022-23 with events 1, 2, 8 (gaps 3-6 plain unused, 7 void); the plain-unused case also in the existing 2019-20 toy (`unused numbers: [2, 3,`). Hermetic (`tempfile.mkdtemp`, toy CSV, no clock/zone/git). Red on the old tool, green on the new (check 6); one mutation per rule red (check 6); suite green four ways (check 2). The dry run before landing is the launcher's, after this report. PASS.

## Check 2: clean-checkout suite: PASS

`python -m unittest discover -v -p "test*.py"` on the extractions (`git hash-object` of the extracted files = blobs `75db6ce`/`4353a37` before, `d4dde39`/`ac76557` after; CRLF by `text=auto`, content the commits'):

| mode | `4d3e9b5` (before) | `14a8da5` (after) |
|---|---|---|
| bare | Ran 613, OK (skipped=10), exit 0 | Ran 614, OK (skipped=10), exit 0 |
| runner-like (`GITHUB_ACTIONS=true`, `GITHUB_REF=refs/heads/s16-wip`, `FPL_DRY_RUN=true`, `FPL_DATA_DIR=C:\GIT\FPL-data`) | - | Ran 614, OK (skipped=3) |
| stand-in zones (`PYTHONTZPATH` = scratch `tz2`) | - | Ran 614, OK (skipped=1) |
| hermetic (empty HOME/USERPROFILE/XDG_CONFIG_HOME, `GIT_CONFIG_NOSYSTEM=1`, empty global config, author variables unset) | - | Ran 614, OK (skipped=10) |

The one added test is the void test (present in the four after-runs, absent before). Matches the implementer's `s16void_suites_out.txt` exactly (614/614/614/614, skipped 10/3/1/10). The no-import tests (`tests/test_S3.py` and `tests/test_S4.py`) are ok in every run; the data worktree is clean after the runner-like run.

## Check 3 (the item's own outputs, re-run): PASS

`python -I <tree>/tools/blank_double.py history --hist C:/GIT/FPL/historical`, both trees, exit 0: 125 lines before, 127 after. `diff`: exactly line 53 changed (the 2022-23 line above, replacing `2022-23: 20 teams, 37 events (numbered above 38: []; unused numbers: [7]); 22 team blanks, 42 team doubles`), one line added after it (`  GW7: void round - no fixtures, every team blanks; outside the base rates`), one line appended at the end (the `void rounds, outside the base rates` line). Every other line of the eight seasons and the cross-season table is byte-identical; the empty `numbered above 38: []` is gone (the earlier verifier's cosmetic note). My before-output equals the implementer's `s16p1_history.txt` and my after-output equals `s16void_history.txt`, both `diff`-empty. Claim 3 confirmed.

## Check 5: recording path: PASS

Two copies of `C:\GIT\FPL-data` at `9da6ff1` (`.git` excluded), a `sitecustomize` shim first on `PYTHONPATH` pinning `datetime.now()` to 2026-10-19T00:00:00Z (printed and checked), the nightly's commands (`fpl_edge.py --record --source {own,xg,minutes,bottomup,fpl_ep} --status`, `--watch watchlist.txt --out`, `--diff --out`, `--stuck`) from the `4d3e9b5` tree on one copy and the `14a8da5` tree on the other. Both: `RECORD OK own 275, xg 260, minutes 260, bottomup 260`, `RECORD SKIP fpl_ep the export has no ep_next for any player`, every command exit 0; `diff -rq` of the two copies empty; `projection_log.csv` 6812 rows, sha256 `b927...` on both (the digest the S16 part 1 verifier obtained from the same data). The real 5757-row log is an exact prefix after CRLF normalisation (the worktree file is checked out `eol=crlf`; the writer emits LF), 1055 rows appended, 0 changed. The item touches no runner file (`git diff --stat 4d3e9b5 14a8da5` on `fpl_*.py`, `checks.py`, `p1_eval.py`, `test_fpl.py`, `.github/`: empty) and `blank_double` is referenced outside `tools/` and its test only in CHANGELOG, prereg and worklog. Claim 5 confirmed; the real data worktree is untouched.

## Check 6: mutation spot-check: PASS

On an LF-normalised copy of the `14a8da5` tree (`git hash-object` = blob `d4dde39` before and after each run). The implementer's `mutate_s16p1.py` re-run by me: P1-P15 all RED (15/15; P11-P15 the void rules: no void round, void inside the base count, with-count without it, void listed as unused, no closing line). My own ten, `tests.test_S16_part1`:

| mutation | result |
|---|---|
| V1 void round keyed to 2021-22 | FAILED (failures=1) |
| V2 void round keyed to GW8 | FAILED (failures=1) |
| V3 with-count misses one team | FAILED (failures=1) |
| V4 per-event void line silent | FAILED (failures=1) |
| V5 void round pushed into the cross-season table | FAILED (failures=1) |
| V6 closing line counts rounds, not teams | FAILED (failures=1) |
| V7 every gap in 1..38 guessed as a void round | FAILED (failures=3) |
| V8 empty lists printed again | FAILED (failures=2) |
| V9 the with-count's doubles inflated | FAILED (failures=1) |
| V10 void round printed after all base-rate rows instead of in event order | OK (not caught) |

9/10 red. V10 is an equivalent mutant on the toy (its only base-rate event, GW2, precedes GW7 either way); on the real data the GW7 line would move below GW37, a presentation difference the prereg does not pin. Not a defect. The new test red on `4d3e9b5` with the new test file (`FAILED (failures=1)`, the void test, the old line reading `(numbered above 38: []; unused numbers: [3, 4, 5, 6, 7]); 1 team blanks, 1 team doubles`), green on `14a8da5` (9 tests OK); the old test file on the new tool green (8 tests OK). Claim 4 confirmed.

## Check 7: secrets: PASS

`git show 14a8da5:tools/blank_double.py 14a8da5:tests/test_S16_part1.py | grep -i -E "apikey|api_key|authorization|bearer|secret|token|https?://|[A-Za-z0-9]{32,}"`: no match.

## The judgement asked for

"Excluded from the blank/double base rates and counts" plus "print both counts": met. The season's main count is without the void round (22 team blanks, 42 team doubles) and the with-count is printed beside it in the same line (42 / 42); the cross-season table carries nothing from the void round and the closing line lists it apart with its 20 team blanks; the per-event line keeps it in the history under the label "void round". Nothing infers other void rounds. One observation for the record, not required by the ruling: the tool does not assert that a named void round holds zero fixtures; if a future entry named a round that has fixtures, that round's own blanks and doubles would stay in the season totals but drop out of the per-event listing and the table. With the single ruled entry (0 fixtures in 2022-23 event 7, confirmed by the earlier verifier's independent count) this cannot occur. The commit carries no CHANGELOG entry; the launcher said that comes at landing.

## Claims checked

1. Order: `5e81c36` before `14a8da5`, ancestor relation and timestamps. Confirmed.
2. The change: table from the ruling, no guessing (V7 red, 2019-20 line unchanged); the 2022-23 line, the per-event line, the table exclusion and the closing line all as quoted; empty lists gone; reproduction test unchanged. Confirmed.
3. Real files: only the three lines differ. Confirmed.
4. Tests: one new test red before, green after; P1-P15 red; 613 -> 614 green four ways. Confirmed.
5. Runner path untouched. Confirmed.

VERDICT: PASS

The amendment's acceptance tests and the ruling were committed in `5e81c36` before the single code commit `14a8da5`, which changes only `tools/blank_double.py` and its test; on the real history the delta is exactly the three lines the ruling asks for, with the base count (22 / 42) and the with-count (42 / 42) side by side, the void round labelled in the per-event list, absent from the cross-season table and listed apart with its 20 team blanks, and the reproduction test output unchanged from both trees; the new test is red on the old tool and green on the new; 15 + 9 mutations are red and the one survivor is an equivalent mutant on the toy; the suite goes 613 -> 614 green bare, runner-like, with stand-in zones and hermetically; the recording path regenerates a byte-identical projection log from both trees under a frozen clock; the two files hold no secret; and nothing on the runner path moved.
