# Verifier report: W2 amendment 2 (section exceptions)

Verifier: backtest-verifier, run on Fable 5.1 (model fable, effort high), 19 Oct 2026 evening.
Agent file read from disk first (`.claude/agents/backtest-verifier.md` in the worktree); it matches the loaded instructions.
Scope: branch `w2-wip`, scratch worktree `.../scratchpad/w2`, code commit `c21e0e0` on top of `d0ac3f5`.
Nothing was written outside this file; all runs were on `git archive` copies under `.../scratchpad/verify_W2a2/`.

## Prereg and ruling

- Ruling: master `a78e2e7` (`prereg/W2.md`, last section "Amendment 2: section exceptions, 19 Oct evening"),
  committed 2026-10-19 21:11:59 +0200. Code commit `c21e0e0` is 2026-10-19 21:24:19 +0200 (author and committer
  dates equal). The prereg precedes the code: PASS.
- The amendment carries the full "RULING 19 Oct evening" block (points 1-5, END RULING). Point 3, verbatim in the
  prereg: "A KeyError (or any exception) inside a section ends as SKIPPED with the same check-31 WARN, never a red
  night. The standings flag rule stays limited to event 2." Matches the text given at launch character for character.
- Observation (not a FAIL): `a78e2e7` is not an ancestor of `c21e0e0`; `w2-wip`'s own `prereg/W2.md` at `c21e0e0`
  is master's minus exactly those 20 lines (`git diff a78e2e7 c21e0e0 -- prereg/W2.md`: 20 deletions, nothing else).
  The branch picks the amendment up when it takes master before Saturday's merge, as the prereg plans.

## Code scope (`git diff d0ac3f5 c21e0e0`)

Only `fpl_sections.py` (+10/-7) and `tests/test_W2.py` (+34). Every other runner file is byte-identical
(`fpl_nightly.py`, `fpl_sync.py`, `checks.py`, `fpl_edge.py`, `fpl_lambda.py`, `fpl_chips.py`, `fpl_league.py`,
`fpl_bt.py`, `fpl_pit.py`, workflows): PASS.

`fpl_sections.py`:
- `except MISSING as e` -> `except Exception as e`; `MISSING` narrowed to the three `MissingInput` classes;
  `why = str(e) if isinstance(e, MISSING) else f"{type(e).__name__}: {e}"`; the unused `sqlite3` import removed;
  docstrings updated. `main()` still returns 0 unconditionally; the loop over `TITLES` is unchanged, so the second
  section runs after the first fails.
- Output text unchanged for every pre-existing case: all three `MissingInput` classes subclass `Exception` directly
  (`fpl_bt.py:66`, `fpl_chips.py:43`, `fpl_league.py:45`), never `KeyError`/`OSError`, so a missing input still
  prints its plain message, and `sqlite3.Error`/`OSError`/`KeyError` still print `<type>: <message>` as before.
- `fpl_nightly.py` lines 274-283 ("SECTIONS FAILED" on a non-zero exit or a missing report) unchanged.
- `checks.py` `c31` unchanged: returns only `WARN` or `OK`; its regex `SKIPPED: .*` matches the new lines.
- `fpl_sync.py` `flag_standings_labels` unchanged: `WHERE s.event = 2 AND s.total != g.total_points` (event 2 only).

Behaviour probes on the `c21e0e0` copy (no tracked file edited):
- CLI, empty data folder: prints `CHIPS SKIPPED: no dated export under ...` and `LEAGUE SKIPPED: ... fpl.sqlite is
  missing`, appends both ruled sections to the report, exit 0.
- `FS.main()` with `fpl_chips.live` raising `KeyError(7)` and `fpl_league.report` raising `ZeroDivisionError`:
  prints `CHIPS SKIPPED: KeyError: 7` and `LEAGUE SKIPPED: ZeroDivisionError: float division by zero`, returns 0.
- `c31` on those two lines: `('WARN', 'CHIPS SKIPPED: KeyError: 7, LEAGUE SKIPPED: ZeroDivisionError: float division
  by zero')`; on a `SECTIONS FAILED` line: WARN. Never FAIL.

## Checks

1. Point-in-time leak check: n/a. The item produces no forecast, feature or metric (a report-section exception
   handler). The recording path is covered under check 5.
