# Verifier report: S6c (xp_v2 as tested against own_rebuilt; the 2026/27 GW5-7 print)

Verifier: backtest-verifier agent on **Fable 5.1** (claude-fable-5-1), effort high, as
`.claude/agents/backtest-verifier.md` (read from disk first; it matched the loaded
instructions). Date 2026-10-19. Repository `C:\GIT\FPL`, branch `s6c-wip`, HEAD `28d0578`.
Written only this file. Every re-run, mutation and recording test was made in a scratch
folder outside the repository (`git archive` copies of `d662656` and `28d0578`); the data
worktree `C:\GIT\FPL-data` (data commit `bd724ca`) was read only (`fpl.sqlite` opened
`mode=ro`). `git status` of both worktrees is unchanged at the end.

## Preliminaries

- `prereg/S6c.md` committed in `d662656` (2026-10-19 14:55:07 +0200); the first code commit
  is `11c262c` (15:02:21 +0200). The prereg has exactly one commit; it was not edited after
  the results existed (`tools/out/s6c/run.txt`: start 13:10:20 UTC, commit `28d0578`,
  0 modified tracked files).
- The ruling text is present verbatim in `prereg/S6c.md` (RULING S6b acceptance + lanes
  merge, points 1-4, END RULING) with Boris's queue line.
- `git diff --name-only e534200..28d0578` = `prereg/S6c.md`, `tests/test_S6c.py`,
  `tools/xp_v2_replay.py` only. No runner file changed. The runner modules
  (`fpl_nightly.py`, `fpl_sync.py`, `fpl_edge.py`, `fpl_publish.py`, `fpl_gate.py`,
  `fpl_ship.py`, `fpl_alert.py`, `fpl_odds.py`, `checks.py`, `p1_eval.py`) import nothing
  under `tools/` or `analysis/`; the nightly workflow runs only `fpl_nightly.py`,
  `fpl_publish.py` and `fpl_alert.py`.
- Input SHA-256s, recomputed, equal the claims: players_raw `412ce017...`, 2024-25 merged_gw
  `5bbbcba6...`, fixtures `ce696e18...`, teams `d10a6db8...`, game_config `a72a9908...`,
  elements_positions `ac3dc891...`; 2025-26 merged_gw `0d09f1f1...`, fixtures `2d7e3950...`,
  teams `b29df099...`; odds file `3e3a8352...` (tracked in git, the same bytes in the
  scratch copy).

## own_rebuilt against live own's formula (prereg "Definitions pinned")

Read side by side with `fpl_edge.record_status` (the `else:` branch, source own) and
`fpl_edge.project`:

