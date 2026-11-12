# Verifier report: W3 (Part F item F-B; runner work, unmerged)

Verifier: the `backtest-verifier` agent, model Fable 5.1, effort high (the
agent file on disk, `.claude/agents/backtest-verifier.md`, read first; it
matches the loaded instructions). Scope: branch `w3-wip` at `09b3a50`
(W3 code `66ae89a` and `09b3a50`), base `e739437`. Prereg:
`prereg/W3.md` on master at `ccb5882`. Everything below was measured on
clean `git archive` copies of `e739437` and `09b3a50` and on two file
copies of `C:\GIT\FPL-data` (commit `bd724ca`, nightly 2026-10-19) under
the session scratchpad; `C:\GIT\FPL-data` and the `w3` worktree were
read only (`git status` clean in both before this file was written).
No session transcript or chat log was read. Hashes and key-like strings
are masked to four characters.

## Prereg before code: PASS

`ccb5882` (prereg/W3.md, 2026-10-19 21:30:36 +0200) precedes the first W3
code commit `66ae89a` (22:09:28 +0200). The prereg is on master, not an
ancestor of `w3-wip` (the branch forks from `w2-wip`), which is how the
protocol has worked for every branch item. Its F-B paragraph is
byte-identical to `BUILD_PLAN.md`'s (691 characters); its "RULING 19 Oct
evening" block is byte-identical to the one in `prereg/W2.md` at
`a78e2e7`. No pass/fail metric: W3 is a wiring item, so checks 1, 2, 5,
6, 7 and the item's own acceptance tests apply (check 3 is the
acceptance tests re-run; check 4 is the ruling's presence).

## Claim 1: runner copies by AST, no database, no tools/ (PASS)

My own AST walk (`ast_check.py`, independent of `tests/test_W3.py`):
every top-level function, class and assignment in each runner module is
segment-identical to the tool, apart from the declared hand-written
definitions:

| runner | tool | definitions | identical | hand-written |
|---|---|---|---|---|
| fpl_xpv2 | tools/xp_v2_live | 13 | 8 | PRIOR_FILE, load_prior_file, export_names, live_forecast, record |
| fpl_xpr | tools/xp_v2_replay | 8 | 8 | - |
| fpl_shares | tools/shares | 6 | 5 | Prior (its `prior()` method verbatim: True) |
| fpl_xpv | tools/xp_v2 | 3 | 3 | - |
| fpl_pmf | tools/points_pmf | 31 | 31 | - |
| fpl_mv2 | tools/minutes_v2 | 10 | 10 | - |
| fpl_realised | tools/xp_v2_replay | 2 | 2 | - |

No other top-level statements exist in the copies besides imports and
docstrings. Imports of every runner module touched or added (fpl_xpv2,
fpl_xpr, fpl_shares, fpl_xpv, fpl_pmf, fpl_mv2, fpl_realised, fpl_squad,
fpl_sections, fpl_nightly, fpl_edge, checks, fpl_sync, fpl_lambda,
fpl_hist, fpl_chips, fpl_bt, fpl_league) resolve to the standard library
or repo root modules only; nothing under `tools/`. `sqlite3` is absent
from fpl_xpv2, fpl_xpr, fpl_shares, fpl_xpv, fpl_lambda, fpl_hist and
fpl_edge (fpl_edge imports fpl_xpv2 lazily inside `record_status`).
Dynamic proof: `fpl_xpv2.record` on the real GW8 export in a folder
holding only `odds/` (no fpl.sqlite) returned the same 285 rows and
created no sqlite file. The existing S3 test (the nightly imports nothing
under tools/ or analysis/) is green in the suite.

## Claim 2: prior file and export keys (PASS)

- `python tools/make_prior.py --hist C:/GIT/FPL/historical --check` on
  the clean head copy: "identical to a regeneration", exit 0. File
  110,445 bytes, LF, sha256 `a1d2...`. Its recorded input hashes equal
  my own sha256 of the three files: merged_gw.csv `0d09...`,
  players_raw.csv `412c...`, teams.csv `b29d...`.
- `fpl_shares.Prior(load_prior_file())` against `tools/shares.Prior` on
  the real 2025/26 folder: k, rel, by_name_club (551 entries, same
  order), club_pos, league_pos and clubs all equal; 90,384 queries over
  538 names (one unknown) x 21 clubs (one unknown) x 4 positions x 2
  metrics: 0 mismatches, 0 asymmetric raises.
- `fpl_sync.export` gains `pl.code, pl.first_name, pl.second_name` (diff);
  `tests.test_W3.SyncExport` checks the keys and the fallback name on an
  in-memory database. `export_names` on the real augmented export equals
  `tools/xp_v2_live.prior_names` on fpl.sqlite + elements_positions.csv +
  the 2025/26 files for all 668 players; 481 keyed by code on both sides.
