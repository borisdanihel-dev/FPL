# verify_S7 — backtest-verifier report (first run + amendment run)

## First run (2026-10-18, commit eb585b5; verdict stands)

Verified S7 at eb585b5 (code d0fc715): **VERDICT PASS**. The prereg and its
amendment 1 were committed before any code and hold the ruling verbatim; the
replay's forecasts and chip values rebuilt with zero difference from inputs
truncated at origins 5, 12 and 19; no training row or live own row was dated
after its deadline; my own replay reproduced the implementer's final output
byte for byte (calculator 16.56, heuristic 16.74, both-early 10.80; paired
gain -0.18, 90% CI [-1.26, +0.72], pre-registered bar FAIL, reported without
tuning); the metric, sample, bootstrap (squad unit, B = 10,000, 90%, seed
20261018) and bar (mean >= 0 and lower bound > -3) were exactly the prereg's;
no runner file changed; 15 of 18 mutations went red (the three survivors M14,
M15, M18 were test gaps, not defects); no secrets. Four readings were flagged
for the chat, none moving a bar: (1) the V_BB wording slip in the prereg's
acceptance test 1 (code follows BUILD_PLAN and the ruling: Σ xP × (1 - w)
everywhere); (2) the tie rule "a tie goes to playing, BB before FH" declared
in code, not in the prereg; (3) the "margin" implemented as chosen action
minus the best other action (+0.07) rather than vs HOLD (+0.13); (4) the
replay's secondary margin interval not printed. Those four readings stand.

## Amendment run (RULING S7 result, points 2-3)

Repository C:\GIT\FPL-b, branch lane-b, verified at HEAD 876d6a4 (ruling
commit d9c36e4, amendment code 41ff6b4; 39a5b88 and 876d6a4 are the main
session's CHANGELOG/worklog commits, df5d5fa the S5 odds CSVs, none touching
tools/chips.py, tests/test_S7.py or prereg/S7.md: `git diff 41ff6b4..HEAD
--stat` on those three is empty). Verifier model: Fable 5.1
(claude-fable-5-1), effort high; .claude/agents/backtest-verifier.md read
from disk first, identical to the loaded instructions. Data read-only from
C:\GIT\FPL-data (HEAD e8629f0 "nightly 2026-10-18", status clean before and
after) and C:\GIT\FPL-b\historical\2025-26; my outputs under
tools/out/verify_s7_amend/ (git-ignored by /tools/out/) and the session
scratchpad. No key-like strings occur in any file or output examined
(nothing to mask).

### Prereg before code — PASS

- "Ruling on the result (verbatim)" with "RULING S7 result:" points 1-4 and
  "END RULING" is present in prereg/S7.md, committed d9c36e4 at 2026-10-18
  22:14:35 +0200 (prereg/S7.md only, +15 lines); the amendment code 41ff6b4
  at 22:19:15 +0200 (tests/test_S7.py +64/-13, tools/chips.py +77/-29, no
  other file). Ruling before code: confirmed by the git order.
- The header above the ruling states the bar, metric, sample and seeds are
  unchanged and that points 2-3 add outputs only. The diff 23825fe..41ff6b4
  of tools/chips.py confirms it: SEED = BT.SEED (20261018), BT.B = 10000,
  BT.CI = 0.90, PASS_LOWER = -3.0, N_SQUADS = 50, SQUAD_SEED = 7,
  REPLAY_FIRST = 5, LAST_GW = 19, the primary bootstrap lines (b1, b2), the
  bar line and the first eight printed lines are untouched; the only changes
  are `fixtures_ticker`, the `tick`/`weeks` arguments to `own_week_points`,
  the removal of the proxy block in `live()`, the two added policies and
  their information-only print block in `replay()`.

### Check 1 — point-in-time leak check

#### 1a Truncation / independence test (decides) — PASS