2. Clean-checkout test run (`git archive` copies, `python -m unittest discover -p "test*.py"`, Python 3.14.7,
   `FPL_DATA_DIR` unset):
   - before (`d0ac3f5`): `Ran 625 tests in 206.773s`, `OK (skipped=10)`
   - after (`c21e0e0`): `Ran 626 tests in 268.211s`, `OK (skipped=10)`
   - The new test `tests.test_W2.ReportSections.test_any_exception_in_a_section_is_skipped_and_the_other_runs` is
     collected by discovery and passes. Delta +1 test as reported.
   - The implementer reported 9 skipped; I see 10: the extra one is a tzdata skip
     (`skipped 'no time-zone database here (Windows without tzdata)'`) on top of the nine real-data/zone/copy skips.
     Environment, not the item.
   PASS.
3. Pre-registered evaluation: n/a (wiring; the prereg's metric, bootstrap and threshold are all "n/a").
4. Prereg metric/filter/bootstrap/threshold: n/a by the prereg; the ruling is present verbatim (above). No metric
   promoted, no re-tuning (nothing measured). PASS.
5. Recording path. Data copied from `C:\GIT\FPL-data` (no pull, no write there) to two scratch folders; all six
   sources recorded with the before code and the after code (`fpl_edge.py --record --source <src> --status ...`):
   `RECORD OK own 285, xg 264, minutes 264, bottomup 264, fpl_ep 668, bottomup_lambda 264` with both.
   Logs: 7766 rows each (7502 baseline + 264 bottomup_lambda, the sixth source not yet on `data`).
   - before-code log vs after-code log: identical in every row with `made_at` stripped (the only byte difference is the
     wall clock, 19:37:24-26 vs 19:37:27-29 UTC); per source, all rows identical: own 1937, xg 1802, minutes 1547,
     bottomup 1547, fpl_ep 668, bottomup_lambda 264.
   - rows 1-5757 byte-identical to the baseline in both; the rewritten GW8 snapshot rows 5758-7502 equal the baseline
     with `made_at` stripped in both.
   `fpl_edge.py` and `fpl_lambda.py` are byte-identical across the item and `fpl_sections.py` is run by the nightly as a
   later step that never opens the log. PASS.
6. Mutation spot-check, scratch copies of `c21e0e0`, `python -m unittest tests.test_W2` (12 tests):
   - red check: the new test against `d0ac3f5`'s `fpl_sections.py`: ERROR (`ZeroDivisionError` propagates).
   - mut1 `except Exception` -> `except MISSING`: ERROR in the new test.
   - mut2 `why = str(e)` (type name dropped): FAIL in the new test (`'CHIPS SKIPPED: float division by zero'`).
   - mut3 `break` after a failing section: the new test ERROR (`KeyError: 'LEAGUE'`), plus
     `test_byte_identical_to_the_tools` ERROR and `test_a_missing_input_is_one_skipped_line...` FAIL.
   - mut4 (mine) `main()` returns 1: FAIL in the new test and in the missing-input test.
   - mut5 (mine) `f"{e}: {type(e).__name__}"` (order swapped): FAIL in the new test.
   All five red. PASS.
7. Secrets: grep of the two changed files and of the diff for `apiKey=`, `api_key`, `Authorization`, `Bearer`,
   32+ hex runs: no match. No key-like string in the item. PASS.

Runner rules: `fpl_sections.py` imports `argparse`, `os`, `sys`, `datetime` and the project's `fpl_bt`, `fpl_chips`,
`fpl_league` only; no `import tools`/`from tools` anywhere in the runner's `*.py`; the existing guard test
(`test_fpl.py` ~5232, "runner never imports tools/") is in the green suite. PASS.

Hermetic: the new test uses `tempfile`, `tests.test_S9.toy_league`, `unittest.mock` and a fixed `datetime`; no
global config, zone or outside file.

## Verdict

VERDICT: PASS

The ruling is in `prereg/W2.md` verbatim on master (`a78e2e7`, 21:11:59) before the code (`c21e0e0`, 21:24:19); the
diff is confined to `fpl_sections.py` and one new hermetic test; any exception inside a section now ends as one
`<TITLE> SKIPPED: <type>: <message>` line while the other section still runs and the CLI exits 0, check 31 WARNs and can
never FAIL, the text for a missing input and for `sqlite3`/`OSError`/`KeyError` is unchanged, the nightly's
`SECTIONS FAILED` path and the event-2 standings flag rule are untouched; the suite is 625 -> 626, OK on clean
checkouts of both commits; the new test is red on the old code and all five mutations (the three named plus two of my
own) go red; a six-source regeneration on a copy of the real data gives a projection log identical row for row to the
pre-item code apart from the wall clock; no secrets, standard library only, nothing under `tools/` imported. The one
note for the merge: `w2-wip`'s own copy of `prereg/W2.md` does not yet carry amendment 2 and must take master before
Saturday.