- Note (not W3's doing): the live database has no `code` column and the
  live export no `code` key (W2 is unmerged), so on the raw real data the
  record is `RECORD SKIP xp_v2 the export's all_players has no code (the
  prior's key)`, and CAPTAIN is `SKIPPED` with the same reason; both are
  WARNs by check 29 / 31. After W2+W3 merge the sync supplies the column.

## Claim 3: real GW8 forecast and record (PASS)

Real-data copy, newest export `fpl_export_gw7_2026-10-19.json.gz`
augmented with `code` from `historical/2026-27/elements_positions.csv`
and names from fpl.sqlite (0 players without a code), now =
2026-10-19T23:00Z, deadline 2026-10-23T17:30Z:
- `tools/xp_v2_live.live()` v `fpl_xpv2.live_forecast()`: 285 players
  both, same keys, max |diff| 0.0 and `==` on every value; `detail`,
  `sources` (10 of 10 fixtures "odds"), `snapshot`
  (`odds_2026-10-19T0613Z.json.gz`, taken 06:13Z) and `by_code` (481)
  identical.
- `fpl_xpv2.record`: 285 rows equal to the tool's values rounded to 3
  places (no value <= 0 to drop); note "snapshot
  odds_2026-10-19T0613Z.json.gz, 10 of 10 fixtures from odds; prior
  2025/26 (S11 file), 481 players keyed by code".
- Log regeneration (check 5 below): six sources identical, xp_v2 adds
  285 GW8 rows. Re-measured, matches the implementer's numbers exactly.

## Claim 4: checks and sources (PASS)

Diff: `checks.SOURCES` and `fpl_nightly.SOURCES` both end in `xp_v2`;
`checks.SKIPPABLE = ("fpl_ep", "bottomup_lambda", "xp_v2")`; check 31's
regex is built from the five `SECTION_TITLES`. The W3 test asserts
`C.SOURCES == N.SOURCES` and c29's OK / WARN (skip) / FAIL (fail,
missing) for xp_v2. Mutation m09 (xp_v2 removed from SKIPPABLE) went red.

## Claim 5: report sections (PASS)

- `fpl_sections.TITLES = ("CHIPS", "LEAGUE", "CAPTAIN", "BAN RISK",
  "REALISED")`, run in that order; the W2 amendment 2 loop (MissingInput
  -> SKIPPED, any exception -> SKIPPED `<type>: <message>`) is unchanged
  and now catches fpl_squad / fpl_xpr / fpl_mv2 / fpl_lambda /
  fpl_shares MissingInput too.
- CAPTAIN on the real copy: `fpl_squad.captain` lines [1:] equal the
  lines produced by `points_pmf.captain_table` + `gw_pass.captain_band`
  + `points_pmf.print_options` on `tools/xp_v2_live.live()` (20 lines):
  Saka MID 6.00 P>=10 0.186 P>=15 0.052 p90 12 captain; option Calafiori
  5.83 within 0.3 xP. Captain id 12, options [8]. Its first line names
  the export and the snapshot.