Live path (scratchpad before_after.py, both clean archives loaded
in-process, `live(resamples=1)`): V_BB and V_FH for GW8-13 are identical at
full precision between the pre-amendment code (23825fe) and the amendment
(41ff6b4), worst difference 0.0 (e.g. GW8 V_BB 6.65649 / V_FH 5.785; GW13
V_BB 6.272885261506394 / V_FH 5.730062839489001; V(8, BB+FH)
12.386552839489001 both). In the text files, GW8-11 rows are unchanged; GW12-13
differ only in the continuation columns V(BB) / V(BB+FH) and the action
(6.27/12.00 -> 6.44/12.17), which now carry the real GW14-19 values instead
of the proxies; the 2-dp V_BB, V_FH, ours XI and FH XI columns are equal to
the last digit for GW8-13. No `proxy` key remains in `detail`; v_bb holds
GW8-19.

Fixtures (scratchpad fix_q.py, my own sqlite query): fpl.sqlite's fixtures
table holds 380 rows, none with a null event or team; GW8-19 have 120 rows,
10 per gameweek, 20 teams, no blank or double week. The ticker built by
`chips.fixtures_ticker(data, 8, 19)` equals my independent rebuild from
`select event, team_h, team_a, team_h_difficulty, team_a_difficulty` joined
to `teams.short_name` (dict equality True, 20 teams, e.g. ARS GW8 'EVE (H)'
3 ... GW19 'IPS (H)' 2), and for GW8-13 it equals `fpl_edge.build_ticker`
on the export's fixtures_next6 (0 mismatches). `own_week_points` on my
independent ticker gives the same weeks, the same pts (worst diff 0.0) and
the same src map as on the item's ticker; on the export's six-week ticker
the GW8-13 values differ by 0.0.

Replay: the two new policies read nothing new. "late" uses fixed weeks
(last-1, last); "bb_first_fh_heur" calls `heuristic_action` on the same
`bench_sum` and `v_fh` from `rp.values(squad, t)` that the first run's 1a
test showed to be invariant to every row with round >= t (max abs diff 0.0
at origins 5, 12, 19). The forecast path is unchanged (diff), so the first
run's truncation result stands for the amended replay.

#### 1b Timestamp audit (decides) — PASS

Scratchpad audit_1b.py: export fpl_export_gw7_2026-10-18.json.gz (the newest
dated file in exports/) generated 2026-10-18T18:45:03+00:00, GW8 deadline
(events.deadline_time) 2026-10-23T17:30:00Z: before. Projection log 5,756
rows, 0 with made_at at or after the deadline. Own GW8 rows: two snapshots
(2026-10-17T22:04:06 275 players, 2026-10-18T18:45:03 285 players);
`own_week_points` uses 285 'own' rows for GW8, exactly the last pre-deadline
snapshot's player set with max abs diff 0.0 against its `predicted` values.
GW9-19 all 'own-model' 285 / 'gate' 383 from the same export via
`fpl_edge.project()` on that week's fixtures. The fixtures rows come from
fpl.sqlite at data HEAD e8629f0 (nightly 2026-10-18, before the deadline).
GW8's kickoffs run 2026-10-23T19:00Z to 2026-10-25T16:30Z; events 7-9 have
data_checked 0 (nothing graded in the future).

#### 1c Shift probe — not applicable

The metric is realised chip points, not a correlation of forecasts with
points; as in the first run, the S4 probe on the `bottomup` source stands.

### Check 2 — clean-checkout test runs — PASS

Clean archives (`git archive`) in the scratchpad, FPL_DATA_DIR unset:
- before (23825fe): `python test_fpl.py` Ran 386, OK (skipped=8);
  `python -m unittest tests.test_S7` Ran 13, OK.
- after (41ff6b4): `python test_fpl.py` Ran 386, OK (skipped=8);
  `python -m unittest tests.test_S7` Ran 13, OK.
Matches the implementer's 386 OK (8 skipped) and 13 OK.

### Check 3 — re-run of the evaluation — PASS

