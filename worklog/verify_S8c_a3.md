# Verifier report: S8c amendment 3 (tools/gw_pass.py writes xp_v2_all.csv)

Model: Fable 5.1 (claude-fable-5-1), effort high, as `.claude/agents/backtest-verifier.md`
says. The agent file on disk was read first; it matches the loaded instructions.

Item: `s8c-wip` commit `ea95cf6` on top of `71c9d17` (amendment 1, verified PASS).
Diff reviewed: `git diff 71c9d17 ea95cf6` = `tools/gw_pass.py` (+44/-2) and
`tests/test_S8c.py` (+90). No other file. Worktree
`.../scratchpad/s8c` clean, HEAD == origin/s8c-wip == ea95cf6.

Prereg: `prereg/S8c.md` on master, section "## Amendment 3", commit `6e7c918`
(2026-10-20 18:30:34 +0200), with the Ruling of Tue 20 Oct night verbatim at
the end (point 3, first bullet checked word for word against the launch text).
The code commit `ea95cf6` is 2026-10-20 18:34:22 +0200: prereg before code. PASS.

Data: `C:\GIT\FPL-data` at `63e6a44` (pull --ff-only: already up to date;
`git status` empty before and after my runs). Historical root `C:\GIT\FPL\historical`.
No API call was made (`ODDS_API_KEY` unset in every command). Scratch:
`.../scratchpad/v8c_a3/` only.

## The eight points asked

### 1. The pinned choice (every export player; not-forecast players at 0)

- How section 5 actually chooses: `side_by_side` calls `CH.xi_and_bench(squad, v2)`,
  which sets `proj = pts.get(r["id"], 0.0)` (tools/chips.py:190): a player xp_v2
  does not forecast enters the XI/bench/captain choice at 0. The print says so
  itself (gw8_pass.txt line 190: "no xp_v2 for Haaland (0 in the choice: status
  not a, under 45 minutes in the last four, or no fixture)"). The CSV's
  `xp_v2 = 0.0` for those rows therefore matches how the bundle chooses. PASS.
- Within the ruling or beyond: the ruling says "every player it forecasts". The
  CSV goes beyond it: 391 rows the forecast does not cover are added, marked
  unambiguously (`p_start` empty, `lambda_source` "not forecast"), so a reader of
  the ruling's narrower set can filter on `lambda_source != "not forecast"`
  and lose nothing. The prereg flags the choice as open for Boris; it is pinned,
  not hidden.
- Consequence of the alternative (forecast players only): Haaland (id 411,
  status d in the GW8 export) would be absent; W3 amendment 2's condition "all
  15 are in the CSV" would fail while he is in our 15, and GW8 REALISED would
  be "not recorded". With the pinned choice he is present at 0, which is also
  what section 5 gives him in the choice.
- Real GW8 numbers (my own run, below): 668 rows = the export's `all_players`;
  277 forecast (all `odds`, 10 of 10 fixtures priced); 391 "not forecast"
  (204 status not 'a', 0 without a fixture, 187 by the 45-minute gate or absent
  from the reliability inputs). Every forecast row passes the documented gate.

### 2. Exactness

My own script (`v8c_a3/exact.py`) ran `xp_v2_live.live` from the ea95cf6
archive on the real data and compared it to my reproduced CSV:
- rows: exactly the export's `all_players`, by id, unique; header
  `id,name,team,position,xp_v2,p_start,lambda_source`; 7 columns every row.
- forecast rows: `xp_v2 == repr(float(xp[pid]))` and `float(cell) == xp[pid]`
  exactly; `p_start == repr(float(detail[pid]["p_start"]))` and round-trips exactly
  (all 277). name = web_name, team = short name, position GK/DEF/MID/FWD.
- `lambda_source`: recomputed independently from `fixtures_next6` sorted by
  kickoff, joined by ";": equal for all 277 (no club has two GW8 fixtures, so
  the join order is not exercised on GW8; see check 6).
- not-forecast rows: `0.0,,not forecast` for all 391; row 411 =
  `411,Haaland,MCI,FWD,0.0,,not forecast`.