- BAN RISK on the real copy: "none of our 15 is one booking from a ban".
  The pooled position rates from `position_rates` (GK 0.0333, DEF
  0.1811, MID 0.1883, FWD 0.2147 per 90) equal my own SQL over
  player_gw joined to finished league fixtures before the deadline. On
  a planted copy (Brentford's GW7 fixture set `finished = 1`) the line
  for Thiago reads "cautions 4, club match 8 next  rate90 0.447
  P(start) 1.00  P(ban) 0.447", equal to my hand computation of
  m/(m+4) shrinkage and min(1, rate90 x P(start)). Band checks: the toy
  test covers (17,4) in / (18,4) out / (30,9) in / (31,9) out; mutations
  m05 and m06 went red.
  Observation (design, not a defect): the prereg's prose says cautions
  are "in league matches kicked off before the deadline ... as S12's
  rows_2627"; `rows_2627` (copied verbatim) counts only fixtures with
  `finished = 1`. In the 19 Oct database all 10 GW7 fixtures are still
  `finished = 0` although player_gw holds their rows, so Thiago's fourth
  caution (GW7) is not counted tonight and he is not listed. This is
  S12's own rule ("a fixture already kicked off but not finished at data
  time is not a missed match") and resolves as soon as the sync flips
  the flag; it only matters for a nightly that runs during or right after
  the previous gameweek's last match.
- REALISED on the real copy: now before the GW8 deadline -> "no gameweek
  from GW8 has passed its deadline yet"; now = 24 Oct -> "GW8: not locked
  down: not graded (data_checked 0, 0 of 10 fixtures finished)". The toy
  test equates its numbers with `xp_v2_replay.info_2627` (own, own_cap,
  v2, v2_cap) and `recorded` with `recorded_own`; the post-deadline
  xp_v2 row (made 18:00Z on deadline day) is never read (value 15.0, not
  3.0). Mutations m07, m10, m14 went red.
- `fpl_sections.sections` on the augmented copy: CHIPS OK 37 lines,
  LEAGUE OK 69, CAPTAIN OK 20, BAN RISK OK 2, REALISED OK 2; on the raw
  copy CAPTAIN SKIPPED (no code), the other four OK.

## Check 1: point-in-time (PASS)

W3 produces one forecast, xp_v2 for the next gameweek (GW8 tonight), so
the three-gameweek truncation reduces to the one evaluated gameweek plus
the simulated ones.
- (a) Truncation, real GW8: planting GW8 rows into `player_gw_recent`
  (every GW7 row copied with event 8, 30 points, xg 3.0), a GW8 result
  into `fixtures_played` (kickoff 24 Oct) and a snapshot file named
  `odds_2026-10-24T0000Z.json.gz` left `xp` and `detail` unchanged
  (`==`) and the chosen snapshot the 19 Oct one. Simulated GW10/20/38
  (test_fpl's synthetic export at gameweeks 9, 19, 37, with code and
  names): xp_v2 recorded 57 of 57 gated players (status a, 45+ minutes
  in the last four, a fixture) at each, and the rows were unchanged
  after planting target-gameweek rows. Toy test
  `test_target_rows_never_move_the_forecast` is green.
- (b) Timestamp audit, real GW8: export generated 2026-10-19T06:13:10Z
  < deadline; rows read are rounds 1-7 only (max event 7; the export
  carries no later rows and `export_rows` drops any > gameweek);
  snapshot taken 2026-10-19T06:13Z < deadline; 60 results used, latest
  kickoff 2026-10-12T19:00Z, none at or after the deadline; prior season
  2025/26 from the committed file. `canonical_through(d["gameweek"])`
  bounds the reliability inputs; `fpl_edge.forecasts` bounds REALISED's
  rows to the last snapshot before each deadline.
- (c) Shift probe: not applicable (no correlation metric).

## Check 2: clean-checkout suites (PASS)

`python -m unittest discover -p "test*.py"` on `git archive` copies
(the head copy also holds `historical/2025-26` and `2026-27`, copied in):
- e739437 bare: Ran 699, OK (skipped=10).
- 09b3a50 bare (FPL_DATA_DIR unset): Ran 716, OK (skipped=10). Skips:
  4 no real projection_log, 2 no real export, 1 no real fpl.sqlite, 2 no
  tzdata, 1 `test_W3.PriorFile.test_the_committed_file_regenerates_from_
  the_real_files`. The implementer's 11th skip is a test that needs
  `historical/`, which my copy has.
- 09b3a50 with `FPL_DATA_DIR=C:\GIT\FPL-data`: Ran 716, OK (skipped=2,
  the two tzdata skips); the committed prior regenerated from the real
  files inside the suite. `C:\GIT\FPL-data` was clean afterwards.
`tests/test_W3.py`: 17 tests, 1 skipped bare.

## Check 3: acceptance tests re-run (PASS)

(1a) forecast == tool: toy (none / before / after snapshot) in the suite
and real GW8 above. (1b) prior == shares.Prior: toy in the suite, real
files above, `--check` byte-identical. (1c) no database, no tools: above.
(1d) six sources unchanged: check 5. (2) CAPTAIN == gw_pass section 7:
toy in the suite, real GW8 above. (3) REALISED == info_2627: toy in the
suite. Every number I re-measured matches the implementer's (285 players,
max |diff| 0.0, 481 by code, 7,765 unchanged rows, 285 added, 57 of 57,
699 -> 716).

## Check 4: rulings in the prereg (PASS)

F-B verbatim and RULING 19 Oct evening verbatim are in `prereg/W3.md`
(both byte-identical to their sources). No metric, bootstrap or bar to
promote or re-tune; "No re-tuning: W3 ports accepted models and adds no
new model" holds: every model function is a verbatim copy and the
hand-written parts are glue (file loading, key lookup, the record, the
band pinned in the prereg, the pooled position mean pinned in the
prereg).

## Check 5: recording path (PASS)

`record_status` for every source in `SOURCES`, horizon 6, under a frozen
clock (2026-10-19T23:00:00Z, patched into the `datetime` module), on the
same copy of the real log (7,502 lines):
- base code, raw export: own 285, xg 264, minutes 264, bottomup 264,
  fpl_ep 668, bottomup_lambda 264 -> 7,766 lines, 400,138 bytes.