- Replay: `python tools/chips.py --replay --out tools/out/verify_s7_amend`
  (my run, 22:20-22:27). tools/out/verify_s7_amend/chips_replay_2025-26.txt
  (11 lines, 1,448 bytes) is **byte-identical** (`cmp`) to the implementer's
  tools/out/amend/chips_replay_2025-26.txt (whose replay_run.log ends "AMEND
  REPLAY DONE" and equals the file modulo CRLF). Its first 8 lines are
  **byte-identical** to the first run's tools/out/final/chips_replay_2025-26.txt
  and to my first-run tools/out/verify_s7/chips_replay_2025-26.txt: the
  pre-registered lines did not move (calculator 16.56, heuristic 16.74,
  both-early 10.80; -0.18 [-1.26, +0.72], FAIL; chip weeks and BB/FH splits
  unchanged). Note: tools/out/chips_replay_2025-26.txt (1,062 bytes at
  21:18) was overwritten by the main session at 22:24 with the amended
  11-line content; it now equals the amend file, so its first 8 lines are
  still the first run's text (checked).
- Comparators (information only, printed under the table), reproduced
  exactly: both-late (FH GW18, BB GW19) mean -7.90 per squad (BB +2.40,
  FH -10.30), calculator - it +24.46 [+18.96, +30.06], heuristic - it
  +24.64 [+19.16, +30.10]; BB GW5 + FH by the heuristic mean 16.64 (BB
  +2.60, FH +14.04), calculator - it -0.08 [-1.26, +0.96], heuristic - it
  +0.10 [-0.90, +1.02]. Arithmetic ties: 16.56 - (-7.90) = 24.46, 16.74 +
  7.90 = 24.64, 16.56 - 16.64 = -0.08, 16.74 - 16.64 = +0.10, 2.40 - 10.30 =
  -7.90, 2.60 + 14.04 = 16.64; the BB-at-GW5 gain +2.60 equals the
  both-early policy's, as it must (same squads, same week).
- Live: `python tools/chips.py --out tools/out/verify_s7_amend` gives a
  chips_live.txt **byte-identical** to tools/out/amend/chips_live.txt: GW8
  PLAY BB, margin +0.07 over the best other action, residual pools GK 62 /
  DEF 301 / MID 368 / FWD 82, 1,000 resamples 90% [-22.77, +3.30], same
  action in 10%; every row GW8-19 'own'/'own-model', no proxy; bench prep
  for GW8 and the Free Hit screen as before. The margin still ties to the
  table: V(8, BB+FH) 12.39 - (PLAY FH 5.79 + V(9, BB) 6.53 = 12.32) = 0.07.
  The implementer's table in worklog/cc_2026-10-18_S7.md matches line for
  line.

### Check 4 — metric, filter, bootstrap, bar as pre-registered — PASS

The primary metric, the 50-squad seed-7 sample, origins GW5-19, the
`bottomup` forecasts, the heuristic, the bootstrap (squad unit, B = 10,000,
90% percentile, seed 20261018) and the bar (mean >= 0 and lower > -3) are
untouched by the diff and reproduce byte for byte (check 3). The ruling on
the result is in prereg/S7.md verbatim with "END RULING", committed before
the amendment code; its point 1 accepts the FAIL and says the numbers stand
as first printed, which they do. The two comparators are labelled
"information only (RULING S7 result point 3)" in the output and carry no
bar; the ruling's weeks (FH GW18, BB GW19; BB GW5) are the code's `last - 1`,
`last`, `first` with REPLAY_FIRST = 5 and LAST_GW = 19. No metric promoted,
no re-tuning: the headline in the report and CHANGELOG remains the primary
metric's FAIL. The first run's four flagged readings are unchanged by the
amendment and still stand as information for the chat.

### Check 5 — recording path — PASS

md5 of fpl_edge.py, fpl_hist.py, fpl_nightly.py, fpl_sync.py, fpl_gate.py,
fpl_publish.py, fpl_ship.py, checks.py, fpl_alert.py, test_fpl.py,
tools/backtest.py and .github/workflows/nightly.yml identical between
23825fe and 41ff6b4 (e.g. fpl_edge.py 64e960546ec5 both). Nightly
isolation: importing fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate,
fpl_publish and fpl_hist loads no module under tools/ or analysis/ (empty
list); no runner file imports tools/analysis/chips/backtest; the workflow
references neither folder. With the recording code byte-identical the
projection log cannot move; it was not regenerated locally (the runner is
the only writer, `--record` never run here) and the data worktree is
untouched (status clean, HEAD e8629f0 before and after every run).

### Check 6 — mutation spot-check — PASS (10 of 11 red)

One-line mutations on a scratch archive of 41ff6b4 (scratchpad mutate.py;
the repository untouched; scratch file restored byte-identical, md5
checked), `python -m unittest tests.test_S7` after each (baseline 13 OK):
- A missing-gameweek check dropped: RED (own_week_points test).
- B home FDR read from the away column: RED (own_week_points test).
- B2 home/away labels swapped: RED (own_week_points test).
- C live back on the export's six weeks (proxy path reintroduced): RED
  (live_runs_and_labels, cli_and_isolation).
- D live budget read from `value` (first run's M14): RED (live labels).
- E heuristic fed the weighted V_BB (first run's M15): RED (replay spy).
- F both-late plays FH in the last week: RED (replay test).
- G BB-first plays BB in the second week: RED (replay test).
- H comparators' bootstrap seed drifted: RED (replay seed spy).
- I primary bootstrap seed drifted (first run's M18): RED (replay seed spy).
- J ticker left unsorted: SURVIVED (the toy's rows are inserted in gameweek
  order, so sorting is a no-op there; the code sorts; a test gap, not a
  defect).
The three first-run survivors (M14, M15, M18) now go red, as the
implementer's report claims.

### Check 7 — secrets — PASS

`git diff 23825fe..HEAD` (CHANGELOG.md, prereg/S7.md, tests/test_S7.py,
tools/chips.py, worklog/SESSION_STATE_B.md, worklog/cc_2026-10-18_S7.md and
the S5 odds CSVs tools/odds/E0_*_fetched_2026-10-18.csv) and the outputs
tools/out/amend/*.txt: no API key, no URL with apiKey=, no Authorization
header value (grep for apikey=, api_key, authorization:, bearer, sk-..,
32-hex: no match). chips.py opens fpl.sqlite read-only (`mode=ro`) and has
no network code.

### Acceptance tests of the amendment (the ruling's points 2-3)

- Point 2, no proxy weeks: `fixtures_ticker` reads GW first..19 from the
  fixtures table in `build_ticker`'s shape; every week GW8-19 is projected
  by the `own` formula on its real fixtures (1a/1b above); a gameweek
  without fixture rows raises MissingInput (tested with 8..25, mutation A
  red); the table carries no proxy row and says "no proxy weeks". PASS.
- Point 3, comparators on the same replay, seed and squads: both policies
  run inside the same squad loop on the same `rp.values` and the same
  bootstrap seed (spy test, mutations H/I red); printed under the existing
  table; the pre-registered lines byte-identical (check 3). PASS.
- Tests (13): the database ticker equals the export's for GW8-10, a missing
  gameweek refused, no proxy rows, the live budget equals
  `fpl_edge.selling_budget` (99.7, never value 100.2) and every FH XI fits
  it (costs 91.2-97.8 on the real export, checked by me in-process), the
  heuristic receives the unweighted bench sum, the bootstrap seed is
  BT.SEED, the comparators' chip weeks on the toy ({FH: 5, BB: 6}; BB at 5).
  PASS.

### Other findings (information)

- GW8 PLAY BB by +0.07 xP with 10% resample agreement (18% before the
  amendment: the real GW14-19 values add alternatives) is information only;
  the chip call is the chat's at Thursday's deadline pass (ruling point 4).
- The working tree held three uncommitted main-session files (CHANGELOG.md,
  worklog/SESSION_STATE_B.md, worklog/cc_2026-10-18_S7.md) when I started;
  they were committed as 39a5b88 and 876d6a4 during this run. My run
  changed nothing in the repository except this file; tools/out/ is
  ignored.

VERDICT: PASS

Reason: the ruling on the result is in prereg/S7.md verbatim and was
committed (d9c36e4) before the amendment code (41ff6b4); the amendment
leaves the pre-registered metric, sample, seeds, bootstrap and bar untouched
and the first eight replay lines byte-identical to the first run, while my
own replay and live runs reproduce the implementer's amended outputs byte
for byte; the live GW8-13 chip values are unchanged at full precision, the
fixtures for every week GW8-19 equal my own query of fpl.sqlite's 120 rows
and the export's six, and every input (export 18:45Z on 2026-10-18, the last
pre-deadline own snapshot, the data-branch fixtures) predates the GW8
deadline; clean-archive tests are 386 OK (8 skipped) plus 13 OK before and
after, no runner file changed and the nightly imports nothing under tools/,
10 of 11 mutations go red including the first run's three survivors, and no
secrets occur. The first run's verdict and its four flagged readings stand;
the two comparators are information only, as the ruling says.
