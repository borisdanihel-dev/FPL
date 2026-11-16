# Verifier report: S8c amendment 4 (the bundle's "if he plays" block)

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high.
Instructions read from `.claude/agents/backtest-verifier.md` on disk first.
Date: 2026-10-20 (UTC evening). Item type: offline tools work, information
only (no pass/fail metric in the prereg): checks 1, 2, 5, 6, 7 plus the
item's own acceptance tests, and the caller's seven specific checks.

Reviewed: `git diff 3750334 4d4bfa9` on `s8c-wip` (origin/s8c-wip holds
4d4bfa9; parent 3750334, the verified bundle commit). Files: `tools/gw_pass.py`
(+60), `tools/xp_v2_live.py` (+8/-4), `tests/test_S8c.py` (+109). Nothing
else.

Prereg: `prereg/S8c.md` "## Amendment 4" on master, commit 6a46a79
(2026-10-20 21:12:32 +0200), with the ruling "Ruling, Tue 20 Oct, 21:00
Prague" verbatim (points 1-3; point 2 is this item). The code commit 4d4bfa9
is 2026-10-20 21:21:06 +0200: prereg before code. PASS.

Real data: `C:\GIT\FPL-data` at 63e6a44 (read-only; nothing written there;
no API calls; `ODDS_API_KEY` unset in every run). Scratch:
`.../scratchpad/v8c_a4/` (clean `git archive` of 3750334 in `before/`, of
4d4bfa9 in `after/`; mutants in `mut/`; my script `recompute.py`, its
output `recompute.log`; bundle runs `run_before/`, `run_after/`).

## Caller's check 1: only the status gate is lifted, for that player only

- `lift` empty changes nothing: `XL.live(..., lift=())` equals the plain
  call in `xp` and `detail` (True). Every existing caller (tests/test_S14,
  tests/test_S6d, tools/gw_pass.py:411, tools/points_pmf.py:573) passes no
  `lift`; the default is `()`. Real data: `xp_v2_all.csv` byte-identical
  before/after (sha256 d8ba0bff... in both my runs and in both of the main
  session's runs); `gw8_pass.txt` before/after differs only in the line-1
  stamp and the three inserted lines (diff `208a209,211`).
- With `lift=(411,)` (Haaland) on the real GW8 data: every other player's
  `xp` and `detail` identical (277 players; True/True); the lifted dict is
  the base dict plus Haaland.
- Independent recompute: I rebuilt `forecast()`'s inputs myself (export,
  snapshot odds_2026-10-20T1301Z, prior, names, `_model`, training slice
  through GW7) and called `core` directly with a gate dict I built
  (`status == "a"`, then `gate[411] = True`): Haaland xp_v2
  4.250027371513 vs the tool's lifted 4.250027371513, diff 0; the whole
  dict equals the tool's lifted dict; minus Haaland it equals the base.
- P(start) 0.75 is the existing input `inp["players"][411]["p_start"]` =
  `start_probability({starts_last4: 4, chance_next_round: 75}, 7)` =
  1.0 x 0.75 (fpl_edge.py:1180, untouched by the diff: `git diff
  --name-only` holds no fpl_edge.py). P(sub) 0.00 = raw `sub_inputs_2526`
  0.000000 x chance 0.75 (core line 116, unchanged). On the real data no
  status-'a' player has chance < 1, so the scaling is exercised only by the
  toy test (0.4 x 0.75 = 0.3; mutant m4 below goes red).
- Printed: `xp_v2 4.25 (P(start) 0.75, P(sub) 0.00 scaled by chance)`. PASS.

## Caller's check 2: own

- `fpl_edge.record_status`'s own branch gate is the one line
  `if p["status"] != "a" or p["mins_last4"] < 45: continue` (the same line in
  the minutes, xg and own branches; shown from source), then
  `sum(project(p, {team: [f]}, horizon, d["gameweek"], priors, personal)[0]
  for f in fx)` over the target's fixtures. `gw_pass.own_if_plays` is that
  computation with only the status part lifted (minutes part kept,
  horizon 6 = `fpl_edge.py --horizon` default 6; the nightly calls
  `--record --source <src>` with no horizon).
- Independent recompute: a deep copy of the real export with Haaland's
  status set to 'a', run through the real `record_status(d2, 6, "own",
  path=<temp log>)`: Haaland's own row 4.44 (3 dp); `own_if_plays` gives
  4.439780 -> printed 4.44; equal at 3 dp. The unlifted export through the
  same branch holds no Haaland row and its 277 rows equal the real
  `projection_log.csv` own rows for GW8 at snapshot 2026-10-20, 277 of 277;
  the lifted copy's other 277 rows are identical to those.
- S9 captain table "Haaland own 4.44": not present in the data
  (`reports/fpl_2026-10-20.txt` and the bundle's S9 table list our XI by
  own; Haaland has no own row because of the gate). Nothing to compare
  there; the record-branch recompute above is the check. PASS.

## Caller's check 3: the captain table place

`PM.live_pmfs` on the full lifted forecast gives Haaland mean
4.250027371512857, P>=10 0.1260, P>=15 0.0246, p90 10; identical to the
one-player dict the tool passes. Inserted into section 7's sums and sorted
by `-mean` (the captain table's own sort, section 7 printed from my run:
Saka 6.05, Calafiori 5.82, Mbeumo 5.66, Muharemovic 5.00, Thomas 4.91,
Thiago 4.78, Rudoni 4.71, Gross 4.47, [Haaland 4.25], Barry 4.18, ...):
place 9 of 15; no other squad mean within 1e-9 of his. PASS.

## Caller's check 4: the print