- head code, raw export: the same six lines plus `RECORD SKIP xp_v2`
  (no code) -> byte-identical to the base log.
- base code, augmented export: byte-identical to base/raw (the added
  keys change nothing for the six sources).
- head code, augmented export: the same six plus `RECORD OK xp_v2 285`
  -> 8,051 lines, 414,888 bytes; with its 285 `xp_v2` rows removed it is
  byte-identical to the base log. The xp_v2 rows carry event 8 and the
  frozen made_at only. No sqlite file was created in any run.
- Simulated GW10/20/38: the six sources' rows identical between base and
  head code at every gameweek (own/xg/minutes/bottomup 57, fpl_ep 60,
  bottomup_lambda skip without a snapshot), xp_v2 57.
The real log holds 0 `xp_v2` rows (the item is unmerged).

## Check 6: mutations (PASS, 15 of 16 red; one survivor noted)

Each in its own copy of head, `tests.test_W3` run (plus test_W1/W2 or
test_fpl where the file is shared):
- m01 export_names fallback name order swapped: RED (4 tests)
- m02 record rounds to 2 places: RED
- m03 live_forecast takes a snapshot after the deadline: RED
- m04 export_rows keeps target rows: RED (AST copy test only; `core`
  reads rounds < t, so the planted rows are behaviourally inert)
- m05 ban band not moved one match on: RED
- m06 position mean not per 90: RED
- m07 lockdown guard dropped: RED
- m08 Prior lists without the 180-minute bar: RED
- m09 xp_v2 not SKIPPABLE: RED
- m10 REALISED reads the log without `fpl_edge.forecasts`: RED
- m11 export without `pl.code`: RED
- m12 wrong prior season accepted: RED
- m13 P(start) ignored in P(ban): RED
- m14 REALISED from GW7: RED
- m15 captain tie to the higher id: RED
- m16 `fpl_edge.record_status`'s xp_v2 branch passes `dl + 30 days` to
  `fpl_xpv2.record`: SURVIVED (tests.test_W3 + test_fpl: 403 OK). The
  toy record test holds only a pre-deadline snapshot, so the glue line
  that hands the deadline to the record is untested. No live consequence:
  the record runs only while `now < dl`, so every snapshot and result on
  disk predates the deadline; the guard matters in the replay paths,
  which stay in tools/. A one-line test (a post-deadline snapshot in
  `test_the_record_rows_and_skips_without_a_database`) would close it.

## Check 7: secrets (PASS)

The 20 files W3 adds or changes contain no `apiKey=`, no Authorization
header value and no key-like string; the only long hex strings are the
three SHA-256 input hashes in the prior file (masked above).

## Other checks

- Standard library only: PASS (import audit above).
- Hermetic tests: PASS. `tests/test_W3.py` uses `tempfile.mkdtemp`
  folders, `mock.patch.object(fpl_xpv2, "PRIOR_FILE", ...)`, aware
  datetimes, and `os.chdir` restored in `finally`; the one
  environment-dependent test is skip-guarded on `FPL_DATA_DIR` and
  `historical/2025-26` and reads repo files only. No git config, time
  zone or locale dependence.
- Write guard from my side: only this file was written in the worktree;
  everything else went to the session scratchpad. `C:\GIT\FPL-data` was
  never written (its `git status` is clean).
- Open design question (the committed prior file and the export's new
  keys) is Boris's, as the prereg says; W3 does what the prereg
  pre-registers.

VERDICT: PASS

Reason: the prereg (with F-B and the 19 Oct evening ruling verbatim)
precedes every W3 commit; every copied definition is segment-identical to
its tool and the runner imports nothing under tools/; the committed S11
prior regenerates byte for byte and answers 90,384 real queries exactly as
the tool; on the real GW8 inputs the runner's forecast equals the tool's
(285 players, max |diff| 0.0, detail and lambda sources identical) and the
record never opens the database; under a frozen clock the six existing
sources' 7,765 regenerated rows are byte-identical between base and W3
code while xp_v2 adds 285 GW8 rows (and 57 of 57 at simulated
GW10/20/38); planted post-deadline rows, results and snapshots never move
the forecast; CAPTAIN equals gw_pass section 7, BAN RISK's pooled rates
equal an independent SQL and its planted line equals a hand computation,
REALISED obeys the lockdown guard and pre-deadline rows; the suites are
699 -> 716 OK on clean copies; 15 of 16 mutations went red, the survivor
being an untested glue line with no live effect; no secrets. The two
notes (the finished-flag semantics of S12's caution count, and the m16
coverage gap) are information for the main session, not defects against
the prereg.