| live own | own_rebuilt (`Replay.own_rebuilt`) |
|---|---|
| gate `status == 'a' and mins_last4 >= 45` | status set `"a"` for all; `mins_last4 < 45` skipped |
| `fx = tick[team]` of the target; none -> no forecast | `s11.club_fixtures(team, t)` (S5's fixture table, the one xp_v2 uses); none -> skipped |
| `sum(project(p, {team: [f]}, horizon, d["gameweek"], priors, personal)[0] for f in fx)` | `sum(project(p, {team: [(t, label, fdr)]}, 6, t-1, priors, personal)[0])` per fixture |
| `fdr` = `h_fdr` for the home side, `a_fdr` for the away side; `fdr_avg(...) or 3.0` | `f["fdr_h"] if home else f["fdr_a"]`, `or 0.0` -> `project`'s `or 3.0` |
| `pts_last4`/`mins_last4` = `player_gw` `event BETWEEN gw-3 AND gw`, gw = last played | `last4(train rows, t-1)`: rounds t-4..t-1 of the training slice (official points and minutes) |
| `gws_played = d["gameweek"]` | `t - 1` |
| `positional_priors(d["all_players"])` | `positional_priors` over every harness player at origin t |
| `personal_priors(d)`: `player_history` with `minutes >= 450`, keyed by `web_name`, first in id order wins a shared `web_name` | history built per harness player whose full name matches one 2024/25 element (manager rows out), `>= 450` minutes, keyed by 2025/26 `web_name`, listed in id order; the same `personal_priors` |
| `if proj > 0: round(proj, 3)` | the same |

Independent hand recomputation on real data (scratch `hand_check2.py`, reading the CSVs
directly and writing out `project`'s arithmetic, players at one club all season): GW5 337 of
342, GW21 313 of 319, GW38 320 of 334 players recomputed, **0 mismatches** at any of the
three origins; every player under 45 minutes absent. (A first pass that resolved the
personal prior by full name showed a few mismatches - Henderson, Gomez, James, Wilson,
Martinez - all explained by live's `web_name` keying: a 2025/26 player sharing a `web_name`
with one who has a 2024/25 row gets that row's prior, exactly as `fpl_edge.personal_priors`
does for live own. own_rebuilt reproduces live here; noted as an observation, not a
departure from the prereg, which pins the web_name key "as the export lists it".)

The lacks are stated: `OWN_REBUILT_LACKS` names the pre-deadline FDR, status and
chance_next_round (taken as available), personal priors before 2024/25, and full-name
identity for the personal prior; it is printed on the line after the header that names
own_rebuilt.

## Check 1: point-in-time leak check - PASS (a, b); no WARN (c)

Scratch `pit_check.py` against the `28d0578` copy.

**1a Truncation test (decides): PASS.** For t = 5, 21, 38 a scratch copy of
`historical/2025-26` was built with rows of round t numerically scrambled (every non-identity
column replaced by random integers), rows of rounds > t removed, and `fixtures.csv` scores of
events >= t scrambled; then `own_rebuilt(t)` and `xp_v2(t)` were rebuilt on it and compared
with the full-data values.

| t | rows kept (round < t) | scrambled (round = t) | dropped (round > t) | own_rebuilt | xp_v2 |
|---|---|---|---|---|---|
| 5 | 2852 | 742 | 26163 | n=342, max diff 0.000e+00 | n=342, 0.000e+00 |
| 21 | 14975 | 795 | 13987 | n=319, 0.000e+00 | n=319, 0.000e+00 |
| 38 | 28916 | 841 | 0 | n=334, 0.000e+00 | n=334, 0.000e+00 |

Key sets identical, every value identical to the bit.

**1b Timestamp audit (decides): PASS.** For every origin t in 5..38, every training row
(round < t) in `merged_gw.csv` has `kickoff_time` before round t's deadline (first kickoff of
round t minus 90 minutes): 0 violations (no postponed fixture is labelled an earlier round
and played after a later origin's deadline). The 2024/25 prior file and the 2025/26 web
names are season-level inputs; the end-of-season FDR is the prereg's pinned, stated lack.
The 2026/27 print: GW5's snapshot 2026-09-17T21:55:18Z precedes the deadline
2026-09-18T17:30:00Z, GW6's 2026-10-09T21:50:35Z precedes 2026-10-10T10:00:00Z (events table
of the data worktree); each gameweek has exactly one own snapshot before its deadline.

**1c Shift probe (warns only): no WARN.** Pooled Spearman of the forecast against the
re-scored points among players with 60+ minutes in both g and g+1, g = 5..37 (n = 4977):
own_rebuilt unshifted 0.0379, shifted 0.0085 (diff +0.029); xp_v2 unshifted 0.1224, shifted
0.0858 (diff +0.037). Both under the 0.25 and 0.10 limits.

## Check 2: clean-checkout test run - PASS

`python -m unittest discover -p "test*.py"` in `git archive` copies, no `FPL_DATA_DIR`:

- before (`d662656`): **Ran 652 tests, OK (skipped=10)**
- after (`28d0578`): **Ran 660 tests, OK (skipped=10)**

(+8 = `tests/test_S6c.py`'s 8 tests. The implementer reported 9 skipped; I saw 10 at both
commits in my environment - a skip-count difference, not a failure.)

## Check 3: my re-run of the pre-registered evaluation - PASS

From the scratch copy: `python tools/xp_v2_replay.py --s6c --hist C:/GIT/FPL/historical/2025-26
--prior C:/GIT/FPL/historical/2024-25 --rules C:/GIT/FPL/historical --out <scratch>
--data C:/GIT/FPL-data`. My `s6c_2025-26.txt` is **identical** to `tools/out/s6c/s6c_2025-26.txt`
except the `normalised ... ->` output-path line; `rescored_2025-26.csv` SHA-256 `55fa029e...`
in both. Numbers (difference 0 < 1e-6):

- primary: mean per-gameweek (xp_v2 - own_rebuilt) **+0.515** points per squad, 90% CI
  **[+0.213, +0.816]**, n=34, p=0.0068; season **+17.5** per squad (own_rebuilt 1362.0,
  xp_v2 1379.5, own_proxy 1367.4)
- decision: upper bound +0.816: **GW8 SWITCH STANDS**
- secondary: Spearman among starters +0.0154 [-0.0120, +0.0421]; MAE -0.1409 [-0.2558,
  -0.0359]; same XI 0.64, same captain 0.42; own_rebuilt - own_proxy -0.158 [-0.455, +0.141]
- 2026/27: GW5 own 54 points, captain 411 (14 of 15 with a row); GW6 own 59, captain 229;
  GW7 not locked down (data_checked 0, 0 of 10 fixtures finished); xp_v2 as tested "not
  available", never substituted.

`--test` from the same copy reproduces S6b: +0.358 [+0.126, +0.592], season +12.2, PASS -
xp_v2 and own_proxy go through S6b's unchanged path (also asserted by
`test_s6c_run_reproduces_s6b_and_the_decision_line`).

The GW5/GW6 lines were recomputed with my own glue from the data worktree (last own
snapshot before the event's deadline, `picks` of entry 3073318, `player_gw`, `xi_and_bench`,
`rule_autosubs`, captain doubled): 54 / captain 411 and 59 / captain 229, 0 autosubs - equal.

## Check 4: metric, filter, bootstrap, threshold as pre-registered - PASS