Block at the end of section 5, after the "9 slots differ; the XI differs;
..." line, before the blank line and section 6 (lines 209-211 of my
`run_after/gw8_pass.txt`). The rest byte-identical: my before/after diff is
exactly the line-1 stamp plus `208a209,211`; my after print minus line 1
is byte-identical to the main session's `s8c_a4_live/gw8_pass.txt` minus
line 1, and my before print likewise to `s8c_a3_live`. The toy tests cover
no flagged player = no block (`test_no_flagged_player_no_block`) and the
rest-identical/CSV-identical case. PASS.

One wording deviation from the prereg: the header line ends with
" (Ruling, Tue 20 Oct, 21:00 Prague, point 2)", which the prereg's header
text does not have. Information only; noted, not blocking.

## Check 1 (point-in-time)

GW8 is unplayed; the block is information only and nothing is recorded, so
there is no evaluated gameweek for a truncation test or a shift probe.
Timestamp audit: the export `fpl_export_gw7_2026-10-20.json.gz` was
generated 2026-10-20T13:01:33Z, the odds snapshot is 2026-10-20T13:01Z, the
training slice is `canonical_through(..., 7)` and `player_gw_recent`'s
max event is 7; the GW8 deadline is 2026-10-23 17:30 UTC. `live()` raises
on an export generated at or after the deadline (unchanged). PASS.

## Check 2 (clean-checkout suites)

`git archive` copies, keys removed (`ODDS_API_KEY` unset), `python -m
unittest discover -p "test*.py"`:
- before 3750334, bare: Ran 768, OK (skipped=10).
- after 4d4bfa9, bare: Ran 773, OK (skipped=10).
- after 4d4bfa9, `FPL_DATA_DIR=C:/GIT/FPL-data`: Ran 773, OK (skipped=3).
+5 = the `IfHePlays` class. PASS.

## Check 5 (recording path)

No runner file in the diff (tools/ and tests/ only), so the projection log
cannot have moved; the real `record_status` own branch, run by me on the
unlifted export to a temp log, reproduces the real log's 277 GW8 own rows
exactly (above). I did not run `--record` against the data (the runner is
the only writer). PASS.

## Check 6 (mutations, mine, in scratch copies of 4d4bfa9; `tests.test_S8c.IfHePlays`)

| id | mutation | result |
|---|---|---|
| m1 | lift leaks: `if lift: gate = {k: True for k in gate}` | RED (test_the_lift_changes_only_that_player: the other flagged player appears) |
| m2 | lift ignored (`pass`) | RED (test_the_lift..., test_the_block) |
| m3 | own: `project(..., d["gameweek"] + 1, ...)` | RED (test_own_is_the_record_branch) |
| m4 | P(sub) unscaled under lift (`chance = None if lift else ...`) | RED (test_the_lift...: 0.4 vs 0.3) |
| m6 | block printed before the "slots differ" line | RED (test_the_block) |
| m7 | header printed with no flagged player | RED (test_no_flagged_player_no_block) |
| m8 | place `+ 2` | RED (test_the_block) |
| m9 | "no xp_v2 even if he plays" branch always taken | RED (test_the_block) |
| m3b | own's minutes gate removed from `own_if_plays` | survives (no toy squad player under 45 minutes) |
| m5 | captain sort by `xp` instead of `mean` | survives (equivalent: the PMF's mean is xp_v2 by construction, S14 option (a)) |

Eight of ten red, including the lift leak and own's gate/inputs. m5 is not
a behaviour change. m3b is a coverage gap: the prereg says own's "minutes
part stays" and no test pins it; the real-data value is unaffected
(Haaland mins_last4 349). Noted, not blocking. PASS.

## Check 7 (secrets, runner isolation)

`git diff 3750334 4d4bfa9` grep for apiKey/api_key/Authorization/Bearer/
32-hex strings: none. Changed files are under tools/ and tests/ only;
`fpl_nightly.py` has no tools/analysis import;
`tests/test_S3.FastTrack.test_the_nightly_imports_nothing_under_tools_or_analysis`
is in the green suites. `ODDS_API_KEY` was unset in every run. PASS.

## Item's own acceptance tests versus the prereg's list

Present: a flagged toy squad player (status d, chance 75, news); the
values (xp_v2, P(start), P(sub) scaled, own, place, PMF summary); the rest
byte-identical with the block removed vs switched off (`if_he_plays`
mocked to `[]`); the CSV byte-identical; no flagged player, no block; own
against the recorded row for an unflagged player. Gap: the prereg's "the
lifted value to `core` with that one gate flipped" is not asserted
directly in the test (the test checks the other players, P(sub) and the
P(start) input); I made that comparison myself on the real data (diff 0).
Noted, not blocking.

Other notes (information only, no change asked): the "no xp_v2 even if he
plays" reason reads the export's `mins_last4` while `core` gates on the
canonical slice's `mins_last4`, and a player absent from `inp["players"]`
would be reported as "no GW fixture"; the main session's GW8 run
(`s8c_a4_live/run.txt`, commit 4d4bfa9, 0 modified files) matches mine.

VERDICT: PASS. The lift sets one player's status gate and nothing else (every other value identical with and without it on the real data and in the test; my own `core` call with Haaland's gate flipped reproduces 4.250027371513 exactly, P(start) 0.75 and P(sub) 0.00 x 0.75 are the existing inputs); own 4.44 is the real `record_status` own branch on a status-lifted copy (horizon 6; the unlifted branch reproduces the real log's 277 rows); the captain place 9 of 15 follows from section 7's PMF summary and sort; the block sits at the end of section 5 and the rest of the print and the CSV are byte-identical before and after on the real data and in the tests; clean suites 768 -> 773 OK (bare and with the data); 8 of 10 mutants red; no runner file, no secret. Two non-blocking notes: the header carries a ruling citation the prereg's text does not, and own's minutes gate in `own_if_plays` has no pinning test.
