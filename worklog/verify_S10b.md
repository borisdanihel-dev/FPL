# verify_S10b — Step 10b (Part F item F-C): 2023/24 and 2024/25 under the 2026/27 rules

Verifier: Claude Fable 5.1 (model fable, effort high), 19 Oct 2026 evening.
Worktree verified: `s10b-wip` at a2902f9 (prereg c0116fe, downloads 5918f02,
landing merge 4ddea35, code a2902f9). All my runs were in my own scratch
trees built with `git archive` (no checkout); nothing in the worktree,
`C:\GIT\FPL`, `C:\GIT\FPL-data` or `C:\GIT\FPL-b` was written except this
file. No network, no `git pull/fetch/commit/push/checkout`.
Hashes below are masked (first 4 characters, then `...`).

## Prereg order — PASS

`prereg/S10b.md` is c0116fe (2026-10-19 19:05:13 +0200). The downloads commit
5918f02 (19:06:49) and the code commit a2902f9 (19:11:25) both descend from it
(`git merge-base --is-ancestor` true for both). The prereg contains the
ruling text "F-C. Step 10b: ..." verbatim, and the definitions (own table =
2026/27 table with `defensive_contribution` zeroed; manager rows out;
within +-1 among minutes > 0; gameweek bootstrap 10,000 / 90% / seed
20261019; pass bar >= 0.99 per season; DEFCON missing flagged, never
invented; bonus official flagged "<season> BPS"; 2026/27 position by code).

## Downloads record — PASS

`worklog/downloads_2026-10-19b.md` records eleven files with URL, fetch time
(UTC), bytes and SHA-256. I recomputed SHA-256 and byte counts for every file
under the worktree's `historical/` and `tools/odds/`:

| file | bytes | SHA-256 (masked) | matches record |
|---|---|---|---|
| historical/2022-23/merged_gw.csv | 4638801 | b78a... | yes |
| historical/2022-23/teams.csv | 1711 | be6a... | yes |
| historical/2022-23/players_raw.csv | 280362 | a874... | yes |
| historical/2023-24/merged_gw.csv | 4997188 | e9c0... | yes |
| historical/2023-24/teams.csv | 1715 | 7795... | yes |
| historical/2023-24/players_raw.csv | 310197 | 43d8... | yes |
| historical/2024-25/merged_gw.csv | 5125595 | 5bbb... | yes (same as S11's copy) |
| historical/2024-25/teams.csv | 1717 | d10a... | yes (same as S11's copy) |
| historical/2024-25/players_raw.csv | 342122 | 7568... | yes |
| tools/odds/E0_2023-24_fetched_2026-10-19.csv | 172196 | b2e0... | yes |
| tools/odds/E0_2024-25_fetched_2026-10-19.csv | 197110 | d0c8... | yes |

The three `fixtures.csv` (2022-23 e783..., 2023-24 d852..., 2024-25 ce69...)
were not re-fetched; the record points to the morning's
`worklog/downloads_2026-10-19.md`, whose hashes and sizes match the files on
disk. The 2026/27 inputs the re-score uses (`game_config.json` a72a...,
`elements_positions.csv` ac3d...) match the morning record too. Both E0 files
have 380 data rows (a full season) and the football-data header. The
`historical/` files are gitignored (`.gitignore` line 17); the worktree's
`git status` is clean.

Note (not a failure): the prereg's data list names `fixtures.csv` among the
files "recorded ... in worklog/downloads_2026-10-19b.md"; the b record
cross-references the morning record for them instead of repeating the rows.

## Check 1 — point-in-time — N/A, evidence given

The item produces no forecast or feature; the reproduction test and the
re-score are descriptive per player-gameweek. `load_season` reads only
`<season>/merged_gw.csv`, `<season>/players_raw.csv`,
`2026-27/game_config.json` and `2026-27/elements_positions.csv`; `score()`
uses only the row's own columns, so a unit for round g depends on nothing
from any other round (1a/1b trivially hold; nothing to truncate). 1c does
not apply (no correlation metric on points).

## Check 2 — clean-checkout test run — PASS

`python -m unittest discover -p "test*.py"` with `FPL_DATA_DIR` unset, in
scratch trees from `git archive`:
- before (4ddea35, the merge just before the code commit): **Ran 687 tests, OK (skipped=10)**
- after (a2902f9): **Ran 692 tests, OK (skipped=10)**
- `tests/test_S10b.py` alone: 5 tests OK.

The delta is +5, as claimed. The implementer's stated expectation was
686 + 5; I measure 687 + 5 at this branch (the base count was an
expectation, not a measurement; the item's own contribution is exactly 5).

## Check 3 — re-run of the pre-registered evaluation — PASS

From my `after` tree, `--hist` pointing at the worktree's `historical/`:

- `rules.py test --season 2023-24 --out ...`: PRIMARY 11086 of 11086 within
  +-1 = 1.0000, 90% CI 1.0000 - 1.0000, PASS; all 28742 units 1.0000; exact
  1.0000; GKP 755, DEF 3748, MID 5176, FWD 1407; no misses; "0 manager rows
  out"; DEFCON parts: no. My `rules_test_2023-24.txt` is byte-identical to
  the implementer's (`diff` empty; SHA-256 b8f1... both, equal to the digest
  in the implementer's run.txt).
- `rules.py test --season 2024-25 --out ...`: PRIMARY 11431 of 11431 =
  1.0000, CI 1.0000 - 1.0000, PASS; all 26919 units 1.0000; GKP 760, DEF
  3745, MID 5668, FWD 1258; "322 manager rows out". Byte-identical to the
  implementer's (SHA-256 ff5e... both, equal to run.txt).
- `rules.py normalise --season 2023-24` / `2024-25`: my `rescored_*.csv` are
  byte-identical to `tools/out/rules_2023-24/rescored_2023-24.csv`
  (bc21...) and `tools/out/rules_2024-25/rescored_2024-25.csv` (49f8...).
  Position changes 2023-24: MID->FWD 73, FWD->MID 200, DEF->MID 49, MID->DEF
  72 player-gameweeks; 2024-25: DEF->MID 88, MID->DEF 112, FWD->MID 111,
  MID->FWD 37; without a code: 0 in both.

Independent re-computation outside the harness (`python -I`, my own scorer
from `game_config.scoring` with DEFCON dropped, own positions, manager rows
out): 2023-24 units 28742, appeared 11086, within +-1 11086 (share
1.000000), exact 11086; 2024-25 units 26919, appeared 11431, within 11431,
exact 11431. Audit of the rescored CSVs: every `code` equals the season's
`players_raw.csv` code (0 mismatches), every `position_2627` equals the
2026/27 position by code or the own position when absent (0 mismatches),
every element is in `players_raw.csv`, `bonus` equals the merged bonus per
unit (0 mismatches), `points_2627_rules` equals the sum of the categories
(0 mismatches), `defensive_contribution` is 0 and `defcon_flag` is "DEFCON
missing" on every row, `bonus_flag` is "<season> BPS" on every row, the sum
of `official` equals the sum of `total_points` of the merged file.

Data facts I confirmed directly: neither season's `merged_gw.csv` has
`defensive_contribution`, `clearances_blocks_interceptions`, `tackles` or
`recoveries` columns; 2024-25 has 322 rows with position `AM`, 2023-24 none;
no duplicate (element, fixture) rows; goalkeeper goals = 0 in both seasons,
so the goalkeeper goal value is indeed untested by these seasons, as claimed.

The implementer's run.txt files name commit a2902f9 with 0 modified tracked
files and digests equal to the files on disk.

## Check 4 — prereg metric, filter, bootstrap, threshold — PASS

`test_season`: units = player-gameweeks of the de-duplicated rows with
position in `CSV_POSITION` (AM out); primary = `share(appeared, within)`
with `appeared` = minutes > 0 and `within` = |points - official| <= 1;
`bootstrap(appeared, within, seed=seed)` with the unchanged Step 10
bootstrap (unit = gameweek, n=10000, level 0.90), seed default 20261019;
bar printed as `primary >= 0.99`, per season. `own_table` zeroes only
`defensive_contribution`. All as the prereg. No metric was promoted and no
constant was tuned after results: the code commit is one commit after the
downloads, the prereg is unchanged since c0116fe, and the results are exact
(1.0000) so there was nothing to tune toward.

Acceptance tests named in the prereg, against `tests/test_S10b.py`:
season argument reads the right files (CLI test, toy root); manager rows
out (asserted "1 manager rows out", element 99 absent); own table drops only
DEFCON (OwnTable); a hand row under each table (OwnTable: difference 2 for a
DEF at the threshold); DEFCON missing flagged, never invented (parts=True vs
False; flag on every row); 2026/27 position by code (P1 MID->FWD, P2
DEF->MID; P4 gone keeps own position); bonus official and flag; share and
bootstrap on a toy (share 1.0 and 0.5 asserted; the CI is computed and
printed but not asserted — the bootstrap function itself is Step 10's,
unchanged, and covered by tests/test_S10.py); run.txt (read back through
`provenance.read_run`); nightly isolation (subprocess import probe);
`test_fpl.py` untouched (confirmed by `git diff c0116fe a2902f9`, empty).
Gap, information only: "a player without a code flagged" has no test (every
toy player has a code; only "without a code: 0" is asserted). I probed it on
a toy: a player absent from `players_raw.csv` gets `code` blank,
`position_2627` = own position, `in_2627` 0, and "without a code: 1" in the
message; `test_season` still runs. On the real data no such player exists
(0 in both seasons).

## Check 5 — recording path — PASS

The item is offline. `git diff --name-only 4ddea35 a2902f9` = `tests/test_S10b.py`,
`tools/rules.py`; `git diff --name-only c0116fe 5918f02` = the two E0 CSVs
and `worklog/downloads_2026-10-19b.md`. No runner file (`fpl_nightly.py`,
`fpl_ship.py`, `fpl_edge.py`, `fpl_sync.py`, `fpl_gate.py`,
`fpl_publish.py`, `fpl_hist.py`, `.github/`, `test_fpl.py`) changed. Grep
of the runner files and workflows for `tools/`, `E0_`, `rules`,
`provenance`: no hits. Import probe in the `after` tree (import
`fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish`, then list
modules whose file is under `/tools/` or named `tools`/`analysis`/`rules`/
`provenance`): `[]`. The projection log cannot move because nothing on the
recording path changed; I did not run `--record` (the runner is the only
writer and `C:\GIT\FPL-data` is read-only for me).

The 2025/26 path (the frozen Step 10 behaviour): master's `tools/rules.py`
(c0116fe = 4ddea35 for this file) and a2902f9's, both run on the same
`historical/` folder: `test` output byte-identical (SHA-256 246c... both;
PRIMARY 11361 of 11361, 29338 units, DEFCON parts agree 3950/3950, 1428/1428,
5347/5347); `normalise` CSV byte-identical (55fa... both); the normalise
message identical apart from my own output filename.

## Check 6 — mutation spot-check — PASS (6 of 6 red)

In a scratch copy, `tests/test_S10b.py` (baseline 5 OK), each mutation
applied alone and the file restored (confirmed identical to a2902f9 after):
1. `own_table` keeps the DEFCON values -> FAIL test_only_the_defcon_category_changes.
2. manager rows kept -> 3 ERRORs (KeyError on `AM`).
3. `flag = ""` (DEFCON flag dropped) -> FAIL test_the_output.
4. `normalise_season` ignores the 2026/27 position by code -> FAIL test_the_output.
5. primary share ignores the +-1 tolerance -> FAIL test_the_share_the_managers_and_a_miss.
6. DEFCON rebuilt when `parts` is False but a `tackles` column exists (invented) -> FAIL test_a_season_with_the_parts_rebuilds_defcon.

## Check 7 — secrets — PASS

The item's added/changed files (two E0 CSVs, the downloads record,
`tools/rules.py`, `tests/test_S10b.py`, `prereg/S10b.md`): no `apiKey=`,
`api_key`, `Authorization`, `Bearer`, `ODDS_API_KEY` or key-shaped token.
The only long hex strings are the eleven recorded SHA-256 digests and the
pinned vaastav commit 9779... in the downloads record. The E0 URLs recorded
are the plain football-data paths with no query string.

## VERDICT: PASS

The prereg was committed before the downloads and the code and carries the
F-C ruling verbatim; every recorded download hash and byte count matches the
files on disk; both reproduction tests re-run through the harness reproduce
the implementer's output byte-for-byte (2023-24 11086 of 11086, 2024-25
11431 of 11431 within +-1, CI 1.0000 - 1.0000, exact, well above the 0.99
bar) and an independent scorer outside the harness gives the same counts;
the metric, filter, bootstrap and bar are exactly the prereg's with no
post-hoc change; the 2025/26 path is byte-identical before and after; no
runner file changed and the runner imports nothing under `tools/`; the suite
goes 687 -> 692 all green; 6 of 6 mutations go red; no secrets. The only
notes are informational: the "player without a code" path has no test (I
probed it and it behaves as the prereg says; none occurs in the real data),
the bootstrap CI on the toy is printed but not asserted, and the base suite
count was 687 rather than the implementer's expected 686.