- line endings: bytes contain 669 LF, 0 CR (the earlier `grep -c $'\r'` = 669
  was MSYS grep's text-mode artefact; the byte count is authoritative).
- `run.txt` lists `xp_v2_all.csv  sha256 d8ba0bff...`; the file's SHA-256
  recomputed by me is the same. Result: `EXACT OK`. PASS.

### 3. Print byte-identical with and without the CSV

- The test `test_the_print_is_the_same_without_the_csv` patches `bundle` to run
  with `keep=None` and compares `gw9_pass.txt` bytes: green; my mutation M6
  (an extra `out(...)` on the CSV path) turns it red.
- Real data: I ran `tools/gw_pass.py` from clean archives of ea95cf6 and
  71c9d17 on the same data (63e6a44) into `v8c_a3/live_after` and
  `v8c_a3/live_before`. `gw8_pass.txt`: 20527 bytes both; byte-identical from
  line 2; line 1 differs only in the `generated HH:MM UTC` stamp (equal after
  masking it). My ea95cf6 print is also byte-identical from line 2 with the
  main session's `s8c_a3_live/gw8_pass.txt`, and the main session's a1 and a3
  prints are identical apart from the stamp. PASS.
- My CSV is byte-identical (`cmp`) with the main session's
  `s8c_a3_live/xp_v2_all.csv` (sha256 d8ba0bff...). The main session's
  `run.txt` names commit ea95cf6 with 0 modified tracked files; mine says
  "commit: unknown (git unavailable)" because a `git archive` tree is not a
  repository, which is the expected provenance for a clean-checkout run.

### 4. No section 5, no CSV; nothing substituted

- `main` writes the CSV only when `keep["res"]` was set, and `bundle` sets it
  inside section 5 after `XL.live` succeeded, the target matched and
  `side_by_side` returned. A missing input prints "missing input: ..." in
  section 5 (unchanged text) and no CSV follows. `test_no_section_5_no_csv`
  (prior season removed) is green; mutation M5 (write unconditionally) goes red
  on two tests. Nothing is substituted: the rows are the forecast or the
  explicit "not forecast" marker. PASS.
- Note (not a defect, within the prereg's words "if section 5 cannot run, no
  CSV"): `keep["res"]` is set later than `live_res["res"]`, so if own has no
  GW8 projection rows in the log, section 5 fails on "own has no GW8
  projections in the log" and no CSV is written even though xp_v2 itself ran.
  For Thursday this means a missing own row would make GW8 REALISED
  "not recorded" under W3 amendment 2. Today's run has 14 of 15 own rows and
  section 5 ran.

### 5. Clean-checkout suites (git archive, no keys present; `ODDS_API_KEY` unset)

| archive | bare | with FPL_DATA_DIR=C:/GIT/FPL-data |
|---|---|---|
| 71c9d17 (before) | Ran 764, OK (skipped=10) | Ran 764, OK (skipped=3) |
| ea95cf6 (after)  | Ran 767, OK (skipped=10) | Ran 767, OK (skipped=3) |

+3 = `XpV2Csv`'s three tests; 0 failures, 0 errors in all four. PASS.

### 6. Runner untouched

The diff holds no runner file (`tools/gw_pass.py`, `tests/test_S8c.py` only).
`.github/workflows/nightly.yml` and `fpl_nightly.py` reference nothing under
`tools/`; the suite's `test_the_nightly_imports_nothing_under_tools_or_analysis`
(tests/test_S3.py, tests/test_S4.py) passed in all four runs. Recording path:
the tool writes only under `--out`; `projection_log.csv` and the data worktree
are unchanged after my runs (`git status` empty at 63e6a44). PASS.

### 7. Mutations (my own, `v8c_a3/mutate.py`, scratch copy, each restored; unmutated copy green)

| # | line broken | result |
|---|---|---|
| M1 | "not forecast" label -> "none" | RED (rows test) |
| M2 | `repr(float(xp))` -> `f"{...:.6f}"` | RED (rows test) |
| M3 | fixtures sorted by fid instead of (kickoff, fid) | still green |
| M4 | `sorted(all_players, key=id)` -> export order | still green |
| M5 | CSV written even without section 5 | RED (2 errors) |
| M6 | an extra `out()` line on the CSV path | RED (print-identical test) |
| M7 | `run.wrote(...)` dropped around the CSV | RED (run.txt line) |
| M8 | `p_start` column from `p_sub` | RED (rows test) |
| M9 | not-forecast `xp_v2` blank instead of `0.0` | RED (rows test) |

7 of 9 red: check 6 PASS. The two survivors are toy limitations, not code
defects: the toy has one fixture per club (M3 changes nothing there; nor on
GW8, where no club has two fixtures) and the toy export's `all_players` is
already id-ordered (M4 changes nothing there). The real export is NOT
id-ordered (checked: 668 ids, unique, unsorted), so the id-sort is load-bearing
on Thursday's file; my exactness check confirms the real CSV is sorted. A
one-line strengthening (shuffle the toy's `all_players` in `setUp`; give one
toy club two target fixtures) would close both gaps. Recorded as a note, not a
defect.

### 8. Secrets

Full-file scan of `tools/gw_pass.py`, `tests/test_S8c.py`, my `xp_v2_all.csv`,
`run.txt` and `gw8_pass.txt` for `apiKey=`, `Authorization`, `Bearer`, 32+ hex
runs: only the two SHA-256 lines in run.txt. Neither changed file mentions
`ODDS_API_KEY` or `apiKey`. PASS.

## The agent file's numbered checks

1. Point-in-time: (a) one live gameweek only (GW8, in the future), so the three-
   gameweek truncation is not applicable; the forecast's training slice is
   `canonical_through(d, 7)` by construction. (b) Timestamp audit: export
   `fpl_export_gw7_2026-10-20.json.gz` generated 2026-10-20T13:01:33Z; odds
   snapshot `odds/odds_2026-10-20T1301Z.json.gz` 13:01 UTC (chosen by
   `OL.newest_snapshot(data_dir, dl)`, before the deadline by construction);
   prior = 2025/26 files; GW8 deadline 2026-10-23T17:30:00Z (events). Every
   input precedes the deadline. PASS. (c) Shift probe: no correlation metric
   in this item: n/a.
2. Clean-checkout suites: table in point 5. PASS.
3. Pre-registered evaluation: descriptive item, no metric; the item's own
   acceptance tests (rows = forecast and detail; not-forecast rows; round trip;
   print identical; CSV in run.txt) are present, green, and shown red by my
   mutations. My reproduced output matches the implementer's byte for byte
   (CSV sha256 d8ba0bff...; print identical from line 2). PASS.
4. Prereg: the ruling verbatim in `prereg/S8c.md`; no metric, no threshold, no
   re-tuning; the one open choice is stated in the prereg before the code. PASS.
5. Recording path: no runner file changed, projection log untouched. PASS.
6. Mutations: 7 of 9 red (point 7). PASS, with the two toy gaps noted.
7. Secrets: none. PASS.

Not in ea95cf6 (as the prereg sequences them after the verifier): the item's
report and the CHANGELOG entry.

VERDICT: PASS. The prereg and the verbatim ruling precede the code; the CSV is
exactly `xp_v2_live.live`'s forecast and P(start) in repr, one row per export
player by id, with the not-forecast players at the 0 that section 5's own choice
gives them, marked and filterable, so the ruling's narrower set is recoverable
and Haaland's row keeps W3's "all 15 in the CSV" satisfiable; the print is
byte-identical with and without the CSV on the toy and on the real GW8 data
(stamp aside, and identical to the main session's); no CSV without section 5;
my reproduction equals the implementer's byte for byte and the SHA-256 in
run.txt; suites 764 -> 767 OK bare and on real data; no runner file, no secrets;
7 of 9 mutations red, the two survivors being toy limitations whose real-data
behaviour I verified directly. Open for Boris: the pinned "every export player
at 0" choice versus the ruling's "every player it forecasts".
