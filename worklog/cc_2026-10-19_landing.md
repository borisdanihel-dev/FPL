# Landing 2026-10-19 — S4, S7, S5, S6, S9 (RULING morning 19 Oct item 1) — report

Lane B. Branch `landing-2026-10-19`, pushed at `067ca5f`, built in a
temporary worktree from `origin/master` (`87d45ce`, after W1 and S16
part 2) once Boris reported W1's real dispatch green (data `bd724ca`,
06:13 UTC, STATUS OK 28/28). Nothing was force-pushed; `lane-b` was not
rebased; `master` is untouched until the dry run is green and Boris says
land.

## What the branch holds

- The revert of `32bf218` (the S4 landing `70f026d` restored: `tools/backtest.py`,
  `tools/hist_pit.py`, `tests/test_S4.py`, `prereg/S4.md`, the S4 report
  and verifier report, `.gitignore`'s `/tools/out/`).
- Lane-b's commits after `70f026d` for S7, S5, S6 and S9, cherry-picked
  in order (35 commits; the S8, S11, S12 and S13 commits and the merge
  commit were left out): `tools/chips.py`, `tools/odds_lambda.py`,
  `tools/console_utf8.py`, `tools/xp_v2.py`, `tools/league.py`, the
  odds CSVs under `tools/odds/`, `tests/test_S5.py`, `test_S6.py`,
  `test_S7.py`, `test_S9.py`, the preregs, reports and verifier reports.
  Every landed file is byte-identical to lane-b at `e7e86e9` (diff empty).
- `CHANGELOG.md` = master's entries, then the S4 entries the revert had
  removed, then lane-b's entries since `70f026d` (pure additions, checked:
  353 lines; each heading once).
- `BUILD_PLAN.md` Part C rule 2 gains the tie-break bullet (RULING S5
  result point 2): GK/DEF ties within 0.3 xP on `own` go to
  `bottomup_lambda`, and the keeper line shows each keeper's odds-implied
  P(clean sheet).
- `overrides.csv` at the repo root, header only
  (`player,gw,p_start,reason,timestamp_utc`), RULING morning item 1.
- `worklog/SESSION_STATE_B.md` as on lane-b at `e7e86e9`.

Not in this landing (they stay on `lane-b` for the next one): S8, S12,
S13, S11, the provenance helper and the bundle.

## Tests

`python -m unittest discover -p "test*.py"` on the landing branch
(`test_fpl.py` plus `tests/`, including lane A's `test_W1.py`,
`test_S16.py`, `test_S3.py`), `FPL_DATA_DIR` unset: **590 tests OK, 10
skipped**, 322 s. The branch adds and changes files under `tests/`, so
it needs the green dry run before it lands (RULING lane B landing), and
lands outside 9d (the GW8 deadline is Friday 2026-10-23 17:30 UTC; now
is Monday morning).

## Provenance check (RULING S8 verifier FAIL item (e))

Every recorded output of S4, S5, S6, S7, S9, S12 and S13 was rerun on
lane-b's `7f72141` (the items' final code plus the provenance wiring,
which changes no number) into each tool's folder with `run.txt`, and
compared byte for byte with the recorded file (the tools' code is unchanged from `7f72141` through `ed1bbb6`, the commits the runs record):

| item | output | result |
|---|---|---|
| S4 | `selftest.txt`, `power.txt`, `report.txt`, the 14 `compare_*.txt` | identical, all 17 |
| S5 | `odds_lambda_test_2025-26.txt`, `_condition_2026-27.txt`, `_fixture_ARS_CHE.txt`, `_live.txt` | identical, all 4 |
| S6 | `xp_v2_develop_cut6.txt`, `xp_v2_validate_cut6.txt` | identical |
| S6 | `xp_v2_forecast.txt` (live, information only) | differs (Vuskovic 5.96 → 6.01 and the like): recorded 21:48 UTC on 18 Oct, ten minutes before that night's nightly committed new data (`9da6ff1`, 21:58 UTC); the inputs moved, the code did not |
| S7 | `chips_live.txt` (live, information only) | differs in one margin (GW11 +4.1 → +4.2): recorded 20:24 UTC on 18 Oct, before the same nightly; the inputs moved |
| S7 | `chips_replay_2025-26.txt` (the pre-registered replay) | identical (711 s) |
| S9 | `league_2026-10-18.txt` | identical up to the date in the file name and header |
| S12 | `minutes_v2_test_2025-26.txt`, `minutes_v2_live.txt` | identical |
| S13 | `defcon_test_2025-26.txt` | identical |

Reading: every pre-registered test and replay number stands on the
final code; the two live screens moved only because the data moved
after they were recorded, which is what live screens do. No rerun is
needed for the record; the two live files are regenerated on the current
data in the tools' folders with their `run.txt`.

## The S8 replay provenance (for the record)

Found by the S8 verifier this morning: the S8 replay recorded on 19 Oct
came from the first commit's candidate generator, not the final code.
The final-code replay (`s8_run3`) is running with `run.txt` and is
recorded under RULING S8 verifier FAIL item (a) when it lands; S8 is not
in this landing.

## Proposed CLAUDE.md line (RULING S8 verifier FAIL item (e))

Under "Work-item protocol":

> - **Provenance.** Every output folder of a tool holds a `run.txt`,
>   written by the tool itself (`tools/provenance.py`): the commit it ran
>   on, the modified tracked files at the run, its start and end times
>   (UTC) and the SHA-256 of each output. A report cites a run only when
>   that commit is the item's final code; a number from any other run is
>   regenerated, never cited.

## Needs Boris

1. The dry-run click on `landing-2026-10-19` (`067ca5f`). On green,
   outside 9d: push the branch to `master` (fast-forward), then merge
   `master` into `lane-b` (a merge commit, no rebase) and push `lane-b`.
2. The CLAUDE.md line above (lane A edits CLAUDE.md, or the landing
   adds it on Boris's word).