- Primary metric: per gameweek the mean over the 50 squads of (xp_v2 - own_rebuilt) realised
  points, season sum GW5-38 - `test_s6c` computes exactly that (`rec["diff"]`, `season`).
- Sample filter: S6b's (`FIRST, LAST = 5, 38`, `CH.N_SQUADS = 50`, `CH.SQUAD_SEED = 7`,
  `sample_squads(gw1_candidates(hist), ...)`, fixed squads, `planner.Replay.realised` on the
  re-scored actuals, `STARTER_P = 0.8` for the secondary).
- Bootstrap: `backtest.bootstrap_mean`, `B = 10000`, `SEED = 20261018`, `CI = 0.90`, unit =
  gameweek - as the prereg.
- Decision threshold: `decision_line` suspends only if `boot["hi"] < 0`; prints the two
  pinned strings.
- Nothing promoted or re-tuned after the results: the prereg's single commit precedes the
  code; the output prints the primary, the secondary (labelled information only) and the
  ruling's decision in that order. No adoption bar is claimed.
- The verbatim ruling is in the prereg (not a FAIL of 4).

## Check 5: recording path - PASS

No runner file changed in `e534200..28d0578` (`fpl_edge.py` byte-identical). Demonstrated
anyway: from a scratch folder holding a copy of the working export `fpl_export_gw7.json`,
`fpl_edge.py --record --source <src>` for all five nightly sources with the `d662656` code
and with the `28d0578` code, into scratch logs. Both wrote 1055 rows for GW8 (own 275, xg 260,
minutes 260, bottomup 260; fpl_ep skipped, no ep_next in the export), identical in every
column but `made_at` (the clock). The real `projection_log.csv` on `data` was not touched.

## Check 6: mutation spot-check - PASS

Scratch copies of `28d0578`, one line changed each, `python -m unittest tests.test_S6c`:

| mutation | result |
|---|---|
| FDR side swapped (`fdr_a` for home) | FAILED (failures=3) |
| form window `lo <=` (five rounds) | FAILED (failures=2) |
| `gws_played` t instead of t-1 | FAILED (failures=3) |
| decision on `boot["lo"]` | FAILED (errors=1) |
| `recorded_own` reads the raw log, not `forecasts()` | FAILED (failures=1) |
| lockdown guard without the fixtures-finished clause | FAILED (failures=1) |
| double gameweek: first fixture only | FAILED (failures=1) |
| personal prior never found | FAILED (failures=2) |
| M3: 450-minute filter dropped at the history rows | OK (equivalent: `personal_priors` re-applies `minutes < 450`) |
| M12: 45-minute gate dropped in own_rebuilt | OK (equivalent: `project` returns 0.0 under 45 minutes and `proj > 0` drops it) |

The implementer's two "equivalent" claims hold by reading `fpl_edge.personal_priors` and
`fpl_edge.project`.

## Check 7: secrets - PASS

The three files at `28d0578` grepped for `apiKey=`, `Authorization`, `api_key`/`api-key`,
`Bearer `, `ODDS_API_KEY` and any 32+ character alphanumeric run: no match. The outputs under
`tools/out/s6c/` are gitignored and contain no key-like string.

## Observations (no verdict effect)

1. `web_name` collisions: own_rebuilt inherits live own's rule that a shared `web_name`
   resolves to the first history row in id order (observed for Martinez and Onana among
   players with a 2024/25 row, and for surnames such as Henderson, Gomez, James, Wilson
   whose namesake has the row). Faithful to live; the prereg pins the web_name key.
2. `run.txt` written by my scratch re-run records `commit: unknown (git unavailable)` because
   the scratch copy is not a git checkout; the implementer's `run.txt` records `28d0578`
   with 0 modified tracked files.
3. Skip count 10 (not 9) at both commits in my environment.

## VERDICT: PASS

The prereg was committed before any S6c code and never edited; own_rebuilt is live own's
`project()` called as `record_status`'s own branch calls it, with the form window t-4..t-1,
`gws_played = t-1`, positional and web_name-keyed 2024/25 personal priors, the
minutes-reliability scaling and the end-of-season FDR by side, summed per fixture, rounded
and kept when > 0 - confirmed by an independent hand recomputation on real data with 0
mismatches at GW5, 21 and 38, and its lacks are stated in the output; the truncation test at
GW5/21/38 reproduces own_rebuilt and xp_v2 to the bit and every training row precedes its
origin's deadline; my re-run reproduces every printed number exactly (+0.515 [+0.213,
+0.816], season +17.5, GW8 SWITCH STANDS; own_rebuilt - own_proxy -0.158 [-0.455, +0.141];
GW5 54 / GW6 59 / GW7 not locked down, xp_v2 "not available"), and S6b's lines reproduce
through the unchanged path; the squads, metric, bootstrap (B=10000, seed 20261018, 90%) and
the suspension threshold (90% upper bound < 0) are the prereg's; the suite is 652 OK before
and 660 OK after; no runner file changed and the recording path writes identical rows with
both code versions; eight real mutations go red and the two claimed-equivalent ones are
equivalent; no secrets.
